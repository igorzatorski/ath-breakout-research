import importlib.util
from pathlib import Path

import pandas as pd
import pyarrow as pa


SCRIPT = Path("scripts/maintenance/download_wrds_crsp_daily_history.py")
SPEC = importlib.util.spec_from_file_location("download_crsp_daily_history", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_yearly_bounds_include_partial_boundary_years() -> None:
    bounds = list(MODULE.yearly_bounds("2024-06-01", "2026-06-30"))

    assert bounds == [
        (pd.Timestamp("2024-06-01"), pd.Timestamp("2024-12-31")),
        (pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-31")),
        (pd.Timestamp("2026-01-01"), pd.Timestamp("2026-06-30")),
    ]


def test_parquet_schema_matches_daily_contract() -> None:
    schema = MODULE.parquet_schema()

    assert schema.names == MODULE.CRSP_DAILY_COLUMNS
    assert schema.field("permno").type == pa.int64()
    assert schema.field("date").type == pa.timestamp("ns")
    assert schema.field("close").type == pa.float64()
    assert schema.field("ticker").type == pa.string()


def test_progress_line_reports_year_completion(monkeypatch) -> None:
    monkeypatch.setattr(MODULE.time, "monotonic", lambda: 160.0)

    result = MODULE.progress_line(2, 4, 100.0)

    assert "2/4" in result
    assert "50.0%" in result
    assert "ETA 1m 00s" in result
