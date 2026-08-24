import pandas as pd

from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.processing import process_market_data


def test_processes_raw_data_into_all_current_features() -> None:
    raw_data = pd.DataFrame(
        {
            "security_id": ["AAPL"] * 150,
            "ticker": ["AAPL"] * 150,
            "date": pd.bdate_range("2024-01-01", periods=150),
            "open": list(range(100, 250)),
            "high": list(range(101, 251)),
            "low": list(range(99, 249)),
            "close": list(range(100, 250)),
            "volume": [1000] * 150,
        }
    )
    prepared_data = prepare_ohlcv_data(raw_data)

    result = process_market_data(prepared_data)

    expected_columns = {
        "split_adj_open",
        "split_adj_high",
        "split_adj_low",
        "split_adj_close",
        "sma_50",
        "sma_100",
        "sma_150",
        "prior_ath",
        "breakout",
    }
    assert expected_columns.issubset(result.columns)
