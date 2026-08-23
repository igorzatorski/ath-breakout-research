"""Adapt daily market data from CSV files to pandas DataFrames."""

from pathlib import Path

import pandas as pd

from ath_breakout.data.preparation import prepare_ohlcv_data


def load_ohlcv_csv(file_path: str | Path) -> pd.DataFrame:
    """Load an OHLCV CSV file into a pandas DataFrame."""
    data = pd.read_csv(file_path)
    return prepare_ohlcv_data(data)
