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


def test_prints_compact_terminal_statistics_without_ascii_charts(capsys) -> None:
    result, _ = make_result()
    print_portfolio_report(result.equity, result.trades, result.summary)

    output = capsys.readouterr().out
    assert "EQUITY CURVE:" not in output
    assert "DRAWDOWN CURVE" not in output
    assert "CAPITAL EXPOSURE" not in output
    assert "STRATEGY VS S&P 500" in output
    assert "Metric" in output
    assert "Difference" in output
    assert "RELATIVE PERFORMANCE" in output
    assert "Alpha 95% HAC confidence interval" in output
    assert "ANNUAL PERFORMANCE" in output
    assert "FIVE WORST AND FIVE BEST DAILY RETURNS" in output
    assert "LATEST COMPLETED TRADES" in output


def test_saves_interactive_dashboard_and_tables(tmp_path: Path) -> None:
    result, candidates = make_result()
    files = save_portfolio_report(
        result.equity, result.trades, result.events, candidates,
        result.summary, tmp_path, open_dashboard=False,
    )

    assert all(path.exists() for path in files.values())
    dashboard = files["dashboard"].read_text(encoding="utf-8").lower()
    assert "plotly" in dashboard
    assert "drawdown comparison" in dashboard
    assert "calendar-year returns" in dashboard
    assert "rolling 21-session annualized volatility" in dashboard
    assert "monthly returns" in dashboard
    assert "daily returns" not in dashboard
    assert "daily pnl" not in dashboard
    assert '"color":"#2855d9"' in dashboard
    assert '"ticktext":["-25%","-20%","-15%","-10%","-5%","0%"]' in dashboard
    assert "annual_performance.csv" in str(files["annual"])
