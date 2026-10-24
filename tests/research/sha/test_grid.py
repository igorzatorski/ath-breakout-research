import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.sha.backtest import (
    ExecutionConfig,
    simulate_long_cash,
    summarize,
)
from ath_breakout.research.sha.grid import build_signals, neighbor_sharpe, simulate_grid


def market():
    rng = np.random.default_rng(918)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.025, 100)))
    opening = np.r_[100, close[:-1]] * np.exp(rng.normal(0, 0.004, 100))
    return pd.DataFrame(
        dict(
            open=opening,
            close=close,
            high=np.maximum(opening, close) * 1.01,
            low=np.minimum(opening, close) * 0.99,
            dividends=np.where(np.arange(100) % 11 == 0, 0.4, 0.0),
        ),
        index=pd.bdate_range("2020-01-01", periods=100),
    )


def test_all_400_pairs_match_independent_ledger_simulator():
    prices = market()
    signals = build_signals(prices)
    assert signals.shape == (100, 400)
    assert (1, 1) in signals and (20, 20) in signals and (10, 10) in signals
    metrics, equity, exposure, trades = simulate_grid(prices, signals, 51)
    for row in metrics.itertuples():
        key = row.pre_span, row.post_span
        ledger, fills, reference_trades = simulate_long_cash(prices, signals[key], 51)
        np.testing.assert_allclose(equity[key], ledger.equity, rtol=1e-12)
        np.testing.assert_array_equal(exposure[key], ledger.exposed)
        for field, value in summarize(ledger, fills, reference_trades).items():
            actual = getattr(row, field)
            if value is None:
                assert pd.isna(actual)
            else:
                assert actual == pytest.approx(value, rel=1e-10, abs=1e-9), (key, field)
        subset = trades.loc[trades.pre_span.eq(key[0]) & trades.post_span.eq(key[1])]
        assert subset.status.tolist() == reference_trades.status.tolist()


def test_batch_neutral_missing_cash_and_prefix():
    prices = market()
    signals = pd.DataFrame(
        {(1, 1): [1, 0, np.nan, -1, 1] * 20, (2, 2): [np.nan] * 100}, index=prices.index
    )
    config = ExecutionConfig(1000, 10, 5)
    metrics, full, _, _ = simulate_grid(prices, signals, 1, config)
    _, prefix, _, _ = simulate_grid(prices.iloc[:50], signals.iloc[:50], 1, config)
    pd.testing.assert_frame_equal(prefix, full.iloc[:50])
    assert full[(2, 2)].eq(1000).all()
    assert metrics.loc[1, "completed_trades"] == 0
    assert pd.isna(metrics.loc[1, "sharpe_252"])


def test_neighbors_exclude_center_and_clip_edges():
    metrics = pd.DataFrame(
        [
            dict(pre_span=i, post_span=j, sharpe_252=i * 10 + j)
            for i in range(1, 4)
            for j in range(1, 4)
        ]
    )
    result = neighbor_sharpe(metrics)
    assert result.loc[0, "neighbor_count"] == 3
    assert result.loc[4, "neighbor_count"] == 8
    assert result.loc[0, "neighbor_worst_sharpe"] == 12
    assert result.loc[0, "neighbor_mean_sharpe"] == pytest.approx((12 + 21 + 22) / 3)
