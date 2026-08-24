"""Refresh the current universe and incrementally update all market data."""

from pathlib import Path

from ath_breakout.data.market_update import update_market_data
from ath_breakout.data.security_registry import update_security_registry
from ath_breakout.data.universe import load_universe_csv
from ath_breakout.data.universe_update import ensure_weekly_iwv_snapshot


UNIVERSE_DIRECTORY = Path("data/universe")
RAW_DIRECTORY = Path("data/raw/yfinance")
PROCESSED_DIRECTORY = Path("data/processed/features")
MANIFEST_FILE = Path("data/state/yfinance_manifest.csv")
REGISTRY_FILE = Path("data/state/security_registry.csv")


def main() -> None:
    universe_file = ensure_weekly_iwv_snapshot(UNIVERSE_DIRECTORY)
    universe = load_universe_csv(universe_file)
    registry = update_security_registry(universe, REGISTRY_FILE)

    current_count = registry["in_current_universe"].sum()
    previous_count = len(registry) - current_count
    print(
        f"Updating {len(registry)} known securities: "
        f"{current_count} current and {previous_count} former"
    )

    manifest = update_market_data(
        universe=registry,
        raw_directory=RAW_DIRECTORY,
        processed_directory=PROCESSED_DIRECTORY,
        manifest_file=MANIFEST_FILE,
    )

    successful = (manifest["status"] == "success").sum()
    failed = (manifest["status"] == "failed").sum()
    print(f"Finished: {successful} successful, {failed} failed")


if __name__ == "__main__":
    main()
