"""Measure freshness and completeness of stored US equity data."""

from datetime import date
from pathlib import Path

import pandas as pd
import pandas_market_calendars as market_calendars

from ath_breakout.data.storage import load_security_data, security_file_path


NYSE_CALENDAR = market_calendars.get_calendar("NYSE")
CALENDAR_START = "1900-01-01"


def valid_nyse_sessions(start_date: str | date, end_date: str | date) -> pd.DatetimeIndex:
    """Return timezone-free dates on which the NYSE was open."""
    sessions = NYSE_CALENDAR.valid_days(
        start_date=start_date,
        end_date=end_date,
    )
    return sessions.tz_localize(None).normalize()


def latest_expected_session(today: date) -> pd.Timestamp:
    """Return the latest completed session expected by the daily updater."""
    end_date = pd.Timestamp(today) - pd.Timedelta(days=1)
    start_date = end_date - pd.Timedelta(days=14)
    sessions = valid_nyse_sessions(start_date, end_date)

    if len(sessions) == 0:
        raise ValueError("No completed NYSE session found")

    return sessions[-1]


def count_missing_sessions(
    dates: pd.Series,
    expected_sessions: pd.DatetimeIndex,
) -> int:
    """Count absent NYSE sessions between a security's first and last row."""
    normalized_dates = pd.DatetimeIndex(pd.to_datetime(dates)).normalize()

    if len(normalized_dates) == 0:
        return 0

    first_date = normalized_dates.min()
    last_date = normalized_dates.max()
    expected_history = expected_sessions[
        (expected_sessions >= first_date) & (expected_sessions <= last_date)
    ]
    missing_sessions = expected_history.difference(normalized_dates)
    return len(missing_sessions)


def build_data_quality_report(
    manifest: pd.DataFrame,
    processed_directory: str | Path,
    today: date,
) -> pd.DataFrame:
    """Build one quality row for every security attempted by the updater."""
    expected_latest = latest_expected_session(today)
    expected_sessions = valid_nyse_sessions(CALENDAR_START, expected_latest)
    report_rows = []

    for _, manifest_row in manifest.iterrows():
        security_id = manifest_row["security_id"]
        processed_file = security_file_path(processed_directory, security_id)
        report_row = {
            "security_id": security_id,
            "ticker": manifest_row["ticker"],
            "in_current_universe": bool(
                manifest_row.get("in_current_universe", True)
            ),
            "update_status": manifest_row["status"],
            "quality_status": "no_data",
            "first_date": None,
            "last_date": None,
            "expected_latest_date": expected_latest.date(),
            "stale_sessions": None,
            "missing_sessions": None,
            "row_count": 0,
            "dividend_events": None,
            "split_events": None,
            "repaired_rows": None,
            "error": manifest_row.get("error"),
        }

        if not processed_file.exists():
            report_rows.append(report_row)
            continue

        try:
            data = load_security_data(processed_file)
        except (OSError, ValueError) as error:
            report_row["quality_status"] = "unreadable"
            report_row["error"] = f"{type(error).__name__}: {error}"
            report_rows.append(report_row)
            continue

        if len(data) == 0:
            report_rows.append(report_row)
            continue

        dates = pd.to_datetime(data["date"])
        first_date = dates.min().normalize()
        last_date = dates.max().normalize()
        missing_sessions = count_missing_sessions(dates, expected_sessions)
        stale_sessions = len(
            expected_sessions[
                (expected_sessions > last_date)
                & (expected_sessions <= expected_latest)
            ]
        )

        if manifest_row["status"] != "success":
            quality_status = "update_failed"
        elif last_date > expected_latest:
            quality_status = "future_date"
        elif stale_sessions > 0 and missing_sessions > 0:
            quality_status = "stale_and_gaps"
        elif stale_sessions > 0:
            quality_status = "stale"
        elif missing_sessions > 0:
            quality_status = "gaps"
        else:
            quality_status = "good"

        report_row.update(
            {
                "quality_status": quality_status,
                "first_date": first_date.date(),
                "last_date": last_date.date(),
                "stale_sessions": stale_sessions,
                "missing_sessions": missing_sessions,
                "row_count": len(data),
                "dividend_events": int((data["dividends"] > 0).sum()),
                "split_events": int((data["stock_splits"] > 0).sum()),
                "repaired_rows": int(data["repaired"].sum()),
            }
        )
        report_rows.append(report_row)

    return pd.DataFrame(report_rows)


def save_data_quality_report(report: pd.DataFrame, output_file: str | Path) -> None:
    """Safely replace the latest CSV quality report."""
    output_path = Path(output_file)
    temporary_path = output_path.with_suffix(".tmp.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(temporary_path, index=False)
    temporary_path.replace(output_path)
