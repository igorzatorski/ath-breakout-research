"""Refresh the current universe and incrementally update all market data."""

from datetime import datetime
from pathlib import Path

from ath_breakout.data.market_update import update_market_data
from ath_breakout.data.quality import build_data_quality_report
from ath_breakout.data.quality import save_data_quality_report
from ath_breakout.data.security_registry import update_security_registry
from ath_breakout.data.universe import load_universe_csv
from ath_breakout.data.universe_update import ensure_weekly_iwv_snapshot


UNIVERSE_DIRECTORY = Path("data/universe")
RAW_DIRECTORY = Path("data/raw/yfinance")
PROCESSED_DIRECTORY = Path("data/processed/features")
MANIFEST_FILE = Path("data/state/yfinance_manifest.csv")
REGISTRY_FILE = Path("data/state/security_registry.csv")
QUALITY_REPORT_FILE = Path("data/state/data_quality_report.csv")


def main() -> None:
    started_at = datetime.now()
    print(f"[{started_at:%Y-%m-%d %H:%M:%S}] Starting market-data update")

    universe_file = ensure_weekly_iwv_snapshot(UNIVERSE_DIRECTORY)
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"Using universe: {universe_file}"
    )
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

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Building quality report")
    quality_report = build_data_quality_report(
        manifest=manifest,
        processed_directory=PROCESSED_DIRECTORY,
        today=datetime.now().date(),
    )
    save_data_quality_report(quality_report, QUALITY_REPORT_FILE)
    quality_counts = quality_report["quality_status"].value_counts()

    for quality_status, count in quality_counts.items():
        print(f"  {quality_status}: {count}")

    elapsed = datetime.now() - started_at
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Finished: "
        f"{successful} successful, {failed} failed | elapsed: {elapsed}"
    )
    print(f"Quality report: {QUALITY_REPORT_FILE}")


if __name__ == "__main__":
    main()
