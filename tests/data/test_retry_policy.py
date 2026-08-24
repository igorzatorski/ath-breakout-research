from datetime import date

import pandas as pd

from ath_breakout.data.retry_policy import (
    classify_download_error,
    failed_retry_state,
    retry_is_due,
    successful_retry_state,
)


def test_first_failure_is_retried_next_day() -> None:
    state = failed_retry_state(
        previous_row=None,
        current_date=date(2026, 8, 24),
        error_type="no_data",
    )

    assert state["failure_count"] == 1
    assert state["download_state"] == "retry_pending"
    assert state["next_retry_date"] == date(2026, 8, 25)


def test_third_failure_switches_to_weekly_retry() -> None:
    previous_row = pd.Series({"failure_count": 2})

    state = failed_retry_state(
        previous_row=previous_row,
        current_date=date(2026, 8, 24),
        error_type="no_data",
    )

    assert state["failure_count"] == 3
    assert state["download_state"] == "weekly_retry"
    assert state["next_retry_date"] == date(2026, 8, 31)


def test_retry_waits_until_scheduled_date() -> None:
    previous_row = pd.Series({"next_retry_date": "2026-08-31"})

    assert retry_is_due(previous_row, date(2026, 8, 30)) == False
    assert retry_is_due(previous_row, date(2026, 8, 31)) == True


def test_success_clears_failure_history() -> None:
    state = successful_retry_state()

    assert state == {
        "download_state": "active",
        "failure_count": 0,
        "last_failure_date": None,
        "next_retry_date": None,
        "error_type": None,
    }


def test_classifies_missing_new_and_existing_data_differently() -> None:
    error = ValueError("Yahoo returned no valid data")

    assert classify_download_error(error, raw_file_exists=False) == "no_data"
    assert (
        classify_download_error(error, raw_file_exists=True)
        == "update_unavailable"
    )
