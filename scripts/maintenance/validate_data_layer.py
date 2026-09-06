"""Validate local CRSP artifacts without downloading or altering raw data."""
import json
from pathlib import Path
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]

def validate(root=ROOT):
    errors = []
    state = root / "data/state"
    try:
        raw = json.loads((state / "crsp_daily_history_manifest.json").read_text())
        processed = json.loads((state / "crsp_strategy_history_manifest.json").read_text())
        quality_path = state / "crsp_quality_summary.json"
        quality = json.loads(quality_path.read_text())
        universe = json.loads((state / "crsp_universe_history_manifest.json").read_text())
    except (OSError, ValueError) as exc:
        return [f"Missing or invalid manifest: {exc}"]
    errors.extend(quality.get("errors", []))
    sources = {p["year"]: p for p in raw.get("partitions", [])}
    if raw.get("status") != "complete" or processed.get("status") != "complete":
        errors.append("Incomplete raw or processed build")
    if set(sources) != {p["year"] for p in processed.get("partitions", [])}:
        errors.append("Raw and processed years differ")
    for manifest in (raw, processed):
        observed_dates = []
        for item in manifest.get("partitions", []):
            path = Path(item["path"])
            try:
                metadata = pq.read_metadata(path)
                if metadata.num_rows != item["rows"]:
                    errors.append(f"Row count mismatch: {path.name}")
                if "date" not in metadata.schema.names:
                    errors.append(f"Missing date column: {path.name}")
                    continue
                date_index = metadata.schema.names.index("date")
                date_stats = [
                    metadata.row_group(index).column(date_index).statistics
                    for index in range(metadata.num_row_groups)
                ]
                date_stats = [stats for stats in date_stats if stats is not None]
                if not date_stats:
                    errors.append(f"Missing date statistics: {path.name}")
                else:
                    observed_dates.extend(
                        [min(stats.min for stats in date_stats), max(stats.max for stats in date_stats)]
                    )
                if manifest is raw and path.stat().st_mtime_ns > quality_path.stat().st_mtime_ns:
                    errors.append(f"Quality audit predates raw partition: {path.name}")
                if manifest is processed:
                    source = Path(sources[item["year"]]["path"])
                    if item.get("source_mtime_ns") != source.stat().st_mtime_ns:
                        errors.append(f"Processed partition lacks current source fingerprint: {path.name}")
            except (OSError, KeyError, ValueError) as exc:
                errors.append(f"Unreadable partition {path.name}: {exc}")
        if observed_dates:
            observed_end = max(observed_dates).date().isoformat()
            if manifest.get("end_date") and manifest["end_date"] > observed_end:
                errors.append(
                    f"{manifest.get('source_manifest', 'CRSP')} claims {manifest['end_date']} "
                    f"but partitions end at {observed_end}"
                )
    seed = Path(processed.get("ath_seed", "missing"))
    if not seed.is_file() or processed.get("seed_mtime_ns") != seed.stat().st_mtime_ns:
        errors.append("Processed ATH seed fingerprint is stale or missing")
    for path in (root / "data/processed/features/SPY.parquet", Path(universe.get("combined_path", "missing"))):
        if not path.is_file():
            errors.append(f"Missing required artifact: {path}")
    if quality.get("daily_rows") != raw.get("daily_rows"):
        errors.append("Quality audit and raw manifest row totals differ")
    return errors

def ensure_ready():
    """Repair local derived artifacts once, then refuse to run on failing gates."""
    errors = validate()
    if errors:
        import subprocess
        import sys
        for script in ("build_crsp_strategy_history.py", "audit_crsp_history_quality.py"):
            subprocess.run([sys.executable, str(ROOT / "scripts/internal" / script)], cwd=ROOT, check=True)
        errors = validate()
    if errors:
        raise RuntimeError("CRSP data validation failed: " + "; ".join(errors))


def main():
    errors = validate()
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print("PASS local CRSP partition counts, input fingerprints and audit freshness")
    return int(bool(errors))

if __name__ == "__main__":
    raise SystemExit(main())
