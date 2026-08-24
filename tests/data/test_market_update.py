from datetime import date

import pandas as pd
import pytest

from ath_breakout.data.market_update import (
    download_start_for_security,
    merge_security_history,
    requires_full_schema_refresh,
    print_update_progress,
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
    existing_data = make_prices(
        ["2026-08-20", "2026-08-21"],
        [100.0, 101.0],
    )
    existing_data["adj_close"] = existing_data["close"]
    existing_data["dividends"] = 0.0
    existing_data["stock_splits"] = 0.0
    existing_data["repaired"] = False
    save_security_data(existing_data, file_path)

    result = download_start_for_security(file_path, overlap_days=7)

    assert result == "2026-08-14"


def test_old_schema_requests_full_history_for_migration(tmp_path) -> None:
    file_path = tmp_path / "AAPL.parquet"
    save_security_data(
        make_prices(["2026-08-20"], [100.0]),
        file_path,
    )

    result = download_start_for_security(file_path)

    assert result == "1900-01-01"
    assert requires_full_schema_refresh(file_path) == True


def test_new_schema_does_not_require_full_refresh(tmp_path) -> None:
    file_path = tmp_path / "AAPL.parquet"
    data = make_prices(["2026-08-20"], [100.0])
    data["adj_close"] = data["close"]
    data["dividends"] = 0.0
    data["stock_splits"] = 0.0
    data["repaired"] = False
    save_security_data(data, file_path)

    assert requires_full_schema_refresh(file_path) == False


def test_full_refresh_replaces_old_schema_instead_of_merging(
    tmp_path,
    monkeypatch,
) -> None:
    universe = pd.DataFrame(
        {"security_id": ["AAPL"], "ticker": ["AAPL"]}
    )
    raw_file = tmp_path / "raw" / "AAPL.parquet"
    save_security_data(
        make_prices(["2020-01-02"], [50.0]),
        raw_file,
    )

    refreshed_data = make_prices(["2020-01-03"], [101.0])
    refreshed_data["adj_close"] = 100.0
    refreshed_data["dividends"] = 1.0
    refreshed_data["stock_splits"] = 0.0
    refreshed_data["repaired"] = False

    def fake_download(**kwargs):
        return refreshed_data, []

    monkeypatch.setattr(
        "ath_breakout.data.market_update.download_yfinance_ohlcv",
        fake_download,
    )

    update_market_data(
        universe=universe,
        raw_directory=tmp_path / "raw",
        processed_directory=tmp_path / "processed",
        manifest_file=tmp_path / "manifest.csv",
        today=date(2026, 8, 24),
        batch_size=1,
    )

    result = load_security_data(raw_file)

    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == ["2020-01-03"]
    assert result["adj_close"].tolist() == [100.0]
    assert result["dividends"].tolist() == [1.0]


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
            "in_current_universe": [True],
        }
    )
    download_arguments = {}

    def fake_download(**kwargs):
        download_arguments.update(kwargs)
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
    assert "split_adj_close" not in raw_data.columns
    assert "split_adj_close" in processed_data.columns
    assert "sma_50" in processed_data.columns
    assert "sma_100" in processed_data.columns
    assert "sma_150" in processed_data.columns
    assert ["prior_ath", "breakout"] == [
        column
        for column in ["prior_ath", "breakout"]
        if column in processed_data.columns
    ]
    assert manifest["status"].tolist() == ["success"]
    assert manifest["in_current_universe"].tolist() == [True]
    assert manifest["dividend_events"].tolist() == [0]
    assert manifest["split_events"].tolist() == [0]
    assert manifest["repaired_rows"].tolist() == [0]
    assert download_arguments["end_date"] == "2026-08-22"
    assert (tmp_path / "state" / "manifest.csv").exists()
    assert not (tmp_path / "state" / "manifest.tmp.csv").exists()


def test_updates_security_outside_current_universe(tmp_path, monkeypatch) -> None:
    registry = pd.DataFrame(
        {
            "security_id": ["MSFT"],
            "ticker": ["MSFT"],
            "in_current_universe": [False],
        }
    )

    def fake_download(**kwargs):
        data = make_prices(["2026-08-21"], [200.0])
        data["security_id"] = "MSFT"
        data["ticker"] = "MSFT"
        return data, []

    monkeypatch.setattr(
        "ath_breakout.data.market_update.download_yfinance_ohlcv",
        fake_download,
    )

    manifest = update_market_data(
        universe=registry,
        raw_directory=tmp_path / "raw",
        processed_directory=tmp_path / "processed",
        manifest_file=tmp_path / "manifest.csv",
        today=date(2026, 8, 24),
        batch_size=1,
    )

    assert (tmp_path / "raw" / "MSFT.parquet").exists()
    assert manifest["in_current_universe"].tolist() == [False]
    assert manifest["status"].tolist() == ["success"]


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


def test_prints_timestamped_progress(capsys) -> None:
    print_update_progress(
        completed_batches=2,
        total_batches=4,
        successful=90,
        failed=10,
    )

    output = capsys.readouterr().out

    assert "50.00%" in output
    assert "batch 2/4" in output
    assert "success: 90" in output
    assert "failed: 10" in output


def test_invalid_security_does_not_stop_other_securities(
    tmp_path,
    monkeypatch,
) -> None:
    universe = pd.DataFrame(
        {
            "security_id": ["AAPL", "BROKEN"],
            "ticker": ["AAPL", "BROKEN"],
        }
    )
    valid_data = make_prices(["2026-08-21"], [100.0])
    valid_data["adj_close"] = 100.0

    invalid_data = make_prices(["2026-08-21"], [50.0])
    invalid_data["security_id"] = "BROKEN"
    invalid_data["ticker"] = "BROKEN"
    invalid_data["adj_close"] = 50.0

    downloaded_data = pd.concat(
        [valid_data, invalid_data],
        ignore_index=True,
    )
    downloaded_data.loc[downloaded_data["ticker"] == "BROKEN", "adj_close"] = None

    def fake_download(**kwargs):
        return downloaded_data, []

    monkeypatch.setattr(
        "ath_breakout.data.market_update.download_yfinance_ohlcv",
        fake_download,
    )

    manifest = update_market_data(
        universe=universe,
        raw_directory=tmp_path / "raw",
        processed_directory=tmp_path / "processed",
        manifest_file=tmp_path / "manifest.csv",
        today=date(2026, 8, 24),
        batch_size=2,
    )

    statuses = dict(zip(manifest["ticker"], manifest["status"]))

    assert statuses == {"AAPL": "success", "BROKEN": "failed"}
    assert (tmp_path / "raw" / "AAPL.parquet").exists()
    assert not (tmp_path / "raw" / "BROKEN.parquet").exists()
    assert "Missing values found in column: adj_close" in manifest.loc[
        manifest["ticker"] == "BROKEN",
        "error",
    ].iloc[0]
