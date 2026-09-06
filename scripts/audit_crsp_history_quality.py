"""Audit downloaded CRSP history and save metadata-only reports."""

import argparse
from pathlib import Path

from ath_breakout.data.crsp_quality import audit_crsp_history, save_crsp_quality_report


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/state/crsp_daily_history_manifest.json"))
    parser.add_argument("--delistings", type=Path, default=Path("data/raw/crsp/delistings.parquet"))
    parser.add_argument("--ath-seed", type=Path, default=Path("data/raw/crsp/ath_seed_before_1993.parquet"))
    parser.add_argument("--summary", type=Path, default=Path("data/state/crsp_quality_summary.json"))
    parser.add_argument("--partitions-report", type=Path, default=Path("data/state/crsp_quality_partitions.csv"))
    parser.add_argument("--batch-size", type=int, default=250_000)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    def progress(done: int, total: int, result: dict) -> None:
        print(
            f"[{done}/{total}] {result['year']}: {result['status']}, "
            f"{result.get('rows', 0):,} rows", flush=True
        )

    summary, partitions = audit_crsp_history(
        arguments.manifest, arguments.delistings, arguments.ath_seed,
        arguments.batch_size, progress,
    )
    save_crsp_quality_report(
        summary, partitions, arguments.summary, arguments.partitions_report
    )
    print(
        f"Audit {summary['status']}: {summary['daily_rows']:,} daily rows, "
        f"{summary['delisting_rows']:,} delistings, "
        f"{summary['ath_seed_rows']:,} ATH seeds."
    )
    print(f"Summary: {arguments.summary}")
    print(f"Partitions: {arguments.partitions_report}")
    for error in summary["errors"]:
        print(f"ERROR: {error}")
    for warning in summary["warnings"]:
        print(f"WARNING: {warning}")
    return int(bool(summary["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
