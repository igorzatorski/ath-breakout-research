from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from scripts.maintenance import run_historical_screener


def test_rejects_a_date_outside_iso_format() -> None:
    with pytest.raises(SystemExit):
        run_historical_screener.parse_arguments(["24-08-2026"])


def test_prompts_for_date_when_run_without_an_argument(monkeypatch) -> None:
    answers = iter(["26-08-2026", "2026-08-26"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    result = run_historical_screener.request_scan_date()

    assert result == date(2026, 8, 26)


def test_runs_and_saves_a_historical_screen(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    output_directory = tmp_path / "history"
    results = pd.DataFrame(
        {
            "setup_state": ["trend_candidate"],
            "ticker": ["AAPL"],
        }
    )
    summary = {
        "current_universe": 1,
        "scanned": 1,
        "excluded_quality_or_stale": 0,
        "historical_mode": True,
    }

    monkeypatch.setattr(
        run_historical_screener,
        "OUTPUT_DIRECTORY",
        output_directory,
    )
    monkeypatch.setattr(
        run_historical_screener,
        "resolve_completed_session",
        lambda as_of: pd.Timestamp(as_of),
    )
    monkeypatch.setattr(
        run_historical_screener,
        "run_stock_screen",
        lambda **kwargs: (results, date(2026, 8, 21), summary),
    )
    monkeypatch.setattr(
        run_historical_screener,
        "print_candidate_tables",
        lambda data: None,
    )
    monkeypatch.setattr(
        run_historical_screener,
        "CRSP_MANIFEST_PATH",
        Path("__missing_crsp_manifest_for_test__.json"),
    )

    run_historical_screener.main(["2026-08-21"])

    output = capsys.readouterr().out
    assert "Market picture at session close: 2026-08-21" in output
    assert "survivorship bias" in output
    assert (output_directory / "screener_2026-08-21.csv").exists()
