import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.baseline_robustness import (
    contributions, crossed_intervals, nonoverlap_ids, ratio_estimates,
)


def test_company_ties_cross_year_and_skips_do_not_extend_clock():
    cal = pd.bdate_range("2023-12-01", periods=510)
    z = pd.DataFrame(dict(event_id=[0, 1, 2, 3, 4, 5], permno=[2, 1, 2, 2, 2, 3],
                          permco=[10, 10, 10, 10, 10, 20], date=cal[[0, 0, 251, 252, 503, 1]]))
    assert set(nonoverlap_ids(z.sample(frac=1, random_state=4), cal)) == {1, 3, 5}
    z["stock_return"] = [999, -1, 999, np.nan, 999, -1]
    z["status"] = "missing_entry"
    assert set(nonoverlap_ids(z, cal)) == {1, 3, 5}
    assert set(nonoverlap_ids(z.loc[z.date <= cal[251]], cal)) == {1, 5}


def test_rejects_missing_company_duplicate_identity_and_bad_calendar():
    z = pd.DataFrame(dict(event_id=[1], permno=[1], permco=[np.nan], date=[pd.Timestamp("2024-01-02")]))
    with pytest.raises(ValueError):
        nonoverlap_ids(z, z.date)
    z.permco = 1
    with pytest.raises(ValueError):
        nonoverlap_ids(pd.concat([z, z]), z.date)
    with pytest.raises(ValueError):
        nonoverlap_ids(z, pd.to_datetime(["2024-01-03"]))


def test_contributions_include_losses_and_reconcile_with_event_mean():
    z = pd.DataFrame(dict(permco=[1, 1, 2, 3], excess=[.1, .3, -.5, np.nan]))
    c = contributions(z, "excess", "permco").set_index("permco")
    assert c.loc[1, "contribution"] == pytest.approx(.4 / 3)
    assert c.loc[2, "contribution"] == pytest.approx(-.5 / 3)
    assert c.contribution.sum() == pytest.approx(z.excess.mean())
    assert c.positive_sum.sum() == pytest.approx(.4)
    assert c.negative_sum.sum() == pytest.approx(-.5)


def test_shared_weight_arithmetic_and_bootstrap_constant_values():
    values = np.array([.1, -.2, .3])
    retained = np.array([1, 0, 1])
    weights = np.array([2, 4, 1])
    result = ratio_estimates(values, retained, weights)
    assert result == pytest.approx([-.3 / 7, .5 / 3, .5 / 3 + .3 / 7])
    cal = pd.bdate_range("2024-01-01", periods=30)
    z = pd.DataFrame(dict(date=cal, permco=np.tile([1, 2, 3], 10), excess=.02, nonoverlap=True))
    a = crossed_intervals(z, "excess", cal, block=7, draws=40)
    assert a == crossed_intervals(z, "excess", cal, block=7, draws=40)
    for row in a:
        expected = 0 if row["variant"] == "change" else .02
        assert row["estimate"] == pytest.approx(expected)
        assert row["lower95"] == pytest.approx(expected)
        assert row["upper95"] == pytest.approx(expected)


def test_one_company_crossed_resampling_matches_date_only():
    cal = pd.bdate_range("2024-01-01", periods=30)
    z = pd.DataFrame(dict(date=cal, permco=1, excess=np.arange(30) / 100, nonoverlap=True))
    rows = crossed_intervals(z, "excess", cal, block=7, draws=40)
    for a, b in zip(rows[:3], rows[3:]):
        assert a["lower95"] == pytest.approx(b["lower95"])
        assert a["upper95"] == pytest.approx(b["upper95"])


def test_sparse_crossed_bootstrap_matches_explicit_event_resampling():
    cal = pd.bdate_range("2024-01-01", periods=7)
    z = pd.DataFrame(dict(date=np.repeat(cal, 3), permco=np.tile([1, 2, 3], 7),
                          excess=np.arange(21) / 100 - .1,
                          nonoverlap=np.tile([True, False, True], 7)))
    actual = crossed_intervals(z, "excess", cal, block=3, draws=80, seed=17)
    rng = np.random.default_rng(17)
    results = {"date_blocks": [], "company_x_date_blocks": []}
    for _ in range(80):
        starts = rng.integers(0, 7, 3)
        expanded = [(start + k) % 7 for start, length in zip(starts, [3, 3, 1])
                    for k in range(length)]
        cw = rng.multinomial(3, np.full(3, 1 / 3))
        tw = np.array([expanded.count(i) for i in range(7)])
        for method, weights in [("date_blocks", np.repeat(tw, 3)),
                                ("company_x_date_blocks", np.repeat(tw, 3) * np.tile(cw, 7))]:
            if weights.sum() and weights[z.nonoverlap].sum():
                results[method].append(ratio_estimates(z.excess.to_numpy(),
                                                       z.nonoverlap.to_numpy(), weights))
    for row in actual:
        col = ["baseline", "nonoverlap", "change"].index(row["variant"])
        bounds = np.quantile(results[row["method"]], [.025, .975], axis=0)
        assert row["lower95"] == pytest.approx(bounds[0, col])
        assert row["upper95"] == pytest.approx(bounds[1, col])
