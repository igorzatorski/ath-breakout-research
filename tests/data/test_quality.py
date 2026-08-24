from datetime import date

import pandas as pd

from ath_breakout.data.quality import (
    build_data_quality_report,
    count_missing_sessions,
    latest_expected_session,
    save_data_quality_report,
    valid_nyse_sessions,
)
from ath_breakout.data.storage import save_security_data


def test_latest_expected_session_excludes_today() -> None:
    result = latest_expected_session(date(2024, 12, 4))

    assert result == pd.Timestamp("2024-12-03")


def test_thanksgiving_is_not_reported_as_a_gap() -> None:
    dates = pd.Series(pd.to_datetime(["2024-11-27", "2024-11-29"]))
    sessions = valid_nyse_sessions("2024-11-27", "2024-11-29")

    result = count_missing_sessions(dates, sessions)

    assert result == 0


def test_detects_a_missing_trading_session() -> None:
    dates = pd.Series(pd.to_datetime(["2024-11-29", "2024-12-03"]))
    sessions = valid_nyse_sessions("2024-11-29", "2024-12-03")

    result = count_missing_sessions(dates, sessions)

    assert result == 1


def test_builds_good_quality_row_for_complete_fresh_data(tmp_path) -> None:
    processed_directory = tmp_path / "processed"
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-12-02", "2024-12-03"]),
            "dividends": [0.0, 0.25],
            "stock_splits": [0.0, 0.0],
            "repaired": [False, True],
        }
    )
    save_security_data(data, processed_directory / "AAPL.parquet")
    manifest = pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
            "in_current_universe": [True],
            "status": ["success"],
            "error": [None],
        }
    )

    report = build_data_quality_report(
        manifest,
        processed_directory,
        today=date(2024, 12, 4),
    )

    assert report.loc[0, "quality_status"] == "good"
    assert report.loc[0, "stale_sessions"] == 0
    assert report.loc[0, "missing_sessions"] == 0
    assert report.loc[0, "dividend_events"] == 1
    assert report.loc[0, "repaired_rows"] == 1


def test_reports_stale_data_and_failed_update(tmp_path) -> None:
    processed_directory = tmp_path / "processed"
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-11-29"]),
            "dividends": [0.0],
            "stock_splits": [0.0],
            "repaired": [False],
        }
    )
    save_security_data(data, processed_directory / "OLD.parquet")
    manifest = pd.DataFrame(
        {
            "security_id": ["OLD"],
            "ticker": ["OLD"],
            "in_current_universe": [True],
            "status": ["failed"],
            "error": ["Yahoo returned no valid data"],
        }
    )

    report = build_data_quality_report(
        manifest,
        processed_directory,
        today=date(2024, 12, 4),
    )

    assert report.loc[0, "quality_status"] == "update_failed"
    assert report.loc[0, "stale_sessions"] == 2


def test_reports_a_scheduled_retry_separately(tmp_path) -> None:
    processed_directory = tmp_path / "processed"
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-12-03"]),
            "dividends": [0.0],
            "stock_splits": [0.0],
            "repaired": [False],
        }
    )
    save_security_data(data, processed_directory / "WAIT.parquet")
    manifest = pd.DataFrame(
        {
            "security_id": ["WAIT"],
            "ticker": ["WAIT"],
            "status": ["retry_deferred"],
            "error": ["ValueError: Yahoo returned no valid data"],
        }
    )

    report = build_data_quality_report(
        manifest,
        processed_directory,
        today=date(2024, 12, 4),
    )

    assert report.loc[0, "quality_status"] == "retry_deferred"
    assert "failure_count" in report.columns
    assert "next_retry_date" in report.columns


def test_saves_quality_report_without_leaving_temporary_file(tmp_path) -> None:
    output_file = tmp_path / "quality.csv"
    report = pd.DataFrame({"security_id": ["AAPL"], "status": ["good"]})

    save_data_quality_report(report, output_file)

    saved_report = pd.read_csv(output_file)
    assert saved_report.to_dict("records") == [
        {"security_id": "AAPL", "status": "good"}
    ]
    assert not (tmp_path / "quality.tmp.csv").exists()
