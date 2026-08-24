import pandas as pd

import pytest

from ath_breakout.data.adapters.yfinance import download_yfinance_ohlcv
from ath_breakout.data.adapters.yfinance import normalize_yfinance_download


def test_normalizes_multiple_yahoo_tickers() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    columns = pd.MultiIndex.from_product(
        [
            ["AAPL", "MSFT"],
            ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
        ]
    )
    raw_data = pd.DataFrame(
        [
            [100, 103, 99, 102, 102, 1200000, 200, 204, 198, 203, 203, 900000],
            [102, 105, 101, 104, 104, 1350000, 203, 205, 200, 201, 201, 950000],
        ],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(
        raw_data,
        ["AAPL", "MSFT"],
    )

    assert failed_tickers == []
    assert result["security_id"].tolist() == ["AAPL", "AAPL", "MSFT", "MSFT"]
    assert result["ticker"].tolist() == ["AAPL", "AAPL", "MSFT", "MSFT"]
    assert result["close"].tolist() == [102, 104, 203, 201]
    assert result["adj_close"].tolist() == [102, 104, 203, 201]
    assert result["dividends"].tolist() == [0.0, 0.0, 0.0, 0.0]
    assert result["stock_splits"].tolist() == [0.0, 0.0, 0.0, 0.0]
    assert result["prices_split_adjusted"].tolist() == [True, True, True, True]


def test_preserves_yahoo_corporate_actions() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    columns = pd.MultiIndex.from_product(
        [["AAPL"], [
            "Open",
            "High",
            "Low",
            "Close",
            "Adj Close",
            "Volume",
            "Dividends",
            "Stock Splits",
            "Repaired?",
        ]]
    )
    raw_data = pd.DataFrame(
        [
            [100, 103, 99, 102, 101, 1200000, 0.25, 0.0, False],
            [51, 53, 50, 52, 52, 2400000, 0.0, 2.0, True],
        ],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(raw_data, ["AAPL"])

    assert failed_tickers == []
    assert result["adj_close"].tolist() == [101, 52]
    assert result["dividends"].tolist() == [0.25, 0.0]
    assert result["stock_splits"].tolist() == [0.0, 2.0]
    assert result["repaired"].tolist() == [False, True]


def test_reports_missing_yahoo_ticker() -> None:
    dates = pd.to_datetime(["2024-01-02"])
    columns = pd.MultiIndex.from_product(
        [["AAPL"], ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )
    raw_data = pd.DataFrame(
        [[100, 103, 99, 102, 102, 1200000]],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(
        raw_data,
        ["AAPL", "MSFT"],
    )

    assert result["ticker"].tolist() == ["AAPL"]
    assert failed_tickers == ["MSFT"]


def test_one_invalid_ticker_does_not_stop_the_batch() -> None:
    dates = pd.to_datetime(["2024-01-02"])
    columns = pd.MultiIndex.from_product(
        [
            ["AAPL", "BROKEN"],
            ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
        ]
    )
    raw_data = pd.DataFrame(
        [[100, 103, 99, 102, 102, 1200000, 50, 52, 49, 51, None, 500000]],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(
        raw_data,
        ["AAPL", "BROKEN"],
    )

    assert result["ticker"].tolist() == ["AAPL"]
    assert failed_tickers == ["BROKEN"]


def test_rejects_non_positive_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be greater than zero"):
        download_yfinance_ohlcv(
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-02-01",
            batch_size=0,
        )


def test_retries_failed_batch_ticker_individually(tmp_path, monkeypatch) -> None:
    dates = pd.to_datetime(["2024-01-02"])
    columns = pd.MultiIndex.from_product(
        [["AAPL"], ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )
    invalid_download = pd.DataFrame(
        [[100, 103, 99, 102, None, 1200000]],
        index=dates,
        columns=columns,
    )
    invalid_download.index.name = "Date"
    valid_download = invalid_download.copy()
    valid_download[("AAPL", "Adj Close")] = 102
    downloads = iter([invalid_download, valid_download])

    monkeypatch.setattr(
        "ath_breakout.data.adapters.yfinance.yf.download",
        lambda **kwargs: next(downloads),
    )

    result, failed_tickers = download_yfinance_ohlcv(
        tickers=["AAPL"],
        start_date="2024-01-01",
        end_date="2024-01-03",
        cache_directory=tmp_path / "cache",
    )

    assert failed_tickers == []
    assert result["ticker"].tolist() == ["AAPL"]
