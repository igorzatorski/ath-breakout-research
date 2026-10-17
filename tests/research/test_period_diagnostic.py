import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.period_diagnostic import (
    additive_groups, mix_within_decomposition, period_change_intervals, period_labels,
)


def test_period_boundaries_and_additive_contributions():
    dates = pd.Series(pd.to_datetime(["2009-12-31", "2010-01-04", "2017-12-29", "2018-01-02"]))
    assert period_labels(dates).tolist() == ["early", "middle", "middle", "recent"]
    z = pd.DataFrame(dict(period=["early", "early", "early", "recent"],
                          cell=["a", "a", "b", "b"], value=[.1, .3, -.5, .2]))
    c = additive_groups(z, "cell", "value")
    assert c.loc[c.period.eq("early"), "contribution"].sum() == pytest.approx(-.1/3)
    assert c.loc[c.period.eq("recent"), "contribution"].sum() == pytest.approx(.2)


def test_mix_and_within_are_distinct_and_reconcile():
    # Old: equal A/B weights, means 0 and 1; new: A weight .75, means .2 and 1.2.
    z = pd.DataFrame(dict(period=["early"]*4+["recent"]*4,
                          cell=["a", "a", "b", "b", "a", "a", "a", "b"],
                          value=[0, 0, 1, 1, .2, .2, .2, 1.2]))
    d = mix_within_decomposition(z, "cell", "value")
    assert d["mix"].sum() == pytest.approx(-.25)
    assert d["within"].sum() == pytest.approx(.2)
    assert d.total_change.sum() == pytest.approx(-.05)
    assert d.one_sided_support.sum() == 0


def test_disappearing_and_new_cells_are_not_imputed_as_shared_means():
    z = pd.DataFrame(dict(period=["early", "early", "recent", "recent"],
                          cell=["shared", "old_only", "shared", "new_only"],
                          value=[.1, .5, .2, -.3]))
    d = mix_within_decomposition(z, "cell", "value").set_index("cell")
    assert d.loc["shared", "within"] == pytest.approx(.05)
    assert d.loc["old_only", "one_sided_support"] == pytest.approx(-.25)
    assert d.loc["new_only", "one_sided_support"] == pytest.approx(-.15)
    assert np.isnan(d.loc["old_only", "new_mean"])
    assert d.total_change.sum() == pytest.approx(-.35)


def test_joint_period_bootstrap_matches_explicit_resampling():
    cal = pd.bdate_range("2024-01-01", periods=30)
    rows = [(day, co, ["early", "middle", "recent"][t//10], .01*((t*co)%17), .005*t)
            for t, day in enumerate(cal) for co in [1, 2, 3]]
    z = pd.DataFrame(rows, columns=["date", "permco", "period", "stock_return", "spy_return"])
    z["excess_spy"] = z.stock_return-z.spy_return
    actual = period_change_intervals(z, cal, block=2, draws=60, seed=17)
    assert actual == period_change_intervals(z, cal, block=2, draws=60, seed=17)
    rng = np.random.default_rng(17)
    samples = []
    for _ in range(60):
        starts = rng.integers(0, 30, 15)
        dates = [(s+k)%30 for s in starts for k in range(2)]
        cw = rng.multinomial(3, np.full(3, 1/3))
        weights = np.array([dates.count(cal.get_loc(r.date))*cw[r.permco-1] for r in z.itertuples()])
        values = []
        for period in ["early", "middle", "recent"]:
            mask = z.period.eq(period)
            values.append([np.average(z.loc[mask, col], weights=weights[mask]) if weights[mask].sum() else np.nan
                           for col in ["stock_return", "spy_return", "excess_spy"]])
        samples.append(values)
    samples = np.asarray(samples)
    for row in actual:
        j = ["stock_return", "spy_return", "excess_spy"].index(row["metric"])
        if row["contrast"] == "recent_minus_early":
            values = samples[:, 2, j]-samples[:, 0, j]
        else:
            values = samples[:, ["early", "middle", "recent"].index(row["contrast"]), j]
        lo, hi = np.nanquantile(values, [.025, .975])
        assert row["lower95"] == pytest.approx(lo)
        assert row["upper95"] == pytest.approx(hi)


def test_long_calendar_period_index_does_not_overflow_int8_codes():
    cal = pd.bdate_range("2020-01-01", periods=300)
    period = np.repeat(["early", "middle", "recent"], 100)
    returns = np.repeat([.1, .2, .3], 100)
    z = pd.DataFrame(dict(date=cal, permco=1, period=period,
                          stock_return=returns, spy_return=0., excess_spy=returns))
    rows = period_change_intervals(z, cal, block=21, draws=40, seed=17)
    change = next(r for r in rows if r["metric"] == "excess_spy" and r["contrast"] == "recent_minus_early")
    assert change["estimate"] == pytest.approx(.2)
    assert change["lower95"] == pytest.approx(.2)
    assert change["upper95"] == pytest.approx(.2)
