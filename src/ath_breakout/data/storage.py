"""Store one security's market data in each Parquet file."""

from pathlib import Path

import pandas as pd


def security_file_path(directory: str | Path, security_id: str) -> Path:
    """Return the Parquet path used for one security."""
    return Path(directory) / f"{security_id}.parquet"


def load_security_data(file_path: str | Path) -> pd.DataFrame:
    """Load one security's Parquet history."""
    return pd.read_parquet(file_path)


def save_security_data(data: pd.DataFrame, file_path: str | Path) -> None:
    """Safely replace one security's Parquet history."""
    output_path = Path(file_path)
    temporary_path = output_path.with_suffix(".tmp.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data.to_parquet(temporary_path, index=False)
    temporary_path.replace(output_path)
