"""Keep the local IWV proxy universe reasonably current."""

from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd

from ath_breakout.data.adapters.ishares import download_iwv_universe
from ath_breakout.data.universe import find_latest_iwv_snapshot, load_universe_csv


def ensure_weekly_iwv_snapshot(
    directory: str | Path,
    today: date | None = None,
    maximum_age_days: int = 7,
    download_function: Callable[[], pd.DataFrame] | None = None,
) -> Path:
    """Reuse a recent IWV snapshot or download and save a new one."""
    directory_path = Path(directory)
    current_date = today or date.today()

    try:
        latest_path = find_latest_iwv_snapshot(directory_path)
        latest_universe = load_universe_csv(latest_path)
        if "downloaded_at" in latest_universe.columns:
            downloaded_date = pd.to_datetime(
                latest_universe["downloaded_at"].iloc[0],
                utc=True,
            ).date()
        else:
            downloaded_date = date.fromtimestamp(latest_path.stat().st_mtime)

        snapshot_age = (current_date - downloaded_date).days

        if snapshot_age < maximum_age_days:
            return latest_path
    except FileNotFoundError:
        pass

    downloader = download_function or download_iwv_universe
    new_universe = downloader()
    snapshot_date = pd.to_datetime(new_universe["as_of_date"].iloc[0])
    output_path = directory_path / (
        f"iwv_holdings_{snapshot_date.strftime('%Y-%m-%d')}.csv"
    )

    directory_path.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".tmp.csv")
    new_universe.to_csv(temporary_path, index=False)
    temporary_path.replace(output_path)
    return output_path
