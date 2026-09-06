import json
import pandas as pd
from scripts.maintenance.validate_data_layer import validate


def test_gate_detects_changed_raw_partition(tmp_path):
    state = tmp_path / "data/state"
    state.mkdir(parents=True)
    raw = tmp_path / "raw.parquet"
    derived = tmp_path / "derived.parquet"
    seed = tmp_path / "seed.parquet"
    universe = tmp_path / "universe.parquet"
    spy = tmp_path / "data/processed/features/SPY.parquet"
    spy.parent.mkdir(parents=True)
    for p in (raw, derived, seed, universe, spy):
        pd.DataFrame({"value": [1]}).to_parquet(p)
    manifests = {
        "crsp_daily_history_manifest.json": {"status": "complete", "daily_rows": 1, "partitions": [{"year": 2024, "path": str(raw), "rows": 1}]},
        "crsp_strategy_history_manifest.json": {"status": "complete", "ath_seed": str(seed), "seed_mtime_ns": seed.stat().st_mtime_ns, "partitions": [{"year": 2024, "path": str(derived), "rows": 1, "source_mtime_ns": raw.stat().st_mtime_ns}]},
        "crsp_universe_history_manifest.json": {"combined_path": str(universe)},
        "crsp_quality_summary.json": {"daily_rows": 1, "errors": []},
    }
    for name, content in manifests.items():
        (state / name).write_text(json.dumps(content))
    assert validate(tmp_path) == []
    pd.DataFrame({"value": [1, 2]}).to_parquet(raw)
    errors = validate(tmp_path)
    assert any("Row count mismatch" in e for e in errors)
    assert any("source fingerprint" in e for e in errors)
