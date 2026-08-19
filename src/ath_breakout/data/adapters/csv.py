"""Adapt daily market data from CSV files to pandas DataFrames."""

from pathlib import Path

import pandas as pd

from ath_breakout.data.validation import validate_required_columns
from ath_breakout.data.validation import validate_unique_dates


def load_ohlcv_csv(file_path: str | Path) -> pd.DataFrame:
    """Load an OHLCV CSV file into a pandas DataFrame."""
    data = pd.read_csv(file_path)
    validate_required_columns(data)
    data["date"] = pd.to_datetime(data["date"])
    validate_unique_dates(data)
    data = data.sort_values("date")
    return data
