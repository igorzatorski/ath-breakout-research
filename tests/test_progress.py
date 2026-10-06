"""Validate ETA calculation and confirm progress does not alter simulation results."""
from datetime import date
import pandas as pd

from ath_breakout import progress
from ath_breakout.data.market_update import print_update_progress
from ath_breakout.screening.screener import print_screen_progress
from ath_breakout.backtesting.portfolio import run_portfolio_backtest
from tests.backtesting.test_portfolio import make_inputs


def test_eta_changes_from_unknown_to_estimated_to_complete(monkeypatch):
    monkeypatch.setattr(progress.time, "monotonic", lambda: 130.0)
    assert progress.timing_values(0, 100, 100)["eta"] == "calculating"
    assert progress.timing_values(25, 100, 100) == {"elapsed": "0m 30s", "eta": "1m 30s", "total": "2m 00s"}
    assert progress.timing_values(100, 100, 100)["eta"] == "0m 00s"
    assert progress.timing_values(0, 0, 100)["eta"] == "0m 00s"


def test_download_and_screen_display_remaining_time(monkeypatch, capsys):
    monkeypatch.setattr(progress.time, "monotonic", lambda: 130.0)
    print_update_progress(1, 4, 50, 0, started_at=100)
    print_screen_progress(25, 100, started_at=100)
    output = capsys.readouterr().out
    assert output.count("ETA:") == 2
    assert output.count("1m 30s") == 2


def test_simulation_progress_preserves_results(capsys):
    histories, candidates, benchmark = make_inputs()
    arguments = (histories, candidates, benchmark, date(2026, 1, 2), date(2026, 1, 9))
    without = run_portfolio_backtest(*arguments)
    with_progress = run_portfolio_backtest(*arguments, show_progress=True)
    pd.testing.assert_frame_equal(without.equity, with_progress.equity)
    pd.testing.assert_frame_equal(without.trades, with_progress.trades)
    output = capsys.readouterr().out
    assert "simulation" in output and "ETA:" in output and "100.00%" in output
