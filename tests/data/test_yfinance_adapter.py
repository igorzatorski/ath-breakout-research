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


def test_rejects_non_positive_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be greater than zero"):
        download_yfinance_ohlcv(
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-02-01",
            batch_size=0,
        )
