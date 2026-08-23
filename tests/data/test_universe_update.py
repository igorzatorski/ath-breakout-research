from datetime import date

import pandas as pd

from ath_breakout.data.universe_update import ensure_weekly_iwv_snapshot


def make_universe(as_of_date: str) -> pd.DataFrame:
    """Create a minimal valid IWV-like universe."""
    return pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
            "name": ["APPLE INC"],
            "sector": ["Information Technology"],
            "as_of_date": [as_of_date],
            "downloaded_at": [as_of_date],
            "source": ["IWV holdings"],
        }
    )


def test_reuses_snapshot_younger_than_one_week(tmp_path) -> None:
    existing_path = tmp_path / "iwv_holdings_2026-08-20.csv"
    make_universe("2026-08-20").to_csv(existing_path, index=False)

    def download_must_not_run() -> pd.DataFrame:
        raise AssertionError("Recent snapshot should have been reused")

    result = ensure_weekly_iwv_snapshot(
        directory=tmp_path,
        today=date(2026, 8, 23),
        download_function=download_must_not_run,
    )

    assert result == existing_path


def test_downloads_snapshot_when_existing_one_is_one_week_old(tmp_path) -> None:
    old_path = tmp_path / "iwv_holdings_2026-08-16.csv"
    make_universe("2026-08-16").to_csv(old_path, index=False)

    def download_new_universe() -> pd.DataFrame:
        return make_universe("2026-08-23")

    result = ensure_weekly_iwv_snapshot(
        directory=tmp_path,
        today=date(2026, 8, 23),
        download_function=download_new_universe,
    )

    assert result == tmp_path / "iwv_holdings_2026-08-23.csv"
    assert result.exists()
    assert not (tmp_path / "iwv_holdings_2026-08-23.tmp.csv").exists()
