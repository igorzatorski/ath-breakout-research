"""Run the complete daily IWV and market-data pipeline."""

import argparse
from datetime import date, datetime
from pathlib import Path
import time

import pandas as pd

from ath_breakout.data.adapters.yfinance import yahoo_session_is_available
from ath_breakout.data.market_update import update_market_data
from ath_breakout.data.market_calendar import resolve_completed_session
from ath_breakout.data.quality import build_data_quality_report
from ath_breakout.data.quality import save_data_quality_report
from ath_breakout.data.security_registry import update_security_registry
from ath_breakout.data.universe import load_universe_csv
from ath_breakout.data.universe_update import ensure_daily_iwv_snapshot


UNIVERSE_DIRECTORY = Path("data/universe")
RAW_DIRECTORY = Path("data/raw/yfinance")
PROCESSED_DIRECTORY = Path("data/processed/features")
MANIFEST_FILE = Path("data/state/yfinance_manifest.csv")
REGISTRY_FILE = Path("data/state/security_registry.csv")
QUALITY_REPORT_FILE = Path("data/state/data_quality_report.csv")
BENCHMARK_MANIFEST_FILE = Path("data/state/benchmark_manifest.csv")
BENCHMARK_UNIVERSE = pd.DataFrame(
    {"security_id": ["IWV", "SPY"], "ticker": ["IWV", "SPY"]}
)


def parse_arguments() -> argparse.Namespace:
    """Read data-pipeline command-line options."""
    parser = argparse.ArgumentParser(
        description="Update and process the complete market-data registry."
    )
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        help="Completed NYSE session in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help=(
            "Redownload full Yahoo history for every known security and "
            "replace its stored history after a successful download"
        ),
    )
    parser.add_argument(
        "--max-wait-minutes",
        type=int,
        default=60,
        help=(
            "maximum time to wait for Yahoo to publish today's completed "
            "daily session (default: 60)"
        ),
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=120,
        help="seconds between Yahoo availability checks (default: 120)",
    )
    return parser.parse_args()


def wait_for_yahoo_session(
    target_session: date,
    max_wait_minutes: int,
    poll_seconds: int,
) -> None:
    """Wait until Yahoo exposes the target daily bar instead of going stale."""
    if max_wait_minutes < 0:
        raise ValueError("max_wait_minutes cannot be negative")
    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be greater than zero")

    deadline = time.monotonic() + max_wait_minutes * 60
    attempt = 1
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"[{timestamp}] Checking Yahoo daily bar for SPY on "
            f"{target_session} (attempt {attempt})",
            flush=True,
        )
        if yahoo_session_is_available(target_session):
            print(f"Yahoo session {target_session} is available.")
            return
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Yahoo has not published session {target_session} after "
                f"waiting {max_wait_minutes} minutes. Run the pipeline again "
                "later or select an earlier completed session with --as-of."
            )
        remaining = max(0, int(deadline - time.monotonic()))
        sleep_seconds = min(poll_seconds, remaining)
        print(
            f"Yahoo is not ready yet. Retrying in {sleep_seconds} seconds...",
            flush=True,
        )
        time.sleep(sleep_seconds)
        attempt += 1


def main() -> None:
    arguments = parse_arguments()
    started_at = datetime.now().astimezone()
    target_session = resolve_completed_session(
        as_of=arguments.as_of,
        now=started_at,
    ).date()
    print(f"[{started_at:%Y-%m-%d %H:%M:%S}] Starting complete data pipeline")
    print(f"Target completed NYSE session: {target_session}")
    if arguments.full_refresh:
        print("Mode: FULL REFRESH of every known security")
    else:
        print("Mode: incremental update")

    wait_for_yahoo_session(
        target_session,
        arguments.max_wait_minutes,
        arguments.poll_seconds,
    )

    universe_file = ensure_daily_iwv_snapshot(UNIVERSE_DIRECTORY)
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
        download_through=target_session,
        full_refresh=arguments.full_refresh,
        retry_failed_now=True,
    )

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Updating IWV benchmark")
    benchmark_manifest = update_market_data(
        universe=BENCHMARK_UNIVERSE,
        raw_directory=RAW_DIRECTORY,
        processed_directory=PROCESSED_DIRECTORY,
        manifest_file=BENCHMARK_MANIFEST_FILE,
        download_through=target_session,
        full_refresh=arguments.full_refresh,
        retry_failed_now=True,
    )
    for _, benchmark in benchmark_manifest.iterrows():
        print(f"{benchmark['ticker']} benchmark: {benchmark['status']}")

    successful = (manifest["status"] == "success").sum()
    failed = (manifest["status"] == "failed").sum()
    deferred = (manifest["status"] == "retry_deferred").sum()

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Building quality report")
    quality_report = build_data_quality_report(
        manifest=manifest,
        processed_directory=PROCESSED_DIRECTORY,
        today=datetime.now().date(),
        expected_latest_date=target_session,
    )
    save_data_quality_report(quality_report, QUALITY_REPORT_FILE)

    quality_counts = quality_report["quality_status"].value_counts()
    for quality_status, count in quality_counts.items():
        print(f"  {quality_status}: {count}")

    finished_at = datetime.now().astimezone()
    elapsed = finished_at - started_at
    print(
        f"[{finished_at:%Y-%m-%d %H:%M:%S}] Finished: "
        f"{successful} successful, {failed} failed, "
        f"{deferred} waiting for retry | elapsed: {elapsed}"
    )

    if failed > 0:
        failed_tickers = manifest.loc[
            manifest["status"] == "failed",
            "ticker",
        ].tolist()
        print(f"Failed tickers: {', '.join(failed_tickers)}")
        print(f"Details: {MANIFEST_FILE}")
        print("Existing files were preserved; the next run will retry them.")

    if deferred > 0:
        print(
            "Deferred tickers reached their retry limit and will be tried "
            "again on their scheduled dates."
        )

    print(f"Quality report: {QUALITY_REPORT_FILE}")


if __name__ == "__main__":
    main()
