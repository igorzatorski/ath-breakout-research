"""Independent ranking, raw momentum and saved filter-summary verification."""
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402


def select(z, variant):
    if variant == "baseline":
        return z
    if variant.startswith("Q"):
        return z.loc[z.quintile == int(variant[1:])]
    return z.loc[z.momentum_percentile > {"top60": .4, "top40": .6, "top20": .8}[variant]]


def main(out):
    m = json.loads((out / "manifest.json").read_text())
    for name, digest in m["artifacts"].items():
        assert sha256(out / name) == digest
    z = pd.read_parquet(out / "events.parquet")
    oldpath = ROOT / "outputs/research/ath/ath_10_baseline_robustness_v001/20261016T200336849055Z/events.parquet"
    old = pd.read_parquet(oldpath).set_index("event_id").loc[z.event_id]
    assert np.array_equal(z.nonoverlap, old.nonoverlap)
    for column in ["stock_return", "spy_return", "excess_spy", "new_excess", "momentum"]:
        assert np.allclose(z[column], old[column], equal_nan=True, atol=1e-12)
    rank_checks, raw_checks, max_mom_error = 0, 0, 0.
    for year in range(1994, 2027):
        pool = pd.read_parquet(out / f"by_year/ranking_pool_{year}.parquet")
        events = z.loc[z.date.dt.year.eq(year) & z.quintile.notna()]
        pools = dict(tuple(pool.groupby("date")))
        for date, f in events.groupby("date"):
            day = pools[date]
            values = np.sort(day.momentum.to_numpy())
            for row in f.itertuples():
                left = int(np.searchsorted(values, row.momentum, side="left"))
                right = int(np.searchsorted(values, row.momentum, side="right"))
                expected = (left + right) / (2 * len(values))
                assert row.rank_population == len(values)
                assert math.isclose(row.momentum_percentile, expected, abs_tol=1e-12)
                q = 1 + sum(expected > b for b in [.2, .4, .6, .8])
                assert row.quintile == q
                rank_checks += 1
        if len(events) == 0:
            continue
        sample = events.iloc[np.linspace(0, len(events)-1, min(3, len(events)), dtype=int)]
        selected = sample.permno.tolist()
        raw = pd.concat([pd.read_parquet(ROOT / f"data/raw/crsp/daily_by_year/daily_{y}.parquet",
                                        columns=["date", "permno", "total_return"],
                                        filters=[("permno", "in", selected)]) for y in [year-1, year]])
        raw = raw.set_index(["permno", "date"])
        cal = valid_nyse_sessions(f"{year-1}-01-01", f"{year}-12-31")
        for row in sample.itertuples():
            pos = cal.get_loc(row.date)
            dates = cal[pos-251:pos-20]
            assert len(dates) == 231
            returns = raw.loc[row.permno].total_return.reindex(dates).to_numpy()
            assert np.isfinite(returns).all() and (returns >= -1).all()
            wealth = 1.
            for value in returns:
                wealth *= 1 + float(value)
            err = abs(wealth - 1 - row.momentum)
            assert err < 1e-9
            max_mom_error = max(max_mom_error, err)
            raw_checks += 1
    assert rank_checks == m["ranked_events"]
    valid = z.excess_spy.notna() & z.quintile.notna()
    base = z.loc[valid]
    matched = base.loc[base.new_excess.notna()]
    samples = {"annual_spy": base, "annual_spy_nonoverlap": base.loc[base.nonoverlap],
               "momentum_controls": matched, "momentum_controls_nonoverlap": matched.loc[matched.nonoverlap]}
    counts = 0
    for filename in ["summary.csv", "by_signal_year.csv"]:
        summary = pd.read_csv(out / filename)
        for row in summary.itertuples():
            f = samples[row.sample]
            period = str(row.period)
            if filename == "by_signal_year.csv":
                f = f.loc[f.date.dt.year.eq(int(period))]
            elif period != "all":
                lo, hi = {"1994_2009": (1994, 2009), "2010_2017": (2010, 2017), "2018_2025": (2018, 2026)}[period]
                f = f.loc[f.date.dt.year.between(lo, hi)]
            f = select(f, row.variant)
            assert len(f) == row.events
            if len(f):
                mean = math.fsum(f[row.metric]) / len(f)
                assert math.isclose(mean, row.excess, abs_tol=1e-12)
                assert math.isclose(math.fsum(f.stock_return)/len(f), row.stock, abs_tol=1e-12)
                assert math.isclose(math.fsum(f.spy_return)/len(f), row.spy, abs_tol=1e-12)
            counts += 1
    for variant in ["baseline", "Q1", "Q2", "Q3", "Q4", "Q5", "top60", "top40", "top20"]:
        f = select(base, variant)
        c = pd.read_csv(out / f"contributors_{variant}.csv")
        assert c.events.sum() == len(f)
        assert math.isclose(c.contribution.sum(), f.excess_spy.mean(), abs_tol=1e-12)
    result = dict(status="passed", all_ranked_event_checks=rank_checks,
                  raw_momentum_products=raw_checks, maximum_momentum_error=max_mom_error,
                  summary_rows_verified=counts, frozen_returns_and_nonoverlap_unchanged=True,
                  manifest_sha256=sha256(out / "manifest.json"), verifier_sha256=sha256(Path(__file__)),
                  scope="All saved ranks and summary means, sampled raw momentum, hashes; not provider truth, OOS or bootstrap calibration")
    (out / "independent_verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
