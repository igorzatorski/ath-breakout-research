import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.momentum_controls import lagged_momentum
from ath_breakout.research.momentum_filter import VARIANTS
from ath_breakout.research.momentum_lookbacks import (
    LOOKBACKS, joint_lookback_intervals, momentum_excluding_recent,
)


@pytest.mark.parametrize("lookback", [63, 126, 252])
def test_exact_endpoints_missing_loss_and_no_recent_or_future_data(lookback):
    rng = np.random.default_rng(17)
    raw = pd.DataFrame({"x": rng.uniform(-.05, .05, 600)})
    t = 400
    expected = np.prod(1 + raw.iloc[t-lookback+1:t-20, 0])-1
    actual = momentum_excluding_recent(raw, lookback)
    assert actual.iloc[t, 0] == pytest.approx(expected)
    assert np.isnan(actual.iloc[lookback-2, 0])
    changed = raw.copy()
    changed.iloc[t-20:] = .99
    assert momentum_excluding_recent(changed, lookback).iloc[t, 0] == pytest.approx(expected)
    for i in [t-lookback+1, t-21]:
        bad = raw.copy()
        bad.iloc[i] = np.nan
        assert np.isnan(momentum_excluding_recent(bad, lookback).iloc[t, 0])
        bad.iloc[i] = -1
        assert momentum_excluding_recent(bad, lookback).iloc[t, 0] == -1
        bad.iloc[i] = -1.1
        assert np.isnan(momentum_excluding_recent(bad, lookback).iloc[t, 0])


def test_long_definition_exactly_reproduces_frozen_function():
    rng = np.random.default_rng(11)
    raw = pd.DataFrame(rng.uniform(-.1, .1, (600, 3)))
    raw.iloc[40, 0] = np.nan
    raw.iloc[300, 1] = -1
    pd.testing.assert_frame_equal(momentum_excluding_recent(raw, 252), lagged_momentum(raw))
    with pytest.raises(ValueError):
        momentum_excluding_recent(raw, 21)


def test_joint_lookback_bootstrap_matches_explicit_event_weights():
    cal = pd.bdate_range("2024-01-01", periods=7)
    rows = [(day, co, q, ((q*co+t*t) % 17)/100-.1,
             (q+co) % 5+1, (q+t) % 5+1)
            for t, day in enumerate(cal) for co in range(1, 4) for q in range(1, 6)
            if (t+co+q) % 4 != 0]
    z = pd.DataFrame(rows, columns=["date", "permco", "quintile_12_1", "excess", "quintile_6_1", "quintile_3_1"])
    actual = joint_lookback_intervals(z, "excess", cal, block=3, draws=60, seed=17)
    assert actual == joint_lookback_intervals(z, "excess", cal, block=3, draws=60, seed=17)
    rng = np.random.default_rng(17)
    points, samples = [], []
    for label in LOOKBACKS:
        q = z[f"quintile_{label}"]
        masks = [np.ones(len(z), bool), *[q.eq(i) for i in range(1, 6)], q.ge(3), q.ge(4), q.ge(5)]
        points.append([z.loc[mask, "excess"].mean() for mask in masks])
    for _ in range(60):
        starts = rng.integers(0, 7, 3)
        expanded = [(s+k) % 7 for s, length in zip(starts, [3, 3, 1]) for k in range(length)]
        cw = rng.multinomial(3, np.full(3, 1/3))
        weights = np.array([expanded.count(cal.get_loc(r.date))*cw[r.permco-1] for r in z.itertuples()])
        means = []
        for label in LOOKBACKS:
            q = z[f"quintile_{label}"]
            masks = [np.ones(len(z), bool), *[q.eq(i) for i in range(1, 6)], q.ge(3), q.ge(4), q.ge(5)]
            means.append([np.average(z.loc[mask, "excess"], weights=weights[mask])
                          if weights[mask].sum() else np.nan for mask in masks])
        samples.append(means)
    samples, points = np.array(samples), np.array(points)
    errors = samples[:, :, 6:9]-samples[:, 0, 0][:, None, None]-(points[:, 6:9]-points[0, 0])
    radius = np.quantile(np.abs(errors[np.isfinite(errors).all(axis=(1, 2))]).max(axis=(1, 2)), .95)
    for row in actual:
        i = list(LOOKBACKS).index(row["lookback"])
        if row["comparison"] == "level":
            j = VARIANTS.index(row["variant"])
            lo, hi = np.nanquantile(samples[:, i, j], [.025, .975])
            assert row["lower95"] == pytest.approx(lo)
            assert row["upper95"] == pytest.approx(hi)
        elif row["comparison"] == "minus_baseline_simultaneous9":
            j = VARIANTS.index(row["variant"])
            p = points[i, j]-points[0, 0]
            assert row["lower95"] == pytest.approx(p-radius)
            assert row["upper95"] == pytest.approx(p+radius)
