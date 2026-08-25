from pathlib import Path

from ath_breakout.backtesting.portfolio import run_portfolio_backtest
from ath_breakout.backtesting.reporting import print_portfolio_report
from ath_breakout.backtesting.reporting import save_portfolio_report
from tests.backtesting.test_portfolio import make_inputs


def make_result():
    histories, candidates, benchmark = make_inputs()
    result = run_portfolio_backtest(
        histories, candidates, benchmark,
        benchmark.iloc[0]["date"].date(), benchmark.iloc[-1]["date"].date(),
        target_position_weight=0.4, maximum_positions=2,
    )
    return result, candidates


def test_prints_terminal_charts_and_statistics(capsys) -> None:
    result, _ = make_result()
    print_portfolio_report(result.equity, result.trades, result.summary)

    output = capsys.readouterr().out
    assert "EQUITY CURVE: STRATEGY (S) VS S&P 500 (B)" in output
    assert "DRAWDOWN CURVE" in output
    assert "CAPITAL EXPOSURE" in output
    assert "PERFORMANCE STATISTICS" in output
    assert "LATEST COMPLETED TRADES" in output


def test_saves_interactive_dashboard_and_tables(tmp_path: Path) -> None:
    result, candidates = make_result()
    files = save_portfolio_report(
        result.equity, result.trades, result.events, candidates,
        result.summary, tmp_path, open_dashboard=False,
    )

    assert all(path.exists() for path in files.values())
    assert "plotly" in files["dashboard"].read_text(encoding="utf-8").lower()
