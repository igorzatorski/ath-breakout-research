"""Read-only quality audit for locally stored CRSP history."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from ath_breakout.data.adapters.crsp import CRSP_DAILY_COLUMNS


AUDIT_COLUMNS = [
    "permno", "date", "open", "high", "low", "close", "volume",
    "total_return", "return_missing_flag", "source",
]


def audit_daily_partition(
    path: str | Path,
    year: int,
    expected_rows: int | None = None,
    batch_size: int = 250_000,
) -> dict:
    """Audit one sorted yearly partition without loading it wholly into memory."""
    path = Path(path)
    parquet = pq.ParquetFile(path)
    missing_columns = sorted(set(CRSP_DAILY_COLUMNS) - set(parquet.schema_arrow.names))
    if missing_columns:
        return {
            "year": year, "path": str(path), "status": "error",
            "rows": parquet.metadata.num_rows, "expected_rows": expected_rows,
            "errors": f"missing columns: {', '.join(missing_columns)}",
        }

    totals = {
        "rows": 0, "duplicate_keys": 0, "out_of_order_keys": 0,
        "null_permno": 0, "null_date": 0, "null_close": 0,
        "null_total_return": 0, "unflagged_null_total_return": 0,
        "null_open": 0, "null_high": 0, "null_low": 0, "null_volume": 0,
        "nonpositive_close": 0, "negative_volume": 0,
        "ohlc_high_violations": 0, "ohlc_low_violations": 0,
        "unexpected_source": 0,
    }
    first_date = last_date = None
    previous_key: tuple[int, pd.Timestamp] | None = None

    for batch in parquet.iter_batches(columns=AUDIT_COLUMNS, batch_size=batch_size):
        data = batch.to_pandas()
        data["date"] = pd.to_datetime(data["date"])
        totals["rows"] += len(data)
        for column in (
            "permno", "date", "close", "total_return", "open", "high", "low",
            "volume",
        ):
            totals[f"null_{column}"] += int(data[column].isna().sum())
        missing_return = data["total_return"].isna()
        missing_flag = (
            data["return_missing_flag"].fillna("").astype(str).str.strip().eq("")
        )
        totals["unflagged_null_total_return"] += int(
            (missing_return & missing_flag).sum()
        )
        totals["nonpositive_close"] += int((data["close"].dropna() <= 0).sum())
        totals["negative_volume"] += int((data["volume"].dropna() < 0).sum())
        complete = data[["open", "high", "low", "close"]].notna().all(axis=1)
        ohlc = data.loc[complete, ["open", "high", "low", "close"]]
        totals["ohlc_high_violations"] += int(
            (ohlc["high"] < ohlc[["open", "low", "close"]].max(axis=1)).sum()
        )
        totals["ohlc_low_violations"] += int(
            (ohlc["low"] > ohlc[["open", "high", "close"]].min(axis=1)).sum()
        )
        totals["unexpected_source"] += int(
            data["source"].fillna("").ne("CRSP CIZ quarterly").sum()
        )

        valid = data.loc[
            data["permno"].notna() & data["date"].notna(), ["permno", "date"]
        ]
        totals["duplicate_keys"] += int(valid.duplicated().sum())
        keys = list(valid.itertuples(index=False, name=None))
        if keys:
            if previous_key is not None:
                totals["duplicate_keys"] += int(keys[0] == previous_key)
                totals["out_of_order_keys"] += int(keys[0] < previous_key)
            totals["out_of_order_keys"] += sum(
                current < prior for prior, current in zip(keys, keys[1:])
            )
            previous_key = keys[-1]
        batch_min, batch_max = data["date"].min(), data["date"].max()
        first_date = batch_min if first_date is None else min(first_date, batch_min)
        last_date = batch_max if last_date is None else max(last_date, batch_max)

    errors = []
    warnings = []
    if expected_rows is not None and totals["rows"] != expected_rows:
        errors.append(f"row count {totals['rows']:,} != manifest {expected_rows:,}")
    for key in (
        "duplicate_keys", "out_of_order_keys", "null_permno", "null_date",
        "nonpositive_close", "negative_volume", "unexpected_source",
    ):
        if totals[key]:
            errors.append(f"{key}: {totals[key]:,}")
    for key in ("ohlc_high_violations", "ohlc_low_violations"):
        if totals[key]:
            warnings.append(f"{key}: {totals[key]:,}")
    if first_date is not None and (first_date.year != year or last_date.year != year):
        errors.append(f"dates outside {year}: {first_date.date()} to {last_date.date()}")
    return {
        "year": year, "path": str(path),
        "status": "error" if errors else "warning" if warnings else "pass",
        "expected_rows": expected_rows,
        "first_date": first_date.date().isoformat() if first_date is not None else None,
        "last_date": last_date.date().isoformat() if last_date is not None else None,
        **totals, "errors": "; ".join(errors), "warnings": "; ".join(warnings),
    }


def audit_crsp_history(
    manifest_path: str | Path,
    delistings_path: str | Path,
    seed_path: str | Path,
    batch_size: int = 250_000,
    progress=None,
) -> tuple[dict, pd.DataFrame]:
    """Audit all manifest partitions plus delisting and pre-period seed files."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows, errors, warnings = [], [], []
    partitions = manifest.get("partitions", [])
    for index, partition in enumerate(partitions, start=1):
        path = Path(partition["path"])
        if not path.exists():
            result = {
                "year": partition["year"], "path": str(path), "status": "error",
                "expected_rows": partition.get("rows"), "rows": 0,
                "errors": "partition file is missing",
            }
        else:
            result = audit_daily_partition(
                path, int(partition["year"]), partition.get("rows"), batch_size
            )
        rows.append(result)
        if result["status"] == "error":
            errors.append(f"{result['year']}: {result['errors']}")
        if result["status"] == "warning":
            warnings.append(f"{result['year']}: {result['warnings']}")
        if progress:
            progress(index, len(partitions), result)

    report = pd.DataFrame(rows)
    actual_rows = int(report.get("rows", pd.Series(dtype=int)).fillna(0).sum())
    if actual_rows != int(manifest.get("daily_rows", actual_rows)):
        errors.append(
            f"total rows {actual_rows:,} != manifest {manifest.get('daily_rows', 0):,}"
        )
    if manifest.get("status") != "complete":
        errors.append(f"manifest status is {manifest.get('status')!r}, not 'complete'")
    delistings = pd.read_parquet(delistings_path)
    seed = pd.read_parquet(seed_path)
    duplicate_delistings = int(
        delistings.duplicated(["permno", "delisting_date"]).sum()
    )
    invalid_delisting_returns = int(
        (delistings["delisting_return"].dropna() < -1).sum()
    )
    duplicate_seed_permnos = int(seed["permno"].duplicated().sum())
    invalid_seed_highs = int((seed["prior_comparable_high"].dropna() <= 0).sum())
    checks = [
        (duplicate_delistings, "duplicate delistings"),
        (invalid_delisting_returns, "delisting returns below -100%"),
        (duplicate_seed_permnos, "duplicate seed PERMNOs"),
        (invalid_seed_highs, "nonpositive ATH seed highs"),
    ]
    errors.extend(f"{label}: {count:,}" for count, label in checks if count)
    if len(delistings) != int(manifest.get("delisting_rows", len(delistings))):
        errors.append("delisting row count differs from manifest")
    if len(seed) != int(manifest.get("ath_seed_rows", len(seed))):
        errors.append("ATH seed row count differs from manifest")
    summary = {
        "status": "error" if errors else "warning" if warnings else "pass",
        "manifest_status": manifest.get("status"),
        "partition_count": len(rows), "daily_rows": actual_rows,
        "daily_unique_permnos_manifest": manifest.get("unique_permnos"),
        "delisting_rows": len(delistings),
        "delisting_rows_manifest": manifest.get("delisting_rows"),
        "ath_seed_rows": len(seed),
        "ath_seed_rows_manifest": manifest.get("ath_seed_rows"),
        "duplicate_delistings": duplicate_delistings,
        "invalid_delisting_returns": invalid_delisting_returns,
        "duplicate_seed_permnos": duplicate_seed_permnos,
        "invalid_seed_highs": invalid_seed_highs,
        "missing_close_rows": int(report["null_close"].fillna(0).sum()),
        "missing_total_return_rows": int(report["null_total_return"].fillna(0).sum()),
        "unflagged_missing_total_return_rows": int(
            report["unflagged_null_total_return"].fillna(0).sum()
        ),
        "missing_volume_rows": int(report["null_volume"].fillna(0).sum()),
        "errors": errors,
        "warnings": warnings,
        "warning_classes": [
            {
                "category": "raw_ohlc_relation",
                "severity": "requires_review",
                "action": "preserve_raw_exclude_from_strategy",
                "count": sum(
                    int(row.get("ohlc_high_violations", 0) or 0)
                    + int(row.get("ohlc_low_violations", 0) or 0)
                    for row in rows
                ),
                "description": (
                    "Raw records are preserved. Inconsistent OHLC rows are excluded "
                    "by strategy normalization; source cause and impact are not established. "
                    "Count represents relation violations, not necessarily unique records."
                ),
            }
        ] if warnings else [],
    }
    return summary, report


def save_crsp_quality_report(
    summary: dict,
    partitions: pd.DataFrame,
    summary_path: str | Path,
    partitions_path: str | Path,
) -> None:
    """Atomically save metadata-only CRSP audit reports."""
    summary_path, partitions_path = Path(summary_path), Path(partitions_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    partitions_path.parent.mkdir(parents=True, exist_ok=True)
    summary_tmp = summary_path.with_suffix(".tmp.json")
    partitions_tmp = partitions_path.with_suffix(".tmp.csv")
    summary_tmp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    partitions.to_csv(partitions_tmp, index=False)
    summary_tmp.replace(summary_path)
    partitions_tmp.replace(partitions_path)
