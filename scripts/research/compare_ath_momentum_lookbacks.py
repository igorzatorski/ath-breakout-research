"""Compare exactly three predeclared momentum lookbacks on frozen ATH outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.momentum_filter import VARIANTS, rank_momentum, variant_mask  # noqa: E402
from ath_breakout.research.momentum_lookbacks import (  # noqa: E402
    LOOKBACKS, joint_lookback_intervals, momentum_excluding_recent,
)
from ath_breakout.research.baseline_robustness import contributions  # noqa: E402
from audit_ath_baseline import BASE, sha256  # noqa: E402
from study_ath_signal import COLS, bounds  # noqa: E402
from study_ath_momentum_filter import describe  # noqa: E402

PREVIOUS = ROOT / "outputs/research/ath/ath_11_momentum_filter_v001/20261016T201856779702Z"
STUDY = "ath_12_momentum_lookbacks_v001"


def build_features(events, manifest, checked, out):
    expected = {i["path"]: i["sha256"] for i in manifest["inputs"]}
    seed = checked(ROOT / "outputs/research/ath/shared_inputs/high_seed_before_1993.parquet", expected)
    hv = np.isfinite(seed.prior_comparable_high) & seed.prior_comparable_high.gt(0)
    seed_bound = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    prior = dict(zip(seed.loc[np.isfinite(seed_bound), "permno"], seed_bound[np.isfinite(seed_bound)]))
    legacy = set(seed.loc[~hv | seed.missing_high_rows.gt(0) |
                          seed.prior_comparable_high.lt(seed.prior_comparable_close), "permno"])
    membership = checked(ROOT / "data/processed/crsp/universe_memberships.parquet", expected)
    formation = membership[["effective_date", "formation_date"]].drop_duplicates().sort_values("effective_date")
    keys = pd.MultiIndex.from_frame(membership[["effective_date", "permno"]])
    gaps, results, audit = set(), [], []
    tail = None
    for year in range(1993, 2027):
        raw_path = ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet"
        d = checked(raw_path, expected, columns=COLS).sort_values(["permno", "date"]).reset_index(drop=True)
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
            dv = (lb.close*lb.volume).where(np.isfinite(lb.close) & lb.close.gt(0) &
                                           np.isfinite(lb.volume) & lb.volume.ge(0))
            adv = lb.assign(dv=dv).pivot(index="date", columns="permno", values="dv").reindex(cal).rolling(21, min_periods=21).mean()
            ix = pd.MultiIndex.from_frame(d[["date", "permno"]])
            d["adv21"] = adv.stack().reindex(ix).to_numpy()
            for label, sessions in LOOKBACKS.items():
                mom = momentum_excluding_recent(rets, sessions)
                d[f"momentum_{label}"] = mom.stack().reindex(ix).to_numpy()
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
            features = original[["event_id", "date", "permno"]].copy()
            counts = dict(year=year, signals=len(original))
            for label in LOOKBACKS:
                pool = rank_momentum(d.loc[eligible & quality,
                    ["date", "permno", "permco", f"momentum_{label}"]].rename(columns={f"momentum_{label}": "momentum"}))
                keep = pool.date.isin(original.date.unique())
                pool.loc[keep].to_parquet(out / f"by_year/ranking_pool_{label}_{year}.parquet", index=False)
                columns = ["momentum", "momentum_percentile", "quintile", "rank_population"]
                ep = original[["event_id", "date", "permno"]].merge(
                    pool.drop(columns="permco"), on=["date", "permno"], how="left", validate="one_to_one")
                ep = ep.rename(columns={c: f"{c}_{label}" for c in columns})
                if label == "12_1":
                    for c in columns:
                        assert np.allclose(ep[f"{c}_{label}"], original[c], equal_nan=True, atol=1e-10, rtol=1e-10)
                features = features.merge(ep.drop(columns=["date", "permno"]), on="event_id", validate="one_to_one")
                counts[f"ranked_{label}"] = int(ep[f"quintile_{label}"].notna().sum())
            features.to_parquet(out / f"by_year/features_{year}.parquet", index=False)
            results.append(features.drop(columns=["date", "permno"]))
            audit.append(counts)
            print(f"Ranking {year}: {counts}", flush=True)
        _, _, now, bad_now = bounds(d)
        for p, h in pd.Series(now, index=d.index).groupby(d.permno).max().dropna().items():
            prior[p] = max(prior.get(p, h), h)
        gaps.update(d.loc[bad_now, "permno"].unique())
        tail = d[["permno", "date", "close", "volume", "total_return"]].copy()
    pd.DataFrame(audit).to_csv(out / "rank_coverage_by_year.csv", index=False)
    return pd.concat(results, ignore_index=True)


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True, exist_ok=False)
    print(out, flush=True)
    inputs = {}
    bm = json.loads((BASE / "manifest.json").read_text())
    pm = json.loads((PREVIOUS / "manifest.json").read_text())
    for directory in [BASE, PREVIOUS]:
        inputs[str((directory / "manifest.json").relative_to(ROOT))] = sha256(directory / "manifest.json")

    def checked(path, expected, columns=None):
        key = str(path.relative_to(ROOT))
        assert sha256(path) == expected[key], path
        inputs[key] = expected[key]
        return pd.read_parquet(path, columns=columns)

    path = PREVIOUS / "events.parquet"
    events = checked(path, {str(path.relative_to(ROOT)): pm["artifacts"]["events.parquet"]})
    assert len(events) == 75884 and events.event_id.is_unique
    features = build_features(events, bm, checked, out)
    z = events.merge(features, on="event_id", validate="one_to_one")
    qcols = [f"quintile_{label}" for label in LOOKBACKS]
    common = z[qcols].notna().all(axis=1)
    assert common.equals(z.quintile.notna()), "Complete long window implies complete shorter windows"
    z["common_momentum"] = common
    z.to_parquet(out / "events.parquet", index=False)
    annual = z.loc[z.excess_spy.notna() & common].copy()
    assert len(annual) == 65650
    matched = annual.loc[annual.new_excess.notna()]
    samples = [("common_spy", "excess_spy", annual),
               ("common_spy_nonoverlap", "excess_spy", annual.loc[annual.nonoverlap]),
               ("common_controls12", "new_excess", matched),
               ("common_controls12_nonoverlap", "new_excess", matched.loc[matched.nonoverlap])]
    summary, years, uncertainty, availability = [], [], [], []
    periods = [("all", "1994-01-01", "2026-06-30"), ("1994_2009", "1994-01-01", "2009-12-31"),
               ("2010_2017", "2010-01-01", "2017-12-31"), ("2018_2025", "2018-01-01", "2026-06-30")]
    for label in LOOKBACKS:
        ranked = z[f"quintile_{label}"].notna()
        for group, f in [("ranked_annual", z.loc[z.excess_spy.notna() & ranked]),
                         ("missing_momentum_annual", z.loc[z.excess_spy.notna() & ~ranked])]:
            availability.append(dict(lookback=label, group=group, events=len(f),
                                     excess_spy=f.excess_spy.mean(), stock=f.stock_return.mean(), spy=f.spy_return.mean()))
        natural = z.loc[z.excess_spy.notna() & ranked]
        local_samples = samples + [("available_spy", "excess_spy", natural),
                                   ("available_spy_nonoverlap", "excess_spy", natural.loc[natural.nonoverlap])]
        for sample, metric, f in local_samples:
            f = f.assign(quintile=f[f"quintile_{label}"].astype(int))
            for period, lo, hi in periods:
                base = f.loc[f.date.between(lo, hi)]
                for variant in VARIANTS:
                    selected = base.loc[variant_mask(base, variant)]
                    summary.append(dict(lookback=label, **describe(selected, metric, sample, variant, period, len(base))))
            if sample.startswith("common"):
                for year, base in f.groupby(f.date.dt.year):
                    for variant in VARIANTS:
                        selected = base.loc[variant_mask(base, variant)]
                        years.append(dict(lookback=label, **describe(selected, metric, sample, variant, int(year), len(base))))
            if sample == "common_spy":
                for variant in VARIANTS:
                    contributions(f.loc[variant_mask(f, variant)], metric, "permco").to_csv(
                        out / f"contributors_{label}_{variant}.csv", index=False)
    pd.DataFrame(summary).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(years).to_csv(out / "by_signal_year.csv", index=False)
    pd.DataFrame(availability).to_csv(out / "availability.csv", index=False)
    for sample, metric, f in samples:
        print(f"Joint bootstrap {sample}: {len(f)} common events", flush=True)
        cal = valid_nyse_sessions(f.date.min(), f.date.max())
        for block in [252, 504]:
            uncertainty.extend(dict(sample=sample, metric=metric, **row) for row in
                               joint_lookback_intervals(f, metric, cal, block=block))
            pd.DataFrame(uncertainty).to_csv(out / "uncertainty.csv", index=False)
    config = dict(study_id=STUDY, lookback_sessions=LOOKBACKS, skip_sessions=21,
                  horizon=252, variants=VARIANTS, draws=2000, seed=20261016, blocks=[252, 504],
                  primary_population="common observed ATH annual events", ranking_pool="natural same-date eligible universe",
                  control_matching="frozen original 12-1 controls; no rematching", nonoverlap="frozen ath_10 flags",
                  simultaneous_family="nine threshold improvements", exploratory=True)
    (out / "config.json").write_text(json.dumps(config, indent=2))
    codes = [Path(__file__), ROOT / "src/ath_breakout/research/momentum_lookbacks.py",
             ROOT / "src/ath_breakout/research/momentum_filter.py", ROOT / "scripts/research/study_ath_momentum_filter.py"]
    manifest = dict(study_id=STUDY, run_id=stamp, status="completed_exploratory_lookback_comparison",
                    config=config, common_annual_events=len(annual), common_controls_events=len(matched),
                    inputs=inputs, protocol_sha256=sha256(ROOT / "research/ath/ATH_MOMENTUM_LOOKBACKS_PLAN.md"),
                    code_sha256={str(p.relative_to(ROOT)): sha256(p) for p in codes},
                    limitations=["Known conditional history; no untouched OOS or alpha proof",
                                 "Natural ranking denominators differ by available history",
                                 "Secondary controls match 12-1, not the shorter measures",
                                 "Approximate crossed bootstrap, repeated controls and multiple research choices"])
    manifest["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in out.rglob("*") if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(pd.DataFrame(summary).query("sample=='common_spy' and period=='all'")[
        ["lookback", "variant", "events", "stock", "spy", "excess"]].to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == "__main__":
    main()
