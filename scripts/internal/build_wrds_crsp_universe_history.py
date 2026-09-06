"""Build resumable yearly partitions of monthly CRSP liquidity universes."""

import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

import pandas as pd

from ath_breakout.data.adapters.crsp_universe import (
    download_crsp_universe_history_batch,
)
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_DIRECTORY = Path("data/processed/crsp/universe_history")
DEFAULT_MANIFEST = Path("data/state/crsp_universe_history_manifest.json")


def format_duration(seconds: float) -> str:
    """Format a duration for compact terminal progress output."""
    seconds = max(0, round(seconds))
    hours, remainder = divmod(seconds, 3_600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}h {minutes:02d}m"
    return f"{minutes:d}m {seconds:02d}s"


def progress_line(completed: int, total: int, started_at: float) -> str:
    """Return a fixed-width progress bar with elapsed time and ETA."""
    width = 28
    fraction = completed / total if total else 1.0
    filled = min(width, round(width * fraction))
    bar = "#" * filled + "-" * (width - filled)
    elapsed = time.monotonic() - started_at
    eta = elapsed / completed * (total - completed) if completed else 0
    return (
        f"[{bar}] {completed:>2}/{total} ({fraction:6.1%}) | "
        f"elapsed {format_duration(elapsed)} | ETA {format_duration(eta)}"
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build resumable monthly CRSP universe history partitions."
    )
    parser.add_argument("--username", default=os.environ.get("WRDS_USERNAME"))
    parser.add_argument("--start-year", type=int, default=1993)
    parser.add_argument("--end-date", default="2026-06-30")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def yearly_bounds(start_year: int, end_date: date | str):
    """Yield yearly formation bounds with enough prior history for lookback."""
    final_date = pd.Timestamp(end_date).normalize()
    if start_year > final_date.year:
        raise ValueError("Start year cannot follow end date")
    for year in range(start_year, final_date.year + 1):
        formation_start = pd.Timestamp(year=year, month=1, day=1)
        formation_end = min(
            pd.Timestamp(year=year, month=12, day=31), final_date
        )
        lookback_start = formation_start - pd.Timedelta(days=100)
        yield lookback_start, formation_start, formation_end


def main() -> None:
    arguments = parse_arguments()
    username = arguments.username or input("WRDS username: ").strip()
    if not username:
        raise SystemExit("A WRDS username is required.")

    try:
        import wrds
    except ImportError as error:
        raise SystemExit(
            'WRDS support is not installed. Run: python -m pip install -e ".[wrds]"'
        ) from error

    connection_arguments = {"wrds_username": username}
    password = load_wrds_password(username)
    if password is not None:
        connection_arguments["wrds_password"] = password

    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    partitions = []
    print("Building resumable CRSP universe-history partitions...", flush=True)
    connection = wrds.Connection(**connection_arguments)
    try:
        previous = json.loads(arguments.manifest.read_text()) if arguments.manifest.exists() else {}
        bounds = list(yearly_bounds(arguments.start_year, arguments.end_date))
        started_at = time.monotonic()
        for number, (lookback_start, formation_start, formation_end) in enumerate(
            bounds, start=1
        ):
            year = formation_start.year
            destination = arguments.output_directory / f"universe_{year}.parquet"
            covered = previous.get('requested_end_date', '') >= str(formation_end.date())
            if destination.exists() and not arguments.overwrite and covered:
                batch = pd.read_parquet(destination)
                print(
                    f"[{number}/{len(bounds)}] {year}: existing partition, "
                    f"{len(batch):,} rows.",
                    flush=True,
                )
            else:
                print(
                    f"[{number}/{len(bounds)}] {year}: querying WRDS...",
                    flush=True,
                )
                batch = download_crsp_universe_history_batch(
                    connection,
                    lookback_start=lookback_start.date(),
                    formation_start=formation_start.date(),
                    formation_end=formation_end.date(),
                )
                batch.to_parquet(destination, index=False)
                print(
                    f"[{number}/{len(bounds)}] {year}: saved {len(batch):,} rows "
                    f"across {batch['formation_date'].nunique():,} snapshots.",
                    flush=True,
                )
            partitions.append(
                {
                    "year": year,
                    "path": str(destination.resolve()),
                    "rows": len(batch),
                    "snapshots": int(batch["formation_date"].nunique()),
                    "unique_permnos": int(batch["permno"].nunique()),
                }
            )
            print(progress_line(number, len(bounds), started_at), flush=True)
    finally:
        connection.close()

    all_parts = [pd.read_parquet(item["path"]) for item in partitions]
    history = pd.concat(all_parts, ignore_index=True)
    combined_path = arguments.output_directory.parent / "universe_memberships.parquet"
    history.to_parquet(combined_path, index=False)
    permnos_path = arguments.output_directory.parent / "universe_permnos.parquet"
    permnos = (
        history[["security_id", "permno"]]
        .drop_duplicates()
        .sort_values("permno")
        .reset_index(drop=True)
    )
    permnos.to_parquet(permnos_path, index=False)
    manifest = {
        "start_year": arguments.start_year,
        "requested_end_date": str(arguments.end_date),
        "rows": len(history),
        "snapshots": int(history["formation_date"].nunique()),
        "unique_permnos": int(history["permno"].nunique()),
        "first_formation_date": str(history["formation_date"].min().date()),
        "last_formation_date": str(history["formation_date"].max().date()),
        "combined_path": str(combined_path.resolve()),
        "permnos_path": str(permnos_path.resolve()),
        "partitions": partitions,
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Complete rows: {len(history):,}.")
    print(f"Monthly snapshots: {manifest['snapshots']:,}.")
    print(f"Unique PERMNOs: {manifest['unique_permnos']:,}.")
    print(f"Combined local file: {combined_path.resolve()}")
    print(f"Unique PERMNO file: {permnos_path.resolve()}")
    print(f"Manifest: {arguments.manifest.resolve()}")


if __name__ == "__main__":
    main()
