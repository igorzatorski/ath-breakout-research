"""Build resumable yearly CRSP strategy-ready partitions."""

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from ath_breakout.data.crsp_processing import (
    add_stateful_crsp_features,
    initialize_crsp_feature_state,
    normalize_crsp_strategy_rows,
    restore_crsp_feature_state,
)


DEFAULT_SOURCE_MANIFEST = Path("data/state/crsp_daily_history_manifest.json")
DEFAULT_SEED = Path("data/raw/crsp/ath_seed_before_1993.parquet")
DEFAULT_OUTPUT = Path("data/processed/crsp/strategy_by_year")
DEFAULT_MANIFEST = Path("data/state/crsp_strategy_history_manifest.json")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--ath-seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--limit-years", type=int)
    return parser.parse_args()


def build_strategy_history(
    source_manifest: Path,
    ath_seed_path: Path,
    output_directory: Path,
    manifest_path: Path,
    overwrite: bool = False,
    limit_years: int | None = None,
) -> dict:
    """Build or resume chronological processed partitions and return a manifest."""
    source = json.loads(source_manifest.read_text(encoding="utf-8"))
    if source.get("status") != "complete":
        raise ValueError("CRSP source manifest is not complete")
    partitions = source["partitions"]
    if limit_years is not None:
        if limit_years <= 0:
            raise ValueError("limit_years must be positive")
        partitions = partitions[:limit_years]

    output_directory.mkdir(parents=True, exist_ok=True)
    seed = pd.read_parquet(ath_seed_path)
    state = initialize_crsp_feature_state(seed)
    output_partitions = []
    totals = {
        "input_rows": 0, "output_rows": 0, "missing_key_rows": 0,
        "invalid_price_factor_rows": 0, "invalid_share_factor_rows": 0,
        "incomplete_ohlcv_rows": 0, "invalid_price_rows": 0,
        "invalid_volume_rows": 0, "inconsistent_ohlc_rows": 0,
    }
    started = time.monotonic()
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    previous_parts = {p['year']: p for p in previous.get('partitions', [])}
    rebuild = overwrite or previous.get('seed_mtime_ns') != ath_seed_path.stat().st_mtime_ns
    for number, item in enumerate(partitions, start=1):
        year = int(item["year"])
        destination = output_directory / f"strategy_{year}.parquet"
        source_mtime = Path(item['path']).stat().st_mtime_ns
        rebuild = rebuild or previous_parts.get(year, {}).get('source_mtime_ns') != source_mtime
        if destination.exists() and not rebuild:
            processed = pd.read_parquet(destination)
            restore_crsp_feature_state(processed, state)
            status = "existing"
            report = None
        else:
            raw = pd.read_parquet(item["path"])
            canonical, report = normalize_crsp_strategy_rows(raw)
            processed = add_stateful_crsp_features(canonical, state)
            temporary = destination.with_suffix(".tmp.parquet")
            processed.to_parquet(temporary, index=False)
            temporary.replace(destination)
            status = "built"
            for key, value in report.to_dict().items():
                totals[key] += value
        output_partitions.append({
            "year": year, "path": str(destination.resolve()),
            "source_mtime_ns": source_mtime,
            "rows": len(processed), "source_rows": int(item["rows"]),
            "status": status,
            "rejected_rows": int(item["rows"]) - len(processed),
        })
        elapsed = time.monotonic() - started
        print(
            f"[{number}/{len(partitions)}] {year}: {status} {len(processed):,} rows "
            f"| elapsed {elapsed / 60:.1f}m",
            flush=True,
        )

    manifest = {
        "seed_mtime_ns": ath_seed_path.stat().st_mtime_ns,
        "status": "complete" if len(partitions) == len(source["partitions"]) else "sample",
        "source_manifest": str(source_manifest.resolve()),
        "ath_seed": str(ath_seed_path.resolve()),
        "partition_count": len(output_partitions),
        "source_rows": sum(item["source_rows"] for item in output_partitions),
        "output_rows": sum(item["rows"] for item in output_partitions),
        "rejected_rows": sum(item["rejected_rows"] for item in output_partitions),
        "full_run_totals": {
            "input_rows": sum(item["source_rows"] for item in output_partitions),
            "output_rows": sum(item["rows"] for item in output_partitions),
            "rejected_rows": sum(item["rejected_rows"] for item in output_partitions),
        },
        "newly_built_quality_totals": totals,
        "partitions": output_partitions,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_manifest = manifest_path.with_suffix(".tmp.json")
    temporary_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary_manifest.replace(manifest_path)
    return manifest


def main() -> None:
    arguments = parse_arguments()
    result = build_strategy_history(
        arguments.source_manifest, arguments.ath_seed,
        arguments.output_directory, arguments.manifest,
        arguments.overwrite, arguments.limit_years,
    )
    print(
        f"Complete: {result['output_rows']:,} usable rows; "
        f"{result['rejected_rows']:,} rejected rows."
    )
    print(f"Manifest: {arguments.manifest.resolve()}")


if __name__ == "__main__":
    main()
