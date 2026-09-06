"""Independent arithmetic checks: portfolio wealth, not implementation details."""
import pandas as pd
import pytest

from tests.backtesting.test_portfolio import DATES, make_inputs
from ath_breakout.backtesting.portfolio import run_portfolio_backtest


def run_case(closes, returns, exit_day=None, dividend=0.0, benchmark_start=0,
             delistings=None):
    histories, candidates, benchmark = make_inputs()
    history = histories["A"].copy()
    history["close"] = closes
    history["split_adj_close"] = closes
    history["split_adj_open"] = closes
    history["total_return"] = returns
    history["sma_150"] = 1.0
    if exit_day is not None:
        history.loc[DATES[exit_day - 1], "sma_150"] = 1000.0
        history.loc[DATES[exit_day], "dividends"] = dividend
    candidates = candidates[candidates.security_id == "A"].copy()
    candidates["security_id"] = "1"
    return run_portfolio_backtest(
        {"1": history}, candidates, benchmark.iloc[benchmark_start:],
        DATES[0].date(), DATES[-1].date(), target_position_weight=1.0,
        maximum_positions=1, transaction_cost_bps=0,
        return_mode="crsp_total_return", delistings=delistings)


@pytest.mark.parametrize("price,ret,wealth", [(110, .1, 110000),
                         (90, -.1, 90000), (110, .12, 112000), (100, 0, 100000)])
def test_total_return_is_applied_exactly_once(price, ret, wealth):
    result = run_case([100, 100, price, price, price, price], [0, 0, ret, 0, 0, 0])
    assert result.summary["final_equity"] == pytest.approx(wealth)


def test_exit_at_open_keeps_ex_date_distribution_without_future_return():
    result = run_case([100, 100, 98, 98, 98, 98], [0, 0, .8, 0, 0, 0],
                      exit_day=2, dividend=2)
    assert result.summary["final_equity"] == pytest.approx(100000)
    assert result.trades.iloc[0].dividends_received == pytest.approx(2000)


def test_calendar_does_not_depend_on_benchmark_start():
    result = run_case([100] * 6, [0] * 6, benchmark_start=3)
    assert result.equity.iloc[0].date == DATES[0]
    assert result.events.iloc[0].date == DATES[1]
    assert result.equity.iloc[:3].benchmark_equity.isna().all()
    assert pd.isna(result.summary["benchmark_cagr"])


def test_terminal_return_replaces_daily_terminal_row_not_multiplies_twice():
    outcomes = pd.DataFrame({"permno": [1], "daily_return_date": [DATES[3]],
                             "delisting_return": [-.5]})
    result = run_case([100, 100, 110, 55, 55, 55], [0, 0, .1, -.5, 0, 0],
                      delistings=outcomes)
    assert result.summary["final_equity"] == pytest.approx(55000)
    assert result.summary["delisting_exits"] == 1


def test_missing_held_terminal_return_stops_instead_of_inventing_proceeds():
    outcomes = pd.DataFrame({"permno": [1], "daily_return_date": [DATES[3]],
                             "delisting_return": [float("nan")]})
    with pytest.raises(ValueError, match="Missing terminal return"):
        run_case([100] * 6, [0] * 6, delistings=outcomes)


def test_future_return_does_not_change_previous_equity():
    baseline = run_case([100] * 6, [0] * 6)
    changed = run_case([100, 100, 100, 100, 100, 120], [0, 0, 0, 0, 0, .2])
    pd.testing.assert_frame_equal(baseline.equity.iloc[:-1], changed.equity.iloc[:-1])


def test_missing_return_fallback_is_counted():
    result = run_case([100, 100, 110, 110, 110, 110], [0, 0, None, 0, 0, 0])
    assert result.summary["final_equity"] == pytest.approx(110000)
    assert result.summary["return_fallback_sessions"] == 1
