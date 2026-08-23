"""Refresh the current universe and incrementally update all market data."""

from pathlib import Path

from ath_breakout.data.market_update import update_market_data
from ath_breakout.data.universe import load_universe_csv
from ath_breakout.data.universe_update import ensure_weekly_iwv_snapshot


UNIVERSE_DIRECTORY = Path("data/universe")
RAW_DIRECTORY = Path("data/raw/yfinance")
PROCESSED_DIRECTORY = Path("data/processed/features")
MANIFEST_FILE = Path("data/state/yfinance_manifest.csv")


def main() -> None:
    universe_file = ensure_weekly_iwv_snapshot(UNIVERSE_DIRECTORY)
    universe = load_universe_csv(universe_file)

    print(f"Updating {len(universe)} securities from {universe_file}")

    manifest = update_market_data(
        universe=universe,
        raw_directory=RAW_DIRECTORY,
        processed_directory=PROCESSED_DIRECTORY,
        manifest_file=MANIFEST_FILE,
    )

    successful = (manifest["status"] == "success").sum()
    failed = (manifest["status"] == "failed").sum()
    print(f"Finished: {successful} successful, {failed} failed")


if __name__ == "__main__":
    main()
