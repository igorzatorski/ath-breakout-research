"""Run the current-universe ATH stock screener."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from ath_breakout.data.market_calendar import latest_completed_nyse_session
from ath_breakout.screening.reporting import print_candidate_tables
from ath_breakout.screening.screener import run_stock_screen, save_screen_results


REGISTRY_FILE = Path("data/state/security_registry.csv")
QUALITY_REPORT_FILE = Path("data/state/data_quality_report.csv")
PROCESSED_DIRECTORY = Path("data/processed/features")
OUTPUT_DIRECTORY = Path("outputs/screening")


def main() -> None:
    started_at = datetime.now()
    print(f"[{started_at:%Y-%m-%d %H:%M:%S}] Starting ATH stock screener")
    results, scan_date, summary = run_stock_screen(
        registry_file=REGISTRY_FILE,
        quality_report_file=QUALITY_REPORT_FILE,
        processed_directory=PROCESSED_DIRECTORY,
        show_progress=True,
    )
    output_file = OUTPUT_DIRECTORY / f"screener_{scan_date}.csv"
    save_screen_results(results, output_file)

    print("\nATH STOCK SCREENER")
    print(f"Market picture at session close: {scan_date}")
    latest_completed = latest_completed_nyse_session().date()
    print(f"Latest completed NYSE session: {latest_completed}")

    if scan_date < latest_completed:
        print(
            "WARNING: Local market data is behind. Run "
            "python scripts/run_data_pipeline.py before trusting this scan."
        )
    print(f"Current universe: {summary['current_universe']}")
    print(f"Scanned with good, current data: {summary['scanned']}")
    print(
        "Excluded because of unavailable or stale data: "
        f"{summary['excluded_quality_or_stale']}"
    )

    if "setup_state" in results.columns:
        setup_counts = results["setup_state"].value_counts()
    else:
        setup_counts = pd.Series(dtype="int64")

    print(f"Fresh breakouts: {setup_counts.get('fresh_breakout', 0)}")
    print(
        "ATH continuations: "
        f"{setup_counts.get('ath_continuation', 0)}"
    )
    print(
        "Approaching ATH: "
        f"{setup_counts.get('approaching_ath', 0)}"
    )
    print(f"Base ready: {setup_counts.get('base_ready', 0)}")
    if "setup_state" not in results.columns:
        print("\nNo breakout or base-ready candidates passed every filter.")
    else:
        print_candidate_tables(results)

    elapsed = datetime.now() - started_at
    print(f"\nComplete ranking-ready table: {output_file}")
    print(f"Finished in: {elapsed}")


if __name__ == "__main__":
    pd.set_option("display.width", 180)
    main()
