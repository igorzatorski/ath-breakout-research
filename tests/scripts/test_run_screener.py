from datetime import date

import pandas as pd
import pytest

from scripts import run_screener


@pytest.fixture(autouse=True)
def no_network_refresh(monkeypatch):
    monkeypatch.setattr(run_screener.subprocess, "run", lambda *args, **kwargs: None)


def test_main_handles_an_empty_screen_without_crashing(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    output_directory = tmp_path / "screening"
    summary = {
        "current_universe": 10,
        "scanned": 0,
        "excluded_quality_or_stale": 10,
    }

    monkeypatch.setattr(run_screener, "OUTPUT_DIRECTORY", output_directory)
    monkeypatch.setattr(
        run_screener,
        "run_stock_screen",
        lambda **kwargs: (pd.DataFrame(), date(2026, 8, 21), summary),
    )
    monkeypatch.setattr(
        run_screener,
        "latest_completed_nyse_session",
        lambda: pd.Timestamp("2026-08-21"),
    )

    run_screener.main()

    output = capsys.readouterr().out
    assert "Fresh breakouts: 0" in output
    assert "No breakout or base-ready candidates" in output
    assert (output_directory / "screener_2026-08-21.csv").exists()


def test_live_screen_refuses_stale_results(tmp_path, monkeypatch):
    monkeypatch.setattr(run_screener, "OUTPUT_DIRECTORY", tmp_path)
    monkeypatch.setattr(run_screener, "run_stock_screen",
                        lambda **kwargs: (pd.DataFrame(), date(2026, 8, 21), {}))
    monkeypatch.setattr(run_screener, "latest_completed_nyse_session",
                        lambda: pd.Timestamp("2026-08-24"))
    with pytest.raises(RuntimeError, match="Live screener requires"):
        run_screener.main()
    assert not list(tmp_path.glob("*.csv"))


def test_as_of_routes_to_historical_screener(monkeypatch):
    called = []
    monkeypatch.setattr("scripts.maintenance.run_historical_screener.main",
                        lambda args: called.append(args))
    run_screener.main(["--as-of", "2024-01-02"])
    assert called == [["2024-01-02"]]


def test_prompts_for_date_and_routes_historical_screen(monkeypatch):
    called = []
    monkeypatch.setattr("builtins.input", lambda prompt: "2024-01-02")
    monkeypatch.setattr("scripts.maintenance.run_historical_screener.main",
                        lambda args: called.append(args))
    run_screener.main([])
    assert called == [["2024-01-02"]]
