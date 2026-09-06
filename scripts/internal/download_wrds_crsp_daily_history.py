"""Download resumable yearly CRSP daily partitions for the research universe."""

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ath_breakout.data.adapters.crsp import CRSP_DAILY_COLUMNS, stream_crsp_daily
from ath_breakout.data.adapters.crsp_delistings import download_crsp_delistings
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_UNIVERSE = Path("data/processed/crsp/universe_permnos.parquet")
DEFAULT_OUTPUT_DIRECTORY = Path("data/raw/crsp/daily_by_year")
DEFAULT_DELISTINGS = Path("data/raw/crsp/delistings.parquet")
DEFAULT_ATH_SEED = Path("data/raw/crsp/ath_seed_before_1993.parquet")
DEFAULT_MANIFEST = Path("data/state/crsp_daily_history_manifest.json")

STRING_COLUMNS = {
    "security_id", "ticker", "return_missing_flag", "return_duration_flag",
    "distribution_return_flag", "primary_exchange", "conditional_type",
    "trading_status", "share_type", "security_type", "security_subtype",
    "us_incorporation_flag", "issuer_type", "delisting_flag", "source",
}
INTEGER_COLUMNS = {"permno", "permco"}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download resumable CRSP daily history for universe PERMNOs."
    )
    parser.add_argument("--username", default=os.environ.get("WRDS_USERNAME"))
    parser.add_argument("--start-date", default="1993-01-01")
    parser.add_argument("--end-date", default="2026-06-30")
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument(
        "--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY
    )
    parser.add_argument("--delistings", type=Path, default=DEFAULT_DELISTINGS)
    parser.add_argument("--ath-seed", type=Path, default=DEFAULT_ATH_SEED)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--chunk-size", type=int, default=250_000)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def yearly_bounds(start_date: str, end_date: str):
    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()
    if start > end:
        raise ValueError("Start date cannot follow end date")
    for year in range(start.year, end.year + 1):
        yield max(start, pd.Timestamp(year, 1, 1)), min(
            end, pd.Timestamp(year, 12, 31)
        )


def format_duration(seconds: float) -> str:
    seconds = max(0, round(seconds))
    hours, remainder = divmod(seconds, 3_600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:d}h {minutes:02d}m" if hours else f"{minutes:d}m {seconds:02d}s"


def progress_line(completed: int, total: int, started_at: float) -> str:
    width = 28
    fraction = completed / total if total else 1.0
    filled = min(width, round(width * fraction))
    elapsed = time.monotonic() - started_at
    eta = elapsed / completed * (total - completed) if completed else 0
    return (
        f"[{'#' * filled}{'-' * (width - filled)}] {completed}/{total} "
        f"({fraction:6.1%}) | elapsed {format_duration(elapsed)} | "
        f"ETA {format_duration(eta)}"
    )


def parquet_schema() -> pa.Schema:
    fields = []
    for column in CRSP_DAILY_COLUMNS:
        if column in STRING_COLUMNS:
            dtype = pa.string()
        elif column in INTEGER_COLUMNS:
            dtype = pa.int64()
        elif column == "date":
            dtype = pa.timestamp("ns")
        else:
            dtype = pa.float64()
        fields.append(pa.field(column, dtype, nullable=True))
    return pa.schema(fields)


def write_year_partition(connection, permnos, start, end, destination, chunksize):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp.parquet")
    if temporary.exists():
        temporary.unlink()
    schema = parquet_schema()
    writer = pq.ParquetWriter(temporary, schema=schema, compression="zstd")
    rows = 0
    chunks = 0
    previous_key = None
    try:
        for chunk in stream_crsp_daily(
            connection, permnos, start.date(), end.date(), chunksize=chunksize
        ):
            if not chunk.empty:
                first_key = (int(chunk.iloc[0]["permno"]), chunk.iloc[0]["date"])
                if previous_key is not None and first_key <= previous_key:
                    raise ValueError("CRSP stream is duplicated or out of order")
                previous_key = (
                    int(chunk.iloc[-1]["permno"]), chunk.iloc[-1]["date"]
                )
            table = pa.Table.from_pandas(
                chunk, schema=schema, preserve_index=False, safe=False
            )
            writer.write_table(table)
            rows += len(chunk)
            chunks += 1
            print(f"    received chunk {chunks}: {rows:,} rows so far", flush=True)
    except BaseException:
        writer.close()
        if temporary.exists():
            temporary.unlink()
        raise
    writer.close()
    temporary.replace(destination)
    return rows, chunks


def build_ath_seed(connection, permnos, start_date: str) -> pd.DataFrame:
    return connection.raw_sql(
        """
        SELECT
            permno,
            MAX(dlyclose / NULLIF(dlycumfacpr, 0)) AS prior_comparable_high,
            MIN(dlycaldt) AS first_observation_date,
            MAX(dlycaldt) AS last_observation_date,
            COUNT(*) AS observation_count
        FROM crsp_q_stock.dsf_v2
        WHERE permno = ANY(%(permnos)s)
          AND dlycaldt < %(start_date)s
          AND dlyclose > 0
          AND dlycumfacpr > 0
        GROUP BY permno
        ORDER BY permno
        """,
        params={"permnos": permnos, "start_date": start_date},
        date_cols=["first_observation_date", "last_observation_date"],
    )


def write_manifest(path: Path, contents: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp.json')
    temporary.write_text(json.dumps(contents, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    arguments = parse_arguments()
    username = arguments.username or input("WRDS username: ").strip()
    if not username:
        raise SystemExit("A WRDS username is required.")
    if arguments.chunk_size <= 0:
        raise SystemExit("Chunk size must be positive.")
    if not arguments.universe.exists():
        raise SystemExit(f"Universe PERMNO file is missing: {arguments.universe}")

    try:
        import wrds
    except ImportError as error:
        raise SystemExit(
            'WRDS support is not installed. Run: python -m pip install -e ".[wrds]"'
        ) from error

    universe = pd.read_parquet(arguments.universe, columns=["permno"])
    permnos = sorted(universe["permno"].dropna().astype(int).unique().tolist())
    if not permnos:
        raise SystemExit("Universe contains no PERMNOs.")

    connection_arguments = {"wrds_username": username}
    password = load_wrds_password(username)
    if password is not None:
        connection_arguments["wrds_password"] = password

    bounds = list(yearly_bounds(arguments.start_date, arguments.end_date))
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    partitions = []
    started_at = time.monotonic()
    print(f"Downloading CRSP daily history for {len(permnos):,} PERMNOs...", flush=True)
    connection = wrds.Connection(**connection_arguments)
    try:
        available = connection.raw_sql("SELECT MAX(dlycaldt) AS last_date FROM crsp_q_stock.dsf_v2")
        if pd.Timestamp(arguments.end_date) > pd.Timestamp(available.iloc[0]['last_date']):
            raise ValueError(f"Requested end exceeds WRDS coverage: {available.iloc[0]['last_date']}")
        if pd.isna(available.iloc[0]["last_date"]):
            raise ValueError("WRDS returned no CRSP coverage date")
        previous = json.loads(arguments.manifest.read_text()) if arguments.manifest.exists() else {}
        # Legacy manifests do not identify universe contents: refresh conservatively.
        same_universe = previous.get('permnos') == permnos
        for number, (start, end) in enumerate(bounds, start=1):
            destination = arguments.output_directory / f"daily_{start.year}.parquet"
            covered = same_universe and previous.get('status') == 'complete' and pd.Timestamp(previous['start_date']) <= start and pd.Timestamp(previous['end_date']) >= end
            resumed = next((p for p in previous.get("completed_partitions", []) if p["year"] == start.year), {})
            covered = covered or (same_universe and resumed.get("start_date") == str(start.date()) and resumed.get("end_date") == str(end.date()))
            if destination.exists() and not arguments.overwrite and covered:
                rows = pq.read_metadata(destination).num_rows
                print(
                    f"[{number}/{len(bounds)}] {start.year}: existing, {rows:,} rows.",
                    flush=True,
                )
            else:
                print(
                    f"[{number}/{len(bounds)}] {start.year}: querying WRDS "
                    f"({start.date()} to {end.date()})...",
                    flush=True,
                )
                rows, chunks = write_year_partition(
                    connection, permnos, start, end, destination, arguments.chunk_size
                )
                print(
                    f"[{number}/{len(bounds)}] {start.year}: saved {rows:,} rows "
                    f"from {chunks} chunks.",
                    flush=True,
                )
            partitions.append(
                {"year": start.year, "path": str(destination.resolve()), "rows": rows, "start_date": str(start.date()), "end_date": str(end.date())}
            )
            write_manifest(
                arguments.manifest,
                {
                    "status": "running",
                    "permnos": permnos,
                    "start_date": arguments.start_date,
                    "end_date": arguments.end_date,
                    "unique_permnos": len(permnos),
                    "completed_partitions": partitions,
                },
            )
            print(progress_line(number, len(bounds), started_at), flush=True)

        if not arguments.ath_seed.exists() or arguments.overwrite or not same_universe or previous.get("start_date") != arguments.start_date:
            print("Building pre-start all-time-high seed...", flush=True)
            seed = build_ath_seed(connection, permnos, arguments.start_date)
            arguments.ath_seed.parent.mkdir(parents=True, exist_ok=True)
            temporary_seed = arguments.ath_seed.with_suffix(".tmp.parquet")
            seed.to_parquet(temporary_seed, index=False)
            temporary_seed.replace(arguments.ath_seed)
        else:
            seed = pd.read_parquet(arguments.ath_seed)

        if not arguments.delistings.exists() or arguments.overwrite or previous.get('end_date') != arguments.end_date or not same_universe:
            print("Downloading detailed delisting outcomes...", flush=True)
            delistings = download_crsp_delistings(
                connection,
                permnos=permnos,
                start_date=arguments.start_date,
                end_date=arguments.end_date,
            )
            arguments.delistings.parent.mkdir(parents=True, exist_ok=True)
            temporary_delistings = arguments.delistings.with_suffix(".tmp.parquet")
            delistings.to_parquet(temporary_delistings, index=False)
            temporary_delistings.replace(arguments.delistings)
        else:
            delistings = pd.read_parquet(arguments.delistings)
    finally:
        connection.close()

    manifest = {
        "permnos": permnos,
        "status": "complete",
        "start_date": arguments.start_date,
        "end_date": arguments.end_date,
        "unique_permnos": len(permnos),
        "daily_rows": sum(item["rows"] for item in partitions),
        "ath_seed_rows": len(seed),
        "delisting_rows": len(delistings),
        "partitions": partitions,
        "ath_seed_path": str(arguments.ath_seed.resolve()),
        "delistings_path": str(arguments.delistings.resolve()),
    }
    write_manifest(arguments.manifest, manifest)
    print(f"Complete daily rows: {manifest['daily_rows']:,}.", flush=True)
    print(f"ATH seed rows: {manifest['ath_seed_rows']:,}.", flush=True)
    print(f"Delisting rows: {manifest['delisting_rows']:,}.", flush=True)
    print(f"Manifest: {arguments.manifest.resolve()}", flush=True)


if __name__ == "__main__":
    main()
