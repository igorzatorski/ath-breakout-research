"""Run the current-universe stock screener at a historical session close."""

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from ath_breakout.data.market_calendar import resolve_completed_session
from ath_breakout.screening.reporting import print_candidate_tables
from ath_breakout.screening.screener import run_stock_screen, save_screen_results


REGISTRY_FILE = Path("data/state/security_registry.csv")
QUALITY_REPORT_FILE = Path("data/state/data_quality_report.csv")
PROCESSED_DIRECTORY = Path("data/processed/features")
OUTPUT_DIRECTORY = Path("outputs/screening/history")


def parse_date(value: str) -> date:
    """Parse an ISO date supplied on the command line."""
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "date must use YYYY-MM-DD format"
        ) from error


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Return validated command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Recreate the current-universe screener at a past close."
    )
    parser.add_argument(
        "date",
        type=parse_date,
        help="completed NYSE session in YYYY-MM-DD format",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> None:
    """Run and save one historical, no-look-ahead screen."""
    args = parse_arguments(arguments)
    scan_date = resolve_completed_session(as_of=args.date).date()
    started_at = datetime.now()
    print(
        f"[{started_at:%Y-%m-%d %H:%M:%S}] "
        f"Starting historical screen at {scan_date}"
    )

    results, _, summary = run_stock_screen(
        registry_file=REGISTRY_FILE,
        quality_report_file=QUALITY_REPORT_FILE,
        processed_directory=PROCESSED_DIRECTORY,
        as_of_date=scan_date,
        show_progress=True,
    )
    output_file = OUTPUT_DIRECTORY / f"screener_{scan_date}.csv"
    save_screen_results(results, output_file)

    print("\nHISTORICAL ATH STOCK SCREENER")
    print(f"Market picture at session close: {scan_date}")
    print(
        "RESEARCH LIMITATION: prices and features are point-in-time, but the "
        "universe uses current IWV holdings and therefore has survivorship bias."
    )
    print(f"Current-universe proxy securities: {summary['current_universe']}")
    print(f"Securities with data on this session: {summary['scanned']}")
    print(
        "Unavailable on this historical session: "
        f"{summary['excluded_quality_or_stale']}"
    )

    if "setup_state" not in results.columns:
        print("\nNo securities had a usable snapshot on this session.")
    else:
        setup_counts = results["setup_state"].value_counts()
        print(f"Fresh breakouts: {setup_counts.get('fresh_breakout', 0)}")
        print(f"Base ready: {setup_counts.get('base_ready', 0)}")
        print_candidate_tables(results)

    elapsed = datetime.now() - started_at
    print(f"\nComplete historical table: {output_file}")
    print(f"Finished in: {elapsed}")


if __name__ == "__main__":
    pd.set_option("display.width", 180)
    main()
