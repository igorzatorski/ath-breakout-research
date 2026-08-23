from datetime import date

import pandas as pd
import pytest

from ath_breakout.data.market_update import (
    download_start_for_security,
    merge_security_history,
    update_market_data,
)
from ath_breakout.data.storage import load_security_data, save_security_data


def make_prices(dates: list[str], closes: list[float]) -> pd.DataFrame:
    """Create valid daily AAPL prices for update tests."""
    return pd.DataFrame(
        {
            "security_id": ["AAPL"] * len(dates),
            "ticker": ["AAPL"] * len(dates),
            "date": pd.to_datetime(dates),
            "open": closes,
            "high": [price + 1 for price in closes],
            "low": [price - 1 for price in closes],
            "close": closes,
            "volume": [1000] * len(dates),
        }
    )


def test_new_security_requests_full_history(tmp_path) -> None:
    result = download_start_for_security(tmp_path / "AAPL.parquet")

    assert result == "1900-01-01"


def test_existing_security_requests_short_overlap(tmp_path) -> None:
    file_path = tmp_path / "AAPL.parquet"
    save_security_data(
        make_prices(["2026-08-20", "2026-08-21"], [100.0, 101.0]),
        file_path,
    )

    result = download_start_for_security(file_path, overlap_days=7)

    assert result == "2026-08-14"


def test_merge_replaces_overlap_without_duplicate_session() -> None:
    existing = make_prices(["2026-08-20", "2026-08-21"], [100.0, 101.0])
    downloaded = make_prices(["2026-08-21", "2026-08-22"], [102.0, 103.0])

    result = merge_security_history(existing, downloaded)

    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-08-20",
        "2026-08-21",
        "2026-08-22",
    ]
    assert result["close"].tolist() == [100.0, 102.0, 103.0]


def test_updates_raw_processed_and_manifest(tmp_path, monkeypatch) -> None:
    universe = pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
        }
    )

    def fake_download(**kwargs):
        return (
            make_prices(["2026-08-20", "2026-08-21"], [100.0, 102.0]),
            [],
        )

    monkeypatch.setattr(
        "ath_breakout.data.market_update.download_yfinance_ohlcv",
        fake_download,
    )

    manifest = update_market_data(
        universe=universe,
        raw_directory=tmp_path / "raw",
        processed_directory=tmp_path / "processed",
        manifest_file=tmp_path / "state" / "manifest.csv",
        today=date(2026, 8, 22),
        batch_size=1,
    )

    raw_data = load_security_data(tmp_path / "raw" / "AAPL.parquet")
    processed_data = load_security_data(
        tmp_path / "processed" / "AAPL.parquet"
    )

    assert len(raw_data) == 2
    assert "prior_ath" not in raw_data.columns
    assert ["prior_ath", "breakout"] == [
        column
        for column in ["prior_ath", "breakout"]
        if column in processed_data.columns
    ]
    assert manifest["status"].tolist() == ["success"]
    assert (tmp_path / "state" / "manifest.csv").exists()
    assert not (tmp_path / "state" / "manifest.tmp.csv").exists()


def test_rejects_empty_universe(tmp_path) -> None:
    empty_universe = pd.DataFrame(columns=["security_id", "ticker"])

    with pytest.raises(
        ValueError,
        match="Universe must contain at least one security",
    ):
        update_market_data(
            universe=empty_universe,
            raw_directory=tmp_path / "raw",
            processed_directory=tmp_path / "processed",
            manifest_file=tmp_path / "manifest.csv",
        )


def test_rejects_non_positive_update_batch_size(tmp_path) -> None:
    universe = pd.DataFrame(
        {"security_id": ["AAPL"], "ticker": ["AAPL"]}
    )

    with pytest.raises(ValueError, match="batch_size must be greater than zero"):
        update_market_data(
            universe=universe,
            raw_directory=tmp_path / "raw",
            processed_directory=tmp_path / "processed",
            manifest_file=tmp_path / "manifest.csv",
            batch_size=0,
        )
