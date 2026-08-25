from datetime import date

import pandas as pd

from scripts import run_screener


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
