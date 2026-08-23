import pandas as pd

from ath_breakout.strategy.ath import add_breakout_signal, add_prior_ath


def test_adds_prior_ath_without_look_ahead() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL", "AAPL", "AAPL", "AAPL"],
            "high": [100, 105, 103, 110],
        }
    )

    result = add_prior_ath(data)

    assert pd.isna(result.loc[0, "prior_ath"])
    assert result["prior_ath"].iloc[1:].tolist() == [100, 105, 105]


def test_does_not_change_original_data() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL", "AAPL", "AAPL", "AAPL"],
            "high": [100, 105, 103, 110],
        }
    )

    add_prior_ath(data)

    assert "prior_ath" not in data.columns


def test_calculates_prior_ath_separately_for_each_security() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL", "MSFT", "AAPL", "MSFT", "AAPL", "MSFT"],
            "high": [100, 200, 105, 190, 103, 210],
        }
    )

    result = add_prior_ath(data)

    expected_prior_ath = [None, None, 100, 200, 105, 200]

    assert pd.isna(result.loc[0, "prior_ath"])
    assert pd.isna(result.loc[1, "prior_ath"])
    assert result["prior_ath"].iloc[2:].tolist() == expected_prior_ath[2:]


def test_adds_breakout_signal() -> None:
    data = pd.DataFrame(
        {
            "close": [99, 101, 105, 106],
            "prior_ath": [None, 100, 105, 105],
        }
    )

    result = add_breakout_signal(data)

    assert result["breakout"].tolist() == [False, True, False, True]


def test_breakout_signal_does_not_change_original_data() -> None:
    data = pd.DataFrame(
        {
            "close": [99, 101],
            "prior_ath": [None, 100],
        }
    )

    add_breakout_signal(data)

    assert "breakout" not in data.columns
