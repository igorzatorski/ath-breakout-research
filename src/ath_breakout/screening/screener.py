"""Scan the current universe at one completed market session."""

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from ath_breakout.data.market_calendar import latest_expected_session
from ath_breakout.data.storage import load_security_data, security_file_path
from ath_breakout.screening.features import build_security_snapshot


STATE_ORDER = {
    "fresh_breakout": 0,
    "base_ready": 1,
    "approaching_ath": 2,
    "ath_continuation": 3,
    "trend_candidate": 4,
    "not_eligible": 5,
}

SCREEN_COLUMNS = [
    "security_id",
    "ticker",
    "date",
    "split_adj_open",
    "split_adj_high",
    "split_adj_low",
    "split_adj_close",
    "close",
    "volume",
    "sma_50",
    "sma_100",
    "sma_150",
    "sma_200",
    "prior_ath",
    "breakout",
]


def print_screen_progress(completed: int, total: int) -> None:
    """Print one timestamped progress bar for the stock screener."""
    bar_width = 30

    if total == 0:
        percentage = 100.0
        completed_width = bar_width
    else:
        percentage = 100 * completed / total
        completed_width = int(bar_width * completed / total)

    progress_bar = "#" * completed_width
    progress_bar += "-" * (bar_width - completed_width)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count_width = len(str(max(total, 1)))
    print(
        f"[{timestamp}] [{progress_bar}] {percentage:6.2f}% "
        f"scanned {completed:>{count_width}}/{total}",
        flush=True,
    )


def run_stock_screen(
    registry_file: str | Path,
    quality_report_file: str | Path,
    processed_directory: str | Path,
    today: date | None = None,
    as_of_date: date | None = None,
    show_progress: bool = False,
) -> tuple[pd.DataFrame, date, dict]:
    """Return current-universe snapshots at one selected session close."""
    registry = pd.read_csv(registry_file)
    quality = pd.read_csv(quality_report_file)

    if as_of_date is not None:
        scan_date = as_of_date
    elif "expected_latest_date" in quality.columns:
        expected_dates = pd.to_datetime(
            quality["expected_latest_date"],
            errors="coerce",
        ).dropna()
        scan_date = expected_dates.max().date()
    else:
        current_date = today or date.today()
        scan_date = latest_expected_session(current_date).date()

    current_universe = registry[registry["in_current_universe"] == True].copy()
    if as_of_date is None:
        current_universe = current_universe.merge(
            quality[["security_id", "quality_status", "last_date"]],
            on="security_id",
            how="left",
        )
        current_universe["last_date"] = pd.to_datetime(
            current_universe["last_date"],
            errors="coerce",
        )
        usable_universe = current_universe[
            (current_universe["quality_status"] == "good")
            & (current_universe["last_date"].dt.date == scan_date)
        ]
    else:
        # Historical mode deliberately tests every current constituent. A
        # current update failure does not imply that its older data is absent.
        usable_universe = current_universe

    benchmark_file = security_file_path(processed_directory, "IWV")
    if benchmark_file.exists():
        benchmark_data = load_security_data(
            benchmark_file,
            columns=["date", "split_adj_close"],
        )
        benchmark_data["date"] = pd.to_datetime(benchmark_data["date"])
        benchmark_data = benchmark_data[
            benchmark_data["date"].dt.date <= scan_date
        ].sort_values("date").reset_index(drop=True)
    else:
        benchmark_data = None

    snapshot_rows = []

    total_securities = len(usable_universe)

    if show_progress:
        print_screen_progress(0, total_securities)

    for security_number, (_, security) in enumerate(
        usable_universe.iterrows(),
        start=1,
    ):
        processed_file = security_file_path(
            processed_directory,
            security["security_id"],
        )

        if not processed_file.exists():
            continue

        data = load_security_data(processed_file, columns=SCREEN_COLUMNS)
        snapshot = build_security_snapshot(
            data,
            scan_date,
            benchmark_data=benchmark_data,
        )

        if snapshot is not None:
            snapshot_rows.append(snapshot)

        if show_progress and (
            security_number % 100 == 0
            or security_number == total_securities
        ):
            print_screen_progress(security_number, total_securities)

    result = pd.DataFrame(snapshot_rows)

    if len(result) > 0:
        result["_state_order"] = result["setup_state"].map(STATE_ORDER)
        result = result.sort_values(
            ["_state_order", "setup_score", "ath_distance_pct"],
            ascending=[True, False, False],
            na_position="last",
        )
        result = result.drop(columns="_state_order").reset_index(drop=True)

    summary = {
        "current_universe": len(current_universe),
        "usable_quality": len(usable_universe),
        "scanned": len(result),
        "excluded_quality_or_stale": (
            len(current_universe) - len(usable_universe)
            if as_of_date is None
            else len(current_universe) - len(result)
        ),
        "historical_mode": as_of_date is not None,
    }
    return result, scan_date, summary


def save_screen_results(results: pd.DataFrame, output_file: str | Path) -> None:
    """Safely save the complete screener table as CSV."""
    output_path = Path(output_file)
    temporary_path = output_path.with_suffix(".tmp.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(temporary_path, index=False)
    temporary_path.replace(output_path)
