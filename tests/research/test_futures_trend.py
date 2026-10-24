import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.trend_following_futures.model import (
    Config,
    simulate,
    spy_benchmark,
    targets,
)


def sample(n=700):
    rng = np.random.default_rng(812)
    dates = pd.bdate_range("2018-01-01", periods=n)
    changes = rng.normal([0.08, -0.08], [1.0, 0.8], size=(n, 2))
    prices = pd.DataFrame(
        100 + np.cumsum(changes, axis=0), index=dates, columns=["a", "b"]
    )
    rolls = prices * 0
    rolls.iloc[300, 0] = 1
    return prices, rolls


def test_hand_long_short_mark_to_market_and_two_roll_legs():
    prices, rolls = sample()
    ledger, q, decisions, pnl, costs = simulate(
        prices, prices, rolls, [10.0, 20.0], [2.0, 3.0], ["x", "y"]
    )
    changes = prices.diff().loc[ledger.index] * [10.0, 20.0]
    held = q.shift().fillna(0)
    np.testing.assert_allclose(pnl, held * changes)
    expected_trade_cost = q.diff().fillna(0).abs() * [2.0, 3.0]
    expected_roll_cost = 2 * held.abs() * rolls.loc[q.index] * [2.0, 3.0]
    np.testing.assert_allclose(
        costs, expected_trade_cost + expected_roll_cost, atol=1e-8
    )
    assert q.min().min() < 0
    assert q.max().max() > 0
    assert ledger.equity.iloc[0] == 10_000_000
    first = decisions.iloc[0]
    assert q.loc[first.signal_date].eq(0).all()
    assert q.loc[first.execution_date].abs().sum() > 0
    assert pnl.loc[first.execution_date].eq(0).all()


def test_prefix_and_future_additive_adjustment_invariance():
    prices, rolls = sample()
    full = simulate(prices, prices, rolls, [10.0, 20.0], [2.0, 3.0], ["x", "y"])
    cut = 500
    prefix = simulate(
        prices.iloc[:cut],
        prices.iloc[:cut],
        rolls.iloc[:cut],
        [10.0, 20.0],
        [2.0, 3.0],
        ["x", "y"],
    )
    pd.testing.assert_frame_equal(prefix[0], full[0].loc[: prices.index[cut - 1]])
    shifted = simulate(
        prices + 1000, prices, rolls, [10.0, 20.0], [2.0, 3.0], ["x", "y"]
    )
    np.testing.assert_allclose(shifted[0].equity, full[0].equity, rtol=1e-10)
    changed = prices.copy()
    changed.iloc[cut:] *= 10
    future = simulate(changed, changed, rolls, [10.0, 20.0], [2.0, 3.0], ["x", "y"])
    np.testing.assert_allclose(
        future[0].loc[: prices.index[cut - 1]].equity, prefix[0].equity
    )


def test_negative_prices_and_risk_caps():
    prices, rolls = sample()
    negative = prices - 150
    ledger, q, *_ = simulate(
        negative, negative, rolls, [10.0, 20.0], [2.0, 3.0], ["x", "y"]
    )
    assert np.isfinite(ledger.equity).all()
    changes = prices.diff().tail(60) * [10.0, 20.0]
    config = Config(
        market_notional_cap=0.01, class_notional_cap=0.015, gross_notional_cap=0.02
    )
    units, vol = targets(
        changes,
        np.array([-1000.0, 2000.0]),
        np.array([1000.0, 2000.0]),
        [1, -1],
        ["x", "x"],
        100_000,
        config,
    )
    gross = np.abs(units) * [1000, 2000]
    assert (gross <= 1000 + 1e-8).all()
    assert gross.sum() <= 1500 + 1e-8
    assert vol <= 0.10 + 1e-10


def test_spy_self_financing_and_delayed_initial_purchase():
    prices, _ = sample()
    series = prices.a
    anchor = series.index[300]
    ledger = spy_benchmark(series, anchor, 1000)
    units = 1000 / (series.loc[ledger.index[1]] * 1.0001)
    assert ledger.equity.iloc[0] == 1000
    assert ledger.total_return_units.iloc[0] == 0
    assert ledger.total_return_units.iloc[-1] == pytest.approx(units)
    assert ledger.equity.iloc[-1] == pytest.approx(units * series.iloc[-1])
    targeted = spy_benchmark(series, anchor, 1000, target_volatility=0.10)
    assert targeted.cash.min() > -1e-8
    assert targeted.cash.max() > 0


def test_margin_proxy_reduction_is_delayed_and_not_an_instant_fill():
    prices, rolls = sample()
    cfg = Config(margin_proxy_limit=0.01, margin_proxy_reduction=0.005)
    ledger, positions, decisions, *_ = simulate(
        prices, prices, rolls, [10.0, 20.0], [2.0, 3.0], ["x", "y"], cfg
    )
    event = decisions.loc[decisions.reason.eq("margin_proxy_reduction")].iloc[0]
    assert event.execution_date > event.signal_date
    expected = (
        positions.loc[event.signal_date]
        * cfg.margin_proxy_reduction
        / ledger.loc[event.signal_date, "margin_proxy_ratio"]
    )
    np.testing.assert_allclose(positions.loc[event.execution_date], expected)
