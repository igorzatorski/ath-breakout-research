"""Validate market data used by the system."""

import pandas as pd


REQUIRED_OHLCV_COLUMNS = (
    "security_id",
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
)
NUMERIC_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")
PRICE_COLUMNS = ("open", "high", "low", "close")


def validate_required_columns(data: pd.DataFrame) -> None:
    """Raise an error when an OHLCV column is missing."""
    missing_columns = []

    for required_column in REQUIRED_OHLCV_COLUMNS:
        if required_column not in data.columns:
            missing_columns.append(required_column)

    if len(missing_columns) > 0:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing}")


def validate_unique_security_dates(data: pd.DataFrame) -> None:
    """Raise an error when a security has two rows for one date."""
    duplicate_security_dates = data.duplicated(
        subset=["security_id", "date"]
    )
    number_of_duplicates = duplicate_security_dates.sum()

    if number_of_duplicates > 0:
        raise ValueError("Duplicate security_id and date combinations found")


def validate_missing_values(data: pd.DataFrame) -> None:
    """Raise an error when a required OHLCV value is missing."""
    for required_column in REQUIRED_OHLCV_COLUMNS:
        number_of_missing_values = data[required_column].isna().sum()

        if number_of_missing_values > 0:
            raise ValueError(
                f"Missing values found in column: {required_column}"
            )


def validate_numeric_columns(data: pd.DataFrame) -> None:
    """Raise an error when an OHLCV value is not numeric."""
    for numeric_column in NUMERIC_OHLCV_COLUMNS:
        column_is_numeric = pd.api.types.is_numeric_dtype(
            data[numeric_column]
        )

        if column_is_numeric == False:
            raise ValueError(
                f"Non-numeric values found in column: {numeric_column}"
            )


def validate_positive_prices(data: pd.DataFrame) -> None:
    """Raise an error when an OHLC price is zero or negative."""
    for price_column in PRICE_COLUMNS:
        non_positive_prices = data[price_column] <= 0
        number_of_non_positive_prices = non_positive_prices.sum()

        if number_of_non_positive_prices > 0:
            raise ValueError(
                f"Non-positive prices found in column: {price_column}"
            )


def validate_non_negative_volume(data: pd.DataFrame) -> None:
    """Raise an error when volume is negative."""
    negative_volume_values = data["volume"] < 0
    number_of_negative_values = negative_volume_values.sum()

    if number_of_negative_values > 0:
        raise ValueError("Negative volume found")


def validate_high_prices(data: pd.DataFrame) -> None:
    """Raise an error when high is lower than another OHLC price."""
    high_below_open = data["high"] < data["open"]
    number_of_high_below_open = high_below_open.sum()

    if number_of_high_below_open > 0:
        raise ValueError("High price is lower than open price")

    high_below_close = data["high"] < data["close"]
    number_of_high_below_close = high_below_close.sum()

    if number_of_high_below_close > 0:
        raise ValueError("High price is lower than close price")

    high_below_low = data["high"] < data["low"]
    number_of_high_below_low = high_below_low.sum()

    if number_of_high_below_low > 0:
        raise ValueError("High price is lower than low price")


def validate_low_prices(data: pd.DataFrame) -> None:
    """Raise an error when low is higher than another OHLC price."""
    low_above_open = data["low"] > data["open"]
    number_of_low_above_open = low_above_open.sum()

    if number_of_low_above_open > 0:
        raise ValueError("Low price is higher than open price")

    low_above_close = data["low"] > data["close"]
    number_of_low_above_close = low_above_close.sum()

    if number_of_low_above_close > 0:
        raise ValueError("Low price is higher than close price")

    low_above_high = data["low"] > data["high"]
    number_of_low_above_high = low_above_high.sum()

    if number_of_low_above_high > 0:
        raise ValueError("Low price is higher than high price")
