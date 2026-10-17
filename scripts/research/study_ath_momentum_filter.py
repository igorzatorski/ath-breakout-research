"""One frozen momentum 12-1 entry-filter experiment on saved ATH outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.momentum_controls import lagged_momentum  # noqa: E402
from ath_breakout.research.momentum_filter import (  # noqa: E402
    VARIANTS, joint_filter_intervals, rank_momentum, variant_mask,
)
from ath_breakout.research.baseline_robustness import contributions  # noqa: E402
from audit_ath_baseline import BASE, MOM, sha256  # noqa: E402
from study_ath_signal import COLS, bounds  # noqa: E402

ROBUST = ROOT / "outputs/research/ath/ath_10_baseline_robustness_v001/20261016T200336849055Z"
STUDY = "ath_11_momentum_filter_v001"


def build_ranks(events, old_manifest, checked, out):
    expected = {i["path"]: i["sha256"] for i in old_manifest["inputs"]}
    seed = checked(ROOT / "outputs/research/ath/shared_inputs/high_seed_before_1993.parquet", expected)
    hv = np.isfinite(seed.prior_comparable_high) & seed.prior_comparable_high.gt(0)
    bound = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    prior = dict(zip(seed.loc[np.isfinite(bound), "permno"], bound[np.isfinite(bound)]))
    legacy = set(seed.loc[~hv | seed.missing_high_rows.gt(0) |
                          seed.prior_comparable_high.lt(seed.prior_comparable_close), "permno"])
    membership = checked(ROOT / "data/processed/crsp/universe_memberships.parquet", expected)
    formation = membership[["effective_date", "formation_date"]].drop_duplicates().sort_values("effective_date")
    keys = pd.MultiIndex.from_frame(membership[["effective_date", "permno"]])
    gaps, features, audit = set(), [], []
    tail = None
    for year in range(1993, 2027):
        path = ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet"
        d = checked(path, expected, columns=COLS).sort_values(["permno", "date"]).reset_index(drop=True)
        close, high, observed, bad = bounds(d)
        d["adjusted_close"], d["adjusted_high"], d["observed_bound"] = close, high, observed
        cumulative = d.groupby("permno").observed_bound.cummax().groupby(d.permno).ffill()
        d["prior_ath"] = np.fmax(cumulative.groupby(d.permno).shift(), d.permno.map(prior))
        pb = bad.groupby(d.permno).cummax().groupby(d.permno).shift(fill_value=False)
        d["history_uncertain"] = d.permno.isin(legacy) | d.permno.isin(gaps) | pb
        if year >= 1994:
            lb = pd.concat([tail, d[["permno", "date", "close", "volume", "total_return"]]], ignore_index=True)
            cal = valid_nyse_sessions(f"{year-1}-01-01", f"{year}-12-31")
            rr = lb.total_return.where(np.isfinite(lb.total_return) & lb.total_return.ge(-1))
            rets = lb.assign(rr=rr).pivot(index="date", columns="permno", values="rr").reindex(cal)
            mom = lagged_momentum(rets)
            dv = (lb.close * lb.volume).where(np.isfinite(lb.close) & lb.close.gt(0) &
                                             np.isfinite(lb.volume) & lb.volume.ge(0))
            adv = lb.assign(dv=dv).pivot(index="date", columns="permno", values="dv").reindex(cal).rolling(21, min_periods=21).mean()
            ix = pd.MultiIndex.from_frame(d[["date", "permno"]])
            d["adv21"] = adv.stack().reindex(ix).to_numpy()
            d["momentum"] = mom.stack().reindex(ix).to_numpy()
            del lb, rets, mom, adv
            dm = pd.merge_asof(pd.DataFrame({"date": sorted(d.date.unique())}), formation,
                               left_on="date", right_on="effective_date", direction="backward")
            d = d.merge(dm, on="date", how="left", validate="many_to_one")
            member = pd.MultiIndex.from_frame(d[["effective_date", "permno"]]).isin(keys)
            eligible = member & d.adv21.ge(1e7) & d.adjusted_close.notna() & d.prior_ath.notna()
            quality = ~d.history_uncertain & d.adjusted_high.notna()
            signal = d.adjusted_close.gt(d.prior_ath)
            original = events.loc[events.date.dt.year.eq(year)]
            reconstructed = d.loc[eligible & quality & signal]
            assert set(zip(original.permno, original.date)) == set(zip(reconstructed.permno, reconstructed.date))
            pool = rank_momentum(d.loc[eligible & quality, ["date", "permno", "permco", "momentum"]])
            ep = original[["event_id", "permno", "date", "momentum"]].merge(
                pool.drop(columns="permco"), on=["date", "permno"], how="left", validate="one_to_one", suffixes=("_old", ""))
            assert np.allclose(ep.momentum_old, ep.momentum, equal_nan=True, atol=1e-10, rtol=1e-10)
            ep.drop(columns="momentum_old").to_parquet(out / f"by_year/features_{year}.parquet", index=False)
            signal_dates = original.date.unique()
            pool.loc[pool.date.isin(signal_dates)].to_parquet(out / f"by_year/ranking_pool_{year}.parquet", index=False)
            day = pool.groupby("date").agg(rank_population=("permno", "size"),
                                           companies=("permco", "nunique"),
                                           momentum_q20=("momentum", lambda s: s.quantile(.2)),
                                           momentum_q40=("momentum", lambda s: s.quantile(.4)),
                                           momentum_q60=("momentum", lambda s: s.quantile(.6)),
                                           momentum_q80=("momentum", lambda s: s.quantile(.8)))
            day.to_csv(out / f"by_year/rank_context_{year}.csv")
            features.append(ep[["event_id", "momentum_percentile", "quintile", "rank_population"]])
            audit.append(dict(year=year, signals=len(original), ranked=int(ep.quintile.notna().sum()),
                              pool_rows=len(pool), pool_dates=pool.date.nunique()))
            print(f"Ranking {year}: {len(original)} signals, {ep.quintile.notna().sum()} ranked", flush=True)
        _, _, observed_now, bad_now = bounds(d)
        for p, h in pd.Series(observed_now, index=d.index).groupby(d.permno).max().dropna().items():
            prior[p] = max(prior.get(p, h), h)
        gaps.update(d.loc[bad_now, "permno"].unique())
        tail = d[["permno", "date", "close", "volume", "total_return"]].copy()
    pd.DataFrame(audit).to_csv(out / "rank_coverage_by_year.csv", index=False)
    return pd.concat(features, ignore_index=True)


def describe(f, metric, sample, variant, period, denominator):
    c = contributions(f, metric, "permco") if len(f) else pd.DataFrame()
    return dict(sample=sample, variant=variant, period=period, metric=metric,
                events=len(f), securities=f.permno.nunique(), companies=f.permco.nunique(),
                retained_fraction=len(f)/denominator if denominator else np.nan,
                stock=f.stock_return.mean(), spy=f.spy_return.mean(), excess=f[metric].mean(),
                median_excess=f[metric].median(), median_stock=f.stock_return.median(),
                q05_stock=f.stock_return.quantile(.05), q95_stock=f.stock_return.quantile(.95),
                stock_loss_fraction=f.stock_return.lt(0).mean(),
                underperform_fraction=f[metric].lt(0).mean(), terminal_events=int(f.terminal_cash.sum()),
                equal_security=f.groupby("permno")[metric].mean().mean(),
                equal_company=f.groupby("permco")[metric].mean().mean(),
                equal_date=f.groupby("date")[metric].mean().mean(),
                top5_company_contribution=c.head(5).contribution.sum() if len(c) else np.nan)


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True, exist_ok=False)
    print(out, flush=True)
    inputs = {}
    manifests = {}
    for directory in [BASE, MOM, ROBUST]:
        p = directory / "manifest.json"
        manifests[directory] = json.loads(p.read_text())
        inputs[str(p.relative_to(ROOT))] = sha256(p)

    def checked(path, expected, columns=None):
        key = str(path.relative_to(ROOT))
        assert sha256(path) == expected[key], path
        inputs[key] = expected[key]
        return pd.read_parquet(path, columns=columns)

    def artifact(directory, name):
        expected = {str((directory / k).relative_to(ROOT)): v for k, v in manifests[directory]["artifacts"].items()}
        return checked(directory / name, expected)

    events = artifact(ROBUST, "events.parquet")
    old = artifact(MOM, "event_returns.parquet")
    assert events.event_id.is_unique and len(events) == 75884
    assert np.allclose(events.set_index("event_id").momentum.sort_index(),
                       old.set_index("event_id").momentum.sort_index(), equal_nan=True)
    ranks = build_ranks(events, manifests[BASE], checked, out)
    z = events.merge(ranks, on="event_id", validate="one_to_one")
    assert z.momentum.notna().equals(z.quintile.notna())
    z.to_parquet(out / "events.parquet", index=False)
    coverage = z.assign(year=z.date.dt.year, ranked=z.quintile.notna()).groupby(
        ["year", "ranked", "status"]).size().rename("events")
    coverage.to_csv(out / "coverage.csv")
    valid = z.excess_spy.notna()
    pd.DataFrame([dict(group=name, events=len(f), stock=f.stock_return.mean(),
                       spy=f.spy_return.mean(), excess_spy=f.excess_spy.mean()) for name, f in
                  [("all_annual_valid", z.loc[valid]),
                   ("ranked_annual_valid", z.loc[valid & z.quintile.notna()]),
                   ("missing_momentum_annual_valid", z.loc[valid & z.quintile.isna()])]]).to_csv(
        out / "availability.csv", index=False)
    primary = z.loc[valid & z.quintile.notna()].copy()
    primary.quintile = primary.quintile.astype(int)
    matched = primary.loc[primary.new_excess.notna()].copy()
    samples = [("annual_spy", "excess_spy", primary),
               ("annual_spy_nonoverlap", "excess_spy", primary.loc[primary.nonoverlap]),
               ("momentum_controls", "new_excess", matched),
               ("momentum_controls_nonoverlap", "new_excess", matched.loc[matched.nonoverlap])]
    summary, years, intervals = [], [], []
    periods = [("all", "1994-01-01", "2026-06-30"), ("1994_2009", "1994-01-01", "2009-12-31"),
               ("2010_2017", "2010-01-01", "2017-12-31"), ("2018_2025", "2018-01-01", "2026-06-30")]
    for sample, metric, f in samples:
        for period, lo, hi in periods:
            base = f.loc[f.date.between(lo, hi)]
            for variant in VARIANTS:
                selected = base.loc[variant_mask(base, variant)]
                summary.append(describe(selected, metric, sample, variant, period, len(base)))
        for year, base in f.groupby(f.date.dt.year):
            for variant in VARIANTS:
                selected = base.loc[variant_mask(base, variant)]
                years.append(describe(selected, metric, sample, variant, int(year), len(base)))
        if sample == "annual_spy":
            for variant in VARIANTS:
                contributions(f.loc[variant_mask(f, variant)], metric, "permco").to_csv(
                    out / f"contributors_{variant}.csv", index=False)
        print(f"Joint bootstrap {sample}: {len(f)} events", flush=True)
        cal = valid_nyse_sessions(f.date.min(), f.date.max())
        for block in [252, 504]:
            result = joint_filter_intervals(f, metric, cal, block=block)
            intervals.extend(dict(sample=sample, metric=metric, **row) for row in result)
            pd.DataFrame(intervals).to_csv(out / "uncertainty.csv", index=False)
    pd.DataFrame(summary).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(years).to_csv(out / "by_signal_year.csv", index=False)
    config = dict(study_id=STUDY, momentum_sessions=231, skip_sessions=21,
                  horizon=252, percentile="same-date eligible observed universe mid-CDF",
                  variants=VARIANTS, bootstrap_draws=2000, seed=20261016, blocks=[252, 504],
                  nonoverlap="frozen ath_10 flags; no filter-specific reset", costs="gross",
                  retrospective=True, optimization=False)
    (out / "config.json").write_text(json.dumps(config, indent=2))
    codes = [Path(__file__), ROOT / "src/ath_breakout/research/momentum_filter.py",
             ROOT / "src/ath_breakout/research/momentum_controls.py"]
    manifest = dict(study_id=STUDY, run_id=stamp, status="completed_exploratory_filter_study",
                    config=config, events=len(z), ranked_events=int(z.quintile.notna().sum()),
                    annual_ranked_events=len(primary), matched_ranked_events=len(matched),
                    inputs=inputs, protocol_sha256=sha256(ROOT / "research/ath/ATH_MOMENTUM_FILTER_PLAN.md"),
                    code_sha256={str(p.relative_to(ROOT)): sha256(p) for p in codes},
                    limitations=["Known quality-selected history, not untouched OOS",
                                 "Related multiple comparisons; no optimal threshold established",
                                 "Approximate crossed bootstrap; control reuse not fully modeled",
                                 "No portfolio, costs, causal alpha or new momentum lookback"])
    manifest["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in out.rglob("*") if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(pd.DataFrame(summary).query("sample == 'annual_spy' and period == 'all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == "__main__":
    main()
