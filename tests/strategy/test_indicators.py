import pandas as pd

from ath_breakout.strategy.indicators import add_moving_averages


def test_adds_full_window_moving_averages_without_look_ahead() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL"] * 200,
            "split_adj_close": list(range(1, 201)),
        }
    )

    result = add_moving_averages(data)

    assert result["sma_50"].isna().sum() == 49
    assert result["sma_100"].isna().sum() == 99
    assert result["sma_150"].isna().sum() == 149
    assert result["sma_200"].isna().sum() == 199
    assert result.loc[49, "sma_50"] == 25.5
    assert result.loc[99, "sma_100"] == 50.5
    assert result.loc[149, "sma_150"] == 75.5
    assert result.loc[199, "sma_200"] == 100.5


def test_calculates_averages_separately_for_each_security() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL"] * 50 + ["MSFT"] * 50,
            "split_adj_close": [100.0] * 50 + [200.0] * 50,
        }
    )

    result = add_moving_averages(data)

    assert result.loc[49, "sma_50"] == 100.0
    assert result.loc[99, "sma_50"] == 200.0


def test_does_not_change_original_data() -> None:
    data = pd.DataFrame(
        {"security_id": ["AAPL"], "split_adj_close": [100.0]}
    )

    add_moving_averages(data)

    assert "sma_50" not in data.columns
