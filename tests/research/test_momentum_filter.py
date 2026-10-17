import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.momentum_filter import (
    GROUP_MATRIX, VARIANTS, grouped_means, joint_filter_intervals,
    quintiles, rank_momentum, variant_mask,
)


def test_full_cross_section_mid_ranks_and_ties_not_ath_only():
    pool = pd.DataFrame(dict(date=pd.Timestamp("2024-01-02"), permno=range(1, 6),
                             momentum=[-.2, .1, .1, .5, np.nan], ath=[False, True, False, True, True]))
    z = rank_momentum(pool).set_index("permno")
    assert z.momentum_percentile.tolist() == pytest.approx([.125, .5, .5, .875])
    assert z.rank_population.eq(4).all()
    assert z.quintile.tolist() == [1, 3, 3, 5]
    changed = pool.assign(future_return=[100, -1, .2, .3, 0])
    pd.testing.assert_frame_equal(rank_momentum(changed)[z.reset_index().columns], z.reset_index())


def test_boundaries_nested_filters_and_missing_rank_rejection():
    p = [0, .2, .20001, .4, .40001, .6, .60001, .8, .80001, 1]
    q = quintiles(p)
    assert q.tolist() == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    z = pd.DataFrame(dict(quintile=q))
    assert variant_mask(z, "top60").tolist() == [v > .4 for v in p]
    assert variant_mask(z, "top40").tolist() == [v > .6 for v in p]
    assert variant_mask(z, "top20").tolist() == [v > .8 for v in p]
    with pytest.raises(ValueError):
        quintiles([np.nan])
    with pytest.raises(ValueError):
        rank_momentum(pd.DataFrame(dict(date=[1, 1], permno=[1, 1], momentum=[0, 1])))


def test_grouped_means_are_count_weighted_not_means_of_quintile_means():
    sums = np.array([1., 2., 3., 4., 5.])
    counts = np.array([1, 2, 3, 4, 10])
    m = grouped_means(sums, counts)
    assert m[0] == pytest.approx(15 / 20)
    assert m[6] == pytest.approx(12 / 17)
    assert m[8] == pytest.approx(.5)


def test_joint_sparse_bootstrap_matches_explicit_events_and_simultaneous_band():
    cal = pd.bdate_range("2024-01-01", periods=7)
    rows = [(day, co, q, ((q * co + t * t) % 17) / 100 - .1)
            for t, day in enumerate(cal) for co in range(1, 4) for q in range(1, 6)
            if (t + co + q) % 3 != 0]
    z = pd.DataFrame(rows, columns=["date", "permco", "quintile", "excess"])
    actual = joint_filter_intervals(z, "excess", cal, block=3, draws=60, seed=17)
    assert actual == joint_filter_intervals(z, "excess", cal, block=3, draws=60, seed=17)
    rng = np.random.default_rng(17)
    means = []
    for _ in range(60):
        starts = rng.integers(0, 7, 3)
        dates = [(s+k) % 7 for s, length in zip(starts, [3, 3, 1]) for k in range(length)]
        cw = rng.multinomial(3, np.full(3, 1 / 3))
        weights = np.array([dates.count(cal.get_loc(r.date)) * cw[r.permco-1] for r in z.itertuples()])
        row = []
        for name in VARIANTS:
            mask = variant_mask(z, name)
            row.append(np.average(z.loc[mask, "excess"], weights=weights[mask]))
        means.append(row)
    means = np.array(means)
    point = GROUP_MATRIX @ np.array([z.loc[z.quintile.eq(q), "excess"].sum() for q in range(1, 6)]) / (
        GROUP_MATRIX @ np.array([int(z.quintile.eq(q).sum()) for q in range(1, 6)]))
    for row in actual:
        if row["comparison"] == "level":
            i = VARIANTS.index(row["variant"])
            lo, hi = np.quantile(means[:, i], [.025, .975])
            assert row["lower95"] == pytest.approx(lo)
            assert row["upper95"] == pytest.approx(hi)
        if row["comparison"] == "minus_baseline_simultaneous3":
            i = VARIANTS.index(row["variant"])
            p = point[6:9]-point[0]
            radius = np.quantile(np.abs(means[:, 6:9]-means[:, [0]]-p).max(axis=1), .95)
            assert row["lower95"] == pytest.approx(point[i]-point[0]-radius)
            assert row["upper95"] == pytest.approx(point[i]-point[0]+radius)
