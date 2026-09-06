"""Run the ATH stock screener for the latest or a selected session."""

import argparse
import sys
import subprocess
from datetime import date
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ath_breakout.data.market_calendar import latest_completed_nyse_session  # noqa: E402
from ath_breakout.screening.reporting import print_candidate_tables  # noqa: E402
from ath_breakout.screening.screener import run_stock_screen, save_screen_results  # noqa: E402


REGISTRY_FILE = Path("data/state/security_registry.csv")
QUALITY_REPORT_FILE = Path("data/state/data_quality_report.csv")
PROCESSED_DIRECTORY = Path("data/processed/features")
OUTPUT_DIRECTORY = Path("outputs/screening")


def parse_arguments(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of", type=date.fromisoformat,
        help="historical completed NYSE session (YYYY-MM-DD)",
    )
    parser.add_argument("--latest", action="store_true", help="use latest local session")
    return parser.parse_args(arguments)


def request_scan_date() -> date | None:
    """Ask for a date when the script is launched from an interactive terminal."""
    while True:
        value = input("Choose your date (YYYY-MM-DD; Enter = latest): ").strip()
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD, for example 2024-01-02.")


def main(arguments=None) -> None:
    args = parse_arguments(arguments if arguments is not None else ["--latest"])
    if args.as_of is not None:
        from scripts.maintenance.run_historical_screener import main as historical_main
        historical_main([args.as_of.isoformat()])
        return
    if not args.latest:
        requested = request_scan_date()
        if requested is not None:
            from scripts.maintenance.run_historical_screener import main as historical_main
            historical_main([requested.isoformat()])
            return
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/maintenance/run_data_pipeline.py")], check=True, cwd=PROJECT_ROOT)
    started_at = datetime.now()
    print(f"[{started_at:%Y-%m-%d %H:%M:%S}] Starting ATH stock screener")
    results, scan_date, summary = run_stock_screen(
        registry_file=REGISTRY_FILE,
        quality_report_file=QUALITY_REPORT_FILE,
        processed_directory=PROCESSED_DIRECTORY,
        show_progress=True,
    )
    latest_completed = latest_completed_nyse_session().date()
    if scan_date != latest_completed:
        raise RuntimeError(
            f"Live screener requires {latest_completed}; local quality report is {scan_date}. "
            "Run scripts/maintenance/run_data_pipeline.py first."
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
            "python scripts/maintenance/run_data_pipeline.py before trusting this scan."
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
    main(sys.argv[1:])
