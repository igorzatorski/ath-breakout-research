import pandas as pd
import pytest

from ath_breakout.data.validation import validate_required_columns
from ath_breakout.data.validation import validate_unique_security_dates
from ath_breakout.data.validation import validate_missing_values
from ath_breakout.data.validation import validate_numeric_columns
from ath_breakout.data.validation import validate_positive_prices
from ath_breakout.data.validation import validate_non_negative_volume
from ath_breakout.data.validation import validate_high_prices
from ath_breakout.data.validation import validate_low_prices
from ath_breakout.data.validation import validate_corporate_actions


def test_accepts_all_required_columns() -> None:
    data = pd.DataFrame(
        columns=[
            "security_id",
            "ticker",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    )

    validate_required_columns(data)


def test_rejects_missing_columns() -> None:
    data = pd.DataFrame(
        columns=["security_id", "ticker", "date", "open", "high", "low", "close"]
    )

    with pytest.raises(ValueError, match="Missing required columns: volume"):
        validate_required_columns(data)


def test_accepts_same_date_for_different_securities() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL", "MSFT"],
            "date": ["2024-01-02", "2024-01-02"],
        }
    )

    validate_unique_security_dates(data)


def test_rejects_duplicate_date_for_same_security() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL", "AAPL"],
            "date": ["2024-01-02", "2024-01-02"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Duplicate security_id and date combinations found",
    ):
        validate_unique_security_dates(data)


def test_accepts_complete_values() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
            "date": ["2024-01-02"],
            "open": [100],
            "high": [103],
            "low": [99],
            "close": [102],
            "volume": [1200000],
        }
    )

    validate_missing_values(data)


def test_rejects_missing_values() -> None:
    data = pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
            "date": ["2024-01-02"],
            "open": [100],
            "high": [103],
            "low": [99],
            "close": [None],
            "volume": [1200000],
        }
    )

    with pytest.raises(ValueError, match="Missing values found in column: close"):
        validate_missing_values(data)


def test_accepts_numeric_columns() -> None:
    data = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "open": [100],
            "high": [103],
            "low": [99],
            "close": [102],
            "volume": [1200000],
        }
    )

    validate_numeric_columns(data)


def test_rejects_non_numeric_columns() -> None:
    data = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "open": ["one hundred"],
            "high": [103],
            "low": [99],
            "close": [102],
            "volume": [1200000],
        }
    )

    with pytest.raises(ValueError, match="Non-numeric values found in column: open"):
        validate_numeric_columns(data)


def test_accepts_positive_prices() -> None:
    data = pd.DataFrame(
        {
            "open": [100],
            "high": [103],
            "low": [99],
            "close": [102],
        }
    )

    validate_positive_prices(data)


def test_rejects_non_positive_prices() -> None:
    data = pd.DataFrame(
        {
            "open": [0],
            "high": [103],
            "low": [99],
            "close": [102],
        }
    )

    with pytest.raises(ValueError, match="Non-positive prices found in column: open"):
        validate_positive_prices(data)


def test_accepts_zero_volume() -> None:
    data = pd.DataFrame({"volume": [0]})

    validate_non_negative_volume(data)


def test_rejects_negative_volume() -> None:
    data = pd.DataFrame({"volume": [-1]})

    with pytest.raises(ValueError, match="Negative volume found"):
        validate_non_negative_volume(data)


def test_accepts_valid_high_prices() -> None:
    data = pd.DataFrame(
        {"open": [100], "high": [105], "low": [98], "close": [103]}
    )

    validate_high_prices(data)


def test_rejects_high_below_open() -> None:
    data = pd.DataFrame(
        {"open": [106], "high": [105], "low": [98], "close": [103]}
    )

    with pytest.raises(ValueError, match="High price is lower than open price"):
        validate_high_prices(data)


def test_rejects_high_below_close() -> None:
    data = pd.DataFrame(
        {"open": [100], "high": [105], "low": [98], "close": [106]}
    )

    with pytest.raises(ValueError, match="High price is lower than close price"):
        validate_high_prices(data)


def test_rejects_high_below_low() -> None:
    data = pd.DataFrame(
        {"open": [100], "high": [105], "low": [106], "close": [103]}
    )

    with pytest.raises(ValueError, match="High price is lower than low price"):
        validate_high_prices(data)


def test_accepts_valid_low_prices() -> None:
    data = pd.DataFrame(
        {"open": [100], "high": [105], "low": [98], "close": [103]}
    )

    validate_low_prices(data)


def test_rejects_low_above_open() -> None:
    data = pd.DataFrame(
        {"open": [100], "high": [105], "low": [101], "close": [103]}
    )

    with pytest.raises(ValueError, match="Low price is higher than open price"):
        validate_low_prices(data)


def test_rejects_low_above_close() -> None:
    data = pd.DataFrame(
        {"open": [105], "high": [106], "low": [104], "close": [103]}
    )

    with pytest.raises(ValueError, match="Low price is higher than close price"):
        validate_low_prices(data)


def test_rejects_low_above_high() -> None:
    data = pd.DataFrame(
        {"open": [107], "high": [105], "low": [106], "close": [107]}
    )

    with pytest.raises(ValueError, match="Low price is higher than high price"):
        validate_low_prices(data)


def test_accepts_valid_corporate_actions() -> None:
    data = pd.DataFrame(
        {
            "adj_close": [100.0],
            "dividends": [0.0],
            "stock_splits": [2.0],
        }
    )

    validate_corporate_actions(data)


def test_rejects_negative_dividend() -> None:
    data = pd.DataFrame(
        {
            "adj_close": [100.0],
            "dividends": [-1.0],
            "stock_splits": [0.0],
        }
    )

    with pytest.raises(ValueError, match="Negative dividend found"):
        validate_corporate_actions(data)


def test_rejects_negative_split_ratio() -> None:
    data = pd.DataFrame(
        {
            "adj_close": [100.0],
            "dividends": [0.0],
            "stock_splits": [-2.0],
        }
    )

    with pytest.raises(ValueError, match="Negative stock split ratio found"):
        validate_corporate_actions(data)
