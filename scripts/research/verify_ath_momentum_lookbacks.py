"""Independent ranks, raw momentum products and same-event comparison checks."""
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
from compare_ath_momentum_lookbacks import PREVIOUS  # noqa: E402

WINDOWS = {"12_1": 252, "6_1": 126, "3_1": 63}


def subset(z, label, variant):
    if variant == "baseline":
        return z
    if variant.startswith("Q"):
        return z.loc[z[f"quintile_{label}"].eq(int(variant[1:]))]
    return z.loc[z[f"momentum_percentile_{label}"] > {"top60": .4, "top40": .6, "top20": .8}[variant]]


def main(out):
    manifest = json.loads((out / "manifest.json").read_text())
    for name, digest in manifest["artifacts"].items():
        assert sha256(out / name) == digest
    z = pd.read_parquet(out / "events.parquet")
    old = pd.read_parquet(PREVIOUS / "events.parquet").set_index("event_id").loc[z.event_id]
    for col in ["stock_return", "spy_return", "excess_spy", "new_excess", "momentum", "quintile", "momentum_percentile"]:
        assert np.allclose(z[col], old[col], equal_nan=True, atol=1e-12)
    assert np.array_equal(z.nonoverlap, old.nonoverlap)
    common = z[[f"quintile_{label}" for label in WINDOWS]].notna().all(axis=1)
    assert common.equals(z.common_momentum)
    assert common.equals(z.quintile.notna())
    rank_checks, products, max_error = 0, 0, 0.
    for year in range(1994, 2027):
        for label, lookback in WINDOWS.items():
            events = z.loc[z.date.dt.year.eq(year) & z[f"quintile_{label}"].notna()]
            pool = pd.read_parquet(out / f"by_year/ranking_pool_{label}_{year}.parquet")
            pools = dict(tuple(pool.groupby("date")))
            for date, group in events.groupby("date"):
                values = np.sort(pools[date].momentum.to_numpy())
                for row in group.to_dict("records"):
                    value = row[f"momentum_{label}"]
                    rank = (np.searchsorted(values, value, "left") + np.searchsorted(values, value, "right"))/(2*len(values))
                    assert math.isclose(rank, row[f"momentum_percentile_{label}"], abs_tol=1e-12)
                    assert row[f"rank_population_{label}"] == len(values)
                    assert row[f"quintile_{label}"] == 1+sum(rank > b for b in [.2, .4, .6, .8])
                    rank_checks += 1
            if events.empty:
                continue
            sample = events.iloc[np.linspace(0, len(events)-1, min(3, len(events)), dtype=int)]
            raw = pd.concat([pd.read_parquet(ROOT / f"data/raw/crsp/daily_by_year/daily_{y}.parquet",
                                            columns=["permno", "date", "total_return"],
                                            filters=[("permno", "in", sample.permno.tolist())]) for y in [year-1, year]])
            raw = raw.set_index(["permno", "date"])
            cal = valid_nyse_sessions(f"{year-1}-01-01", f"{year}-12-31")
            for row in sample.to_dict("records"):
                pos = cal.get_loc(row["date"])
                dates = cal[pos-lookback+1:pos-20]
                returns = raw.loc[row["permno"]].total_return.reindex(dates).to_numpy()
                assert len(returns) == lookback-21 and np.isfinite(returns).all() and (returns >= -1).all()
                wealth = 1.
                for r in returns:
                    wealth *= 1+float(r)
                err = abs(wealth-1-row[f"momentum_{label}"])
                assert err < 1e-9
                max_error = max(max_error, err)
                products += 1
        print(f"Verified ranks and momentum: {year}", flush=True)
    summary_checks = 0
    for name in ["summary.csv", "by_signal_year.csv"]:
        table = pd.read_csv(out / name)
        for row in table.itertuples():
            f = z.loc[z.excess_spy.notna()]
            if row.sample.startswith("common"):
                f = f.loc[f.common_momentum]
            else:
                f = f.loc[f[f"quintile_{row.lookback}"].notna()]
            if "controls12" in row.sample:
                f = f.loc[f.new_excess.notna()]
            if "nonoverlap" in row.sample:
                f = f.loc[f.nonoverlap]
            p = str(row.period)
            if name == "by_signal_year.csv":
                f = f.loc[f.date.dt.year.eq(int(p))]
            elif p != "all":
                lo, hi = {"1994_2009": (1994, 2009), "2010_2017": (2010, 2017), "2018_2025": (2018, 2026)}[p]
                f = f.loc[f.date.dt.year.between(lo, hi)]
            f = subset(f, row.lookback, row.variant)
            assert len(f) == row.events
            if len(f):
                assert math.isclose(math.fsum(f[row.metric])/len(f), row.excess, abs_tol=1e-12)
                assert math.isclose(math.fsum(f.stock_return)/len(f), row.stock, abs_tol=1e-12)
                assert math.isclose(math.fsum(f.spy_return)/len(f), row.spy, abs_tol=1e-12)
            summary_checks += 1
    common_annual = z.loc[z.excess_spy.notna() & z.common_momentum]
    assert len(common_annual) == 65650
    for label in WINDOWS:
        for variant in ["baseline", "Q1", "Q2", "Q3", "Q4", "Q5", "top60", "top40", "top20"]:
            f = subset(common_annual, label, variant)
            c = pd.read_csv(out / f"contributors_{label}_{variant}.csv")
            assert c.events.sum() == len(f)
            assert math.isclose(c.contribution.sum(), f.excess_spy.mean(), abs_tol=1e-12)
    result = dict(status="passed", rank_checks=rank_checks, raw_momentum_products=products,
                  max_raw_momentum_error=max_error, summary_rows_verified=summary_checks,
                  source_12_1_returns_ranks_and_nonoverlap_preserved=True,
                  common_annual_events=len(common_annual), manifest_sha256=sha256(out / "manifest.json"),
                  verifier_sha256=sha256(Path(__file__)),
                  scope="All saved ranks/summary means and sampled raw products; not provider truth, untouched OOS or bootstrap calibration")
    (out / "independent_verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
