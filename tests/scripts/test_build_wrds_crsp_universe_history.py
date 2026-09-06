import importlib.util
from pathlib import Path

import pandas as pd
import pytest


SCRIPT = Path("scripts/maintenance/build_wrds_crsp_universe_history.py")
SPEC = importlib.util.spec_from_file_location("build_crsp_universe_history", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_yearly_bounds_include_lookback_and_partial_final_year() -> None:
    bounds = list(MODULE.yearly_bounds(2025, "2026-06-30"))

    assert len(bounds) == 2
    assert bounds[0][0] == pd.Timestamp("2024-09-23")
    assert bounds[0][1] == pd.Timestamp("2025-01-01")
    assert bounds[0][2] == pd.Timestamp("2025-12-31")
    assert bounds[1][2] == pd.Timestamp("2026-06-30")


def test_yearly_bounds_reject_reversed_range() -> None:
    with pytest.raises(ValueError, match="Start year cannot follow"):
        list(MODULE.yearly_bounds(2027, "2026-06-30"))


def test_progress_line_reports_completion_and_eta(monkeypatch) -> None:
    monkeypatch.setattr(MODULE.time, "monotonic", lambda: 160.0)

    result = MODULE.progress_line(completed=2, total=4, started_at=100.0)

    assert "2/4" in result
    assert "50.0%" in result
    assert "elapsed 1m 00s" in result
    assert "ETA 1m 00s" in result
