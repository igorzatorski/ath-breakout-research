"""Explain historical mean differences with auditable descriptive decompositions."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.period_diagnostic import (  # noqa: E402
    PERIODS, additive_groups, mix_within_decomposition, period_change_intervals, period_labels,
)
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT / "outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z"
STUDY = "ath_13_period_diagnostic_v001"
LABELS = ["le_minus50", "minus50_to0", "0_to50", "50_to100", "100_to200", "gt200"]


def describe(f, variant, period):
    x = f.excess_spy
    row = dict(variant=variant, period=period, events=len(f), securities=f.permno.nunique(),
               companies=f.permco.nunique(), stock=f.stock_return.mean(), spy=f.spy_return.mean(),
               excess=x.mean(), median_excess=x.median(), median_stock=f.stock_return.median(),
               loss_fraction=f.stock_return.lt(0).mean(), underperform=x.lt(0).mean(),
               q05_stock=f.stock_return.quantile(.05), q95_stock=f.stock_return.quantile(.95),
               q99_stock=f.stock_return.quantile(.99), terminal_events=int(f.terminal_cash.sum()),
               equal_company=f.groupby("permco").excess_spy.mean().mean(),
               equal_date=f.groupby("date").excess_spy.mean().mean(),
               equal_year=f.groupby(f.date.dt.year).excess_spy.mean().mean(),
               capped_positive_excess=x.clip(upper=1).mean())
    for metric in ["market_cap", "adv21", "vol63", "momentum_6_1", "beta", "size_percentile"]:
        if metric in f:
            v = f[metric].replace([np.inf, -np.inf], np.nan)
            row[f"{metric}_median"] = v.median()
            row[f"{metric}_observed"] = int(v.notna().sum())
    return row


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True, exist_ok=False)
    print(out, flush=True)
    source_manifest = json.loads((SOURCE / "manifest.json").read_text())
    inputs = {str((SOURCE / "manifest.json").relative_to(ROOT)): sha256(SOURCE / "manifest.json")}

    def source(name):
        path = SOURCE / name
        digest = sha256(path)
        assert digest == source_manifest["artifacts"][str(Path(name))]
        inputs[str(path.relative_to(ROOT))] = digest
        return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)

    z = source("events.parquet")
    assert z.event_id.is_unique and len(z) == 75884
    source_summary = source("summary.csv")
    size_rows = []
    for year in range(1994, 2027):
        pool = source(f"by_year/ranking_pool_6_1_{year}.parquet")
        raw_path = ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet"
        key = str(raw_path.relative_to(ROOT))
        digest = sha256(raw_path)
        assert digest == source_manifest["inputs"][key]
        inputs[key] = digest
        raw = pd.read_parquet(raw_path, columns=["permno", "date", "market_cap"])
        assert not raw.duplicated(["date", "permno"]).any()
        p = pool[["date", "permno", "permco"]].merge(raw, on=["date", "permno"],
                                                       how="left", validate="one_to_one")
        valid = np.isfinite(p.market_cap) & p.market_cap.gt(0)
        observed = p.loc[valid].copy()
        n = observed.groupby("date").market_cap.transform("size")
        observed["size_percentile"] = (observed.groupby("date").market_cap.rank(method="average")-.5)/n
        observed["size_population"] = n
        observed.to_parquet(out / f"by_year/size_pool_{year}.parquet", index=False)
        e = z.loc[z.date.dt.year.eq(year), ["event_id", "date", "permno", "market_cap"]]
        e = e.merge(observed[["date", "permno", "size_percentile", "size_population"]],
                    on=["date", "permno"], how="left", validate="one_to_one")
        size_rows.append(e[["event_id", "size_percentile", "size_population"]])
        print(f"Size context {year}: {len(observed)} eligible rows", flush=True)
    z = z.merge(pd.concat(size_rows, ignore_index=True), on="event_id", validate="one_to_one")
    z["period"] = period_labels(z.date)
    z["year"] = z.date.dt.year
    p = z.size_percentile
    z["size_bucket"] = np.select([p.le(.25), p.le(.5), p.le(.75), p.notna()],
                                  ["size_Q1", "size_Q2", "size_Q3", "size_Q4"], default="size_missing")
    v = z.vol63
    z["vol_bucket"] = np.select([v.le(.2), v.le(.4), v.le(.6), v.notna()],
                                 ["vol_le20", "vol_20_40", "vol_40_60", "vol_gt60"], default="vol_missing")
    z["size_vol_cell"] = z.size_bucket + "/" + z.vol_bucket
    z["excess_bucket"] = pd.cut(z.excess_spy, [-np.inf, -.5, 0, .5, 1, 2, np.inf], labels=LABELS)
    z.to_parquet(out / "events.parquet", index=False)
    valid = z.common_momentum & z.excess_spy.notna()
    base = z.loc[valid]
    cohorts = {"baseline": base, "12_1_top20": base.loc[base.quintile_12_1.eq(5)],
               "6_1_top20": base.loc[base.quintile_6_1.eq(5)],
               "3_1_top20": base.loc[base.quintile_3_1.eq(5)]}
    summary = []
    for variant, frame in cohorts.items():
        for overlap, f in [("all", frame), ("nonoverlap", frame.loc[frame.nonoverlap])]:
            for period in PERIODS:
                g = f.loc[f.period.eq(period)]
                summary.append(dict(overlap=overlap, **describe(g, variant, period)))
                lookup_sample = "common_spy" if overlap == "all" else "common_spy_nonoverlap"
                lookup_period = {"early": "1994_2009", "middle": "2010_2017", "recent": "2018_2025"}[period]
                label = "12_1" if variant == "baseline" else variant.split("_top")[0]
                old = source_summary.loc[source_summary["sample"].eq(lookup_sample) &
                    source_summary.period.eq(lookup_period) & source_summary.lookback.eq(label) &
                    source_summary.variant.eq("baseline" if variant == "baseline" else "top20")].iloc[0]
                assert len(g) == old.events and np.isclose(g.excess_spy.mean(), old.excess, atol=1e-12)
    pd.DataFrame(summary).to_csv(out / "period_summary.csv", index=False)
    main = cohorts["6_1_top20"]
    years = [describe(f, "6_1_top20", int(year)) for year, f in main.groupby("year")]
    pd.DataFrame(years).to_csv(out / "by_signal_year.csv", index=False)
    years_contribution = additive_groups(main, "year", "excess_spy")
    years_contribution.to_csv(out / "year_contributions.csv", index=False)
    company = additive_groups(main, "permco", "excess_spy")
    names = z.groupby("permco").ticker.agg(lambda x: " / ".join(sorted(set(x.dropna().astype(str)))))
    company["ticker_labels_descriptive"] = company.permco.map(names)
    company.to_csv(out / "company_contributions.csv", index=False)
    tail = additive_groups(main, "excess_bucket", "excess_spy")
    tail.to_csv(out / "tail_contributions.csv", index=False)
    annual_influence, company_influence, episodes = [], [], []
    for period, frame in main.groupby("period"):
        for year in frame.year.unique():
            kept = frame.loc[frame.year.ne(year)]
            annual_influence.append(dict(period=period, omitted_year=int(year), events=len(kept), mean=kept.excess_spy.mean()))
        c = company.loc[company.period.eq(period)].sort_values("contribution", ascending=False)
        for side in ["top", "bottom"]:
            for n in [1, 5, 10]:
                ids = c.head(n).permco if side == "top" else c.tail(n).permco
                kept = frame.loc[~frame.permco.isin(ids)]
                company_influence.append(dict(period=period, side=side, removed_companies=n,
                    removed_events=len(frame)-len(kept), remaining_mean=kept.excess_spy.mean()))
        kept = frame.loc[~frame.year.between(1998, 2000)]
        episodes.append(dict(period=period, omitted="1998_2000", original_events=len(frame),
                             remaining_events=len(kept), mean=kept.excess_spy.mean()))
    pd.DataFrame(annual_influence).to_csv(out / "leave_one_year_out.csv", index=False)
    pd.DataFrame(company_influence).to_csv(out / "company_influence.csv", index=False)
    pd.DataFrame(episodes).to_csv(out / "episode_sensitivity.csv", index=False)
    components = []
    for overlap, f in [("all", main), ("nonoverlap", main.loc[main.nonoverlap])]:
        means = f.groupby("period")[['stock_return', 'spy_return', 'excess_spy']].mean()
        change_stock = means.loc["recent", "stock_return"]-means.loc["early", "stock_return"]
        change_spy = means.loc["recent", "spy_return"]-means.loc["early", "spy_return"]
        change_excess = means.loc["recent", "excess_spy"]-means.loc["early", "excess_spy"]
        assert np.isclose(change_excess, change_stock-change_spy, atol=1e-12)
        components.append(dict(overlap=overlap, stock_change=change_stock, spy_change=change_spy,
                               stock_component=change_stock, benchmark_component=-change_spy,
                               excess_change=change_excess))
    pd.DataFrame(components).to_csv(out / "stock_spy_decomposition.csv", index=False)
    mix_summary = []
    for grouping in ["size_bucket", "vol_bucket", "size_vol_cell", "excess_bucket"]:
        mix = mix_within_decomposition(main, grouping, "excess_spy")
        mix.to_csv(out / f"mix_within_{grouping}.csv", index=False)
        shared = mix.loc[mix.shared]
        wa, wb = shared.old_weight.sum(), shared.new_weight.sum()
        mix_summary.append(dict(grouping=grouping, shared_cells=len(shared),
            old_shared_weight=wa, new_shared_weight=wb,
            mix=mix["mix"].sum(), within=mix["within"].sum(), support=mix.one_sided_support.sum(),
            total_change=mix.total_change.sum(),
            old_standardized_mean=np.sum(shared.old_mean*(shared.old_weight+shared.new_weight)/(wa+wb)),
            recent_standardized_mean=np.sum(shared.new_mean*(shared.old_weight+shared.new_weight)/(wa+wb))))
    pd.DataFrame(mix_summary).to_csv(out / "mix_within_summary.csv", index=False)
    nested = []
    for label, f in [("momentum_controls_available", main.loc[main.new_excess.notna()]),
                     ("capm_common", main.loc[main.stock_car.notna() & main.old_car.notna() & main.momentum_car.notna()])]:
        for period, g in f.groupby("period"):
            car_complete = label == "capm_common"
            nested.append(dict(sample=label, period=period, events=len(g), stock=g.stock_return.mean(),
                spy=g.spy_return.mean(), excess_spy=g.excess_spy.mean(), controls12=g.new_control_return.mean(),
                excess_controls12=g.new_excess.mean(), stock_car=g.stock_car.mean() if car_complete else np.nan,
                control_car=g.momentum_car.mean() if car_complete else np.nan,
                car_gap=g.momentum_gap.mean() if car_complete else np.nan,
                beta=g.beta.mean() if car_complete else np.nan))
    pd.DataFrame(nested).to_csv(out / "matched_capm_context.csv", index=False)
    z.assign(selected_6_1=z.quintile_6_1.eq(5)).groupby("year").agg(signals=("event_id", "size"),
        annual_valid=("excess_spy", "count"), common_momentum=("common_momentum", "sum"),
        selected_6_1=("selected_6_1", "sum")).to_csv(out / "coverage_by_year.csv")
    uncertainty = []
    cal = valid_nyse_sessions(main.date.min(), main.date.max())
    for block in [252, 504]:
        print(f"Period-change bootstrap: block {block}", flush=True)
        uncertainty.extend(period_change_intervals(main, cal, block=block))
    pd.DataFrame(uncertainty).to_csv(out / "uncertainty.csv", index=False)
    config = dict(study_id=STUDY, focus="6_1_top20_selected_after_prior_results", horizon=252,
                  periods=PERIODS, comparison="recent_minus_early", bootstrap_draws=2000,
                  seed=20261016, blocks=[252, 504], outcome_buckets=LABELS,
                  positive_excess_cap_diagnostic=1., sector_available=False, causal=False)
    (out / "config.json").write_text(json.dumps(config, indent=2))
    codes = [Path(__file__), ROOT / "src/ath_breakout/research/period_diagnostic.py"]
    manifest = dict(study_id=STUDY, run_id=stamp, status="completed_descriptive_period_diagnostic",
        config=config, main_events=len(main), inputs=inputs,
        code_sha256={str(p.relative_to(ROOT)): sha256(p) for p in codes},
        protocol_sha256=sha256(ROOT / "research/ath/ATH_PERIOD_DIAGNOSTIC_PLAN.md"),
        limitations=["Accounting attribution is not causal identification", "Known-history chosen focus; no untouched OOS",
                     "No PIT sectors/fundamentals; original quality exclusions persist", "Approximate bootstrap and reused controls"])
    manifest["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in out.rglob("*") if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(pd.DataFrame(components).to_string(index=False), flush=True)
    print(pd.DataFrame(mix_summary).to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == "__main__":
    main()
