"""Validate market data used by the system."""

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def validate_required_columns(data: pd.DataFrame) -> None:
    """Raise an error when an OHLCV column is missing."""
    missing_columns = []

    for required_column in REQUIRED_OHLCV_COLUMNS:
        if required_column not in data.columns:
            missing_columns.append(required_column)

    if len(missing_columns) > 0:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing}")


def validate_unique_dates(data: pd.DataFrame) -> None:
    """Raise an error when the same trading date appears more than once."""
    number_of_rows = len(data)
    number_of_unique_dates = data["date"].nunique()

    if number_of_rows != number_of_unique_dates:
        raise ValueError("Duplicate trading dates found")
