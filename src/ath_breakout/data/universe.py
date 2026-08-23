"""Load and validate security universes."""

from pathlib import Path

import pandas as pd


def find_latest_iwv_snapshot(directory: str | Path) -> Path:
    """Return the newest dated IWV holdings file in a directory."""
    directory_path = Path(directory)
    snapshot_files = list(directory_path.glob("iwv_holdings_*.csv"))

    if len(snapshot_files) == 0:
        raise FileNotFoundError("No IWV universe snapshot found")

    return max(snapshot_files)


def validate_universe(universe: pd.DataFrame) -> None:
    """Raise an error when a security universe is incomplete or ambiguous."""
    required_columns = ("security_id", "ticker")

    for required_column in required_columns:
        if required_column not in universe.columns:
            raise ValueError(f"Missing universe column: {required_column}")

        number_of_missing_values = universe[required_column].isna().sum()

        if number_of_missing_values > 0:
            raise ValueError(f"Missing universe values in column: {required_column}")

    duplicate_security_ids = universe["security_id"].duplicated().sum()

    if duplicate_security_ids > 0:
        raise ValueError("Duplicate security_id values found in universe")

    duplicate_tickers = universe["ticker"].duplicated().sum()

    if duplicate_tickers > 0:
        raise ValueError("Duplicate ticker values found in universe")


def load_universe_csv(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV containing unique security IDs and data-provider tickers."""
    universe = pd.read_csv(file_path)
    validate_universe(universe)

    return universe.reset_index(drop=True)
