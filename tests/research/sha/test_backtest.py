import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.sha.backtest import (
    ExecutionConfig,
    simulate_long_cash,
    summarize,
)


def prices():
    return pd.DataFrame(
        dict(
            open=[100.0, 100.0, 110.0, 120.0, 90.0],
            close=[100.0, 105.0, 115.0, 110.0, 95.0],
            dividends=[0.0, 0.0, 2.0, 3.0, 0.0],
        ),
        index=pd.date_range("2024-01-01", periods=5),
    )


def test_manual_lag_neutral_dividend_entitlement_and_exit():
    p = prices()
    s = pd.Series([1, 0, -1, -1, 1], index=p.index)
    ledger, fills, trades = simulate_long_cash(p, s, 1, ExecutionConfig(1000, 0, 0))
    # Buy 10 shares on day 1. Reinvest 20 dividend cash at day 2 open 110.
    shares = 10 + 20 / 110
    # Sell on day 3, retaining the dividend earned at the previous close.
    final = shares * (120 + 3)
    assert ledger.equity.tolist() == pytest.approx(
        [1000, 1050, shares * 115, final, final]
    )
    assert fills.reason.tolist() == ["entry", "dividend_reinvestment", "exit"]
    assert fills.signal_date.tolist() == list(p.index[:3])
    assert trades.iloc[0].holding_sessions == 2
    assert trades.iloc[0].net_return == pytest.approx(final / 1000 - 1)
    # Last-day green cannot create an execution after the data ends.
    assert ledger.units.iloc[-1] == 0


def test_all_in_costs_and_terminal_open_position():
    p = prices().assign(dividends=0.0)
    ledger, fills, trades = simulate_long_cash(
        p, pd.Series(1, index=p.index), 1, ExecutionConfig(1000, 10, 5)
    )
    expected_units = 1000 / (100 * 1.0005 * 1.001)
    assert ledger.units.iloc[-1] == pytest.approx(expected_units)
    assert ledger.cash.eq(0).iloc[1:].all()
    assert len(fills) == 1
    assert trades.status.tolist() == ["open"]
    assert ledger.equity.iloc[-1] == pytest.approx(expected_units * 95)
    assert summarize(ledger, fills, trades)["completed_trades"] == 0


def test_ex_date_entry_has_no_dividend_entitlement():
    p = prices()
    s = pd.Series([-1, 1, -1, -1, -1], index=p.index)
    ledger, _, _ = simulate_long_cash(p, s, 1, ExecutionConfig(1000, 0, 0))
    assert ledger.dividend_cash.loc[p.index[2]] == 0
    assert ledger.dividend_cash.loc[p.index[3]] == pytest.approx(1000 / 110 * 3)


def test_cash_only_and_missing_signals():
    p = prices()
    ledger, fills, trades = simulate_long_cash(p, pd.Series(np.nan, index=p.index), 1)
    assert ledger.equity.eq(100_000).all()
    assert fills.empty and trades.empty
    assert summarize(ledger, fills, trades)["sharpe_252"] is None


def test_prefix_simulation_and_independent_cash_reconciliation():
    p = prices()
    s = pd.Series([1, 0, -1, 1, -1], index=p.index)
    config = ExecutionConfig(1000, 10, 5)
    ledger, fills, _ = simulate_long_cash(p, s, 1, config)
    prefix, _, _ = simulate_long_cash(p.iloc[:3], s.iloc[:3], 1, config)
    pd.testing.assert_frame_equal(prefix, ledger.iloc[:3])
    cash = 1000.0
    units = 0.0
    for date in ledger.index[1:]:
        cash += units * p.loc[date, "dividends"]
        for fill in fills.loc[fills.date.eq(date)].itertuples():
            cash += fill.cash_flow
            units += fill.units if fill.side == "buy" else -fill.units
        assert cash == pytest.approx(ledger.loc[date, "cash"], abs=1e-9)
        assert cash + units * p.loc[date, "close"] == pytest.approx(
            ledger.loc[date, "equity"]
        )


@pytest.mark.parametrize(
    "kwargs", [{"initial_cash": 0}, {"commission_bps": -1}, {"slippage_bps": 10000}]
)
def test_bad_costs_rejected(kwargs):
    with pytest.raises(ValueError):
        ExecutionConfig(**kwargs)
