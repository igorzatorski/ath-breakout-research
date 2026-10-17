"""Frozen annual ATH concentration, company repeats and coverage diagnostics."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.baseline_robustness import (  # noqa: E402
    contributions, crossed_intervals, nonoverlap_ids,
)
from study_ath_signal import COLS, bounds  # noqa: E402

STUDY = "ath_10_baseline_robustness_v001"
BASE = ROOT / "outputs/research/ath/ath_04_signal_matched_v002/20261015T214148297829Z"
ANNUAL = ROOT / "outputs/research/ath/ath_06_annual_v001/20261015T221839273190Z"
MOM = ROOT / "outputs/research/ath/ath_08_momentum_control_v001/20261015T224210801657Z"
CAPM = ROOT / "outputs/research/ath/ath_09_capm_v001/20261016T193755193800Z"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def feature_profile(z, group):
    row = dict(group=group, events=len(z), securities=z.permno.nunique(),
               companies=z.permco.nunique(), first_date=str(z.date.min()),
               last_date=str(z.date.max()))
    for col in ["market_cap", "adv21", "vol63", "momentum"]:
        if col in z:
            v = z[col].replace([np.inf, -np.inf], np.nan).dropna()
            row.update({f"{col}_{k}": value for k, value in
                        zip(["observed", "q10", "median", "q90"],
                            [len(v), v.quantile(.1), v.median(), v.quantile(.9)])})
    if "excess_spy" in z:
        row["valid_spy"] = int(z.excess_spy.notna().sum())
        row["mean_observed_excess_spy"] = z.excess_spy.mean()
    return row


def reconstruct_candidates(events, original_manifest, checked, out):
    """Replay the original history gate, without matching or forward returns."""
    expected = {i["path"]: i["sha256"] for i in original_manifest["inputs"]}
    seed = checked(ROOT / "outputs/research/ath/shared_inputs/high_seed_before_1993.parquet", expected)
    high_valid = np.isfinite(seed.prior_comparable_high) & seed.prior_comparable_high.gt(0)
    seed_bound = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    prior = dict(zip(seed.loc[np.isfinite(seed_bound), "permno"], seed_bound[np.isfinite(seed_bound)]))
    legacy = set(seed.loc[~high_valid | seed.missing_high_rows.gt(0) |
                          seed.prior_comparable_high.lt(seed.prior_comparable_close), "permno"])
    membership = checked(ROOT / "data/processed/crsp/universe_memberships.parquet", expected)
    formation = membership[["effective_date", "formation_date"]].drop_duplicates().sort_values("effective_date")
    keys = pd.MultiIndex.from_frame(membership[["effective_date", "permno"]])
    gaps, uncertain, audits = set(), [], []
    tail = None
    prior_audit = pd.read_csv(BASE / "sample_audit.csv").set_index("year")
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
            cal = valid_nyse_sessions(f"{year-1}-08-01", f"{year}-12-31")
            dv = (lb.close * lb.volume).where(np.isfinite(lb.close) & lb.close.gt(0) &
                                             np.isfinite(lb.volume) & lb.volume.ge(0))
            adv = lb.assign(dv=dv).pivot(index="date", columns="permno", values="dv").reindex(cal).rolling(21, min_periods=21).mean()
            rr = lb.total_return.where(np.isfinite(lb.total_return) & lb.total_return.ge(-1))
            vol = lb.assign(rr=rr).pivot(index="date", columns="permno", values="rr").reindex(cal).rolling(63, min_periods=63).std() * np.sqrt(252)
            ix = pd.MultiIndex.from_frame(d[["date", "permno"]])
            d["adv21"] = adv.stack().reindex(ix).to_numpy()
            d["vol63"] = vol.stack().reindex(ix).to_numpy()
            date_map = pd.merge_asof(pd.DataFrame({"date": sorted(d.date.unique())}), formation,
                                     left_on="date", right_on="effective_date", direction="backward")
            d = d.merge(date_map, on="date", how="left", validate="many_to_one")
            member = pd.MultiIndex.from_frame(d[["effective_date", "permno"]]).isin(keys)
            eligible = member & d.adv21.ge(10000000) & d.adjusted_close.notna() & d.prior_ath.notna()
            signal = d.adjusted_close.gt(d.prior_ath)
            quality = ~d.history_uncertain & d.adjusted_high.notna()
            reconstructed = d.loc[eligible & signal & quality]
            original = events.loc[events.date.dt.year.eq(year)]
            left = pd.MultiIndex.from_frame(reconstructed[["permno", "date"]]).sort_values()
            right = pd.MultiIndex.from_frame(original[["permno", "date"]]).sort_values()
            assert left.equals(right), f"Qualified identity mismatch: {year}"
            bad_candidates = d.loc[eligible & signal & ~quality].copy()
            assert len(bad_candidates) == prior_audit.loc[year, "uncertain_history_potential_signals"]
            assert len(original) == prior_audit.loc[year, "primary_events"]
            assert int(eligible.sum()) == prior_audit.loc[year, "eligible_stock_days"]
            cols = ["permno", "permco", "ticker", "date", "market_cap", "adv21", "vol63", "history_uncertain"]
            uncertain.append(bad_candidates[cols])
            audits.append(dict(year=year, qualified=len(original), uncertain_candidates=len(bad_candidates),
                               eligible_stock_days=int(eligible.sum())))
            print(f"Coverage replay {year}: {len(original)} qualified, {len(bad_candidates)} uncertain", flush=True)
        _, _, observed_now, bad_now = bounds(d)
        for p, h in pd.Series(observed_now, index=d.index).groupby(d.permno).max().dropna().items():
            prior[p] = max(prior.get(p, h), h)
        gaps.update(d.loc[bad_now, "permno"].unique())
        cutoff = pd.Timestamp(year, 12, 31) - pd.Timedelta(days=150)
        tail = d.loc[d.date.ge(cutoff), ["permno", "date", "close", "volume", "total_return"]].copy()
    u = pd.concat(uncertain, ignore_index=True)
    u.to_parquet(out / "uncertain_candidates.parquet", index=False)
    pd.DataFrame(audits).to_csv(out / "history_coverage_by_year.csv", index=False)
    return u


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    print(out, flush=True)
    inputs = {}
    manifests = {}
    for directory in [BASE, ANNUAL, MOM, CAPM]:
        path = directory / "manifest.json"
        manifests[directory] = json.loads(path.read_text())
        inputs[str(path.relative_to(ROOT))] = sha256(path)

    def checked(path, expected, columns=None):
        key = str(path.relative_to(ROOT))
        assert sha256(path) == expected[key], path
        inputs[key] = expected[key]
        return pd.read_parquet(path, columns=columns)

    def artifact(directory, name, columns=None):
        path = directory / name
        expected = {str((directory / k).relative_to(ROOT)): v
                    for k, v in manifests[directory]["artifacts"].items()}
        return checked(path, expected, columns)

    features = pd.concat([artifact(BASE, f"by_year/events_{year}.parquet")
                          for year in range(1994, 2027)], ignore_index=True)
    assert len(features) == 75884 and features.event_id.is_unique
    assert features.permco.notna().all()
    annual = artifact(ANNUAL, "annual_returns.parquet")
    momentum = artifact(MOM, "event_returns.parquet")
    capm = artifact(CAPM, "event_results.parquet")
    for frame in [annual, momentum, capm]:
        assert frame.event_id.is_unique and set(frame.event_id) == set(features.event_id)
        identities = frame[["event_id", "permno", "date"]].merge(
            features[["event_id", "permno", "date"]], on="event_id", validate="one_to_one")
        assert identities.permno_x.equals(identities.permno_y)
        assert identities.date_x.equals(identities.date_y)
    dates = valid_nyse_sessions("1994-01-01", "2026-06-30")
    kept = set(nonoverlap_ids(features, dates))
    features["nonoverlap"] = features.event_id.isin(kept)
    last, decisions = {}, 0
    for row in features.sort_values(["date", "permco", "permno", "event_id"]).itertuples():
        p = dates.get_loc(row.date)
        decision = row.permco not in last or p >= last[row.permco] + 252
        assert decision == row.nonoverlap
        if decision:
            last[row.permco] = p
        decisions += 1
    z = capm.merge(features.drop(columns=[c for c in features if c in capm and c != "event_id"]),
                   on="event_id", validate="one_to_one")
    assert np.allclose(z.excess_spy, annual.set_index("event_id").loc[z.event_id, "excess_spy"], equal_nan=True)
    assert np.allclose(z.new_excess, momentum.set_index("event_id").loc[z.event_id, "new_excess"], equal_nan=True)
    z.to_parquet(out / "events.parquet", index=False)
    features[["event_id", "permno", "permco", "date", "nonoverlap"]].to_parquet(out / "selection.parquet", index=False)
    samples = [
        ("annual_spy", "excess_spy", z.loc[z.excess_spy.notna()]),
        ("momentum_common", "new_excess", z.loc[z.excess_spy.notna() & z.new_excess.notna() & z.excess_control.notna()]),
        ("capm_common", "momentum_gap", z.loc[z.stock_car.notna() & z.old_car.notna() & z.momentum_car.notna()]),
    ]
    summaries, influence, concentration, uncertainty = [], [], [], []
    for sample, metric, f in samples:
        for period, lo, hi in [("all", "1994-01-01", "2026-06-30"),
                               ("1994_2009", "1994-01-01", "2009-12-31"),
                               ("2010_2017", "2010-01-01", "2017-12-31"),
                               ("2018_2025", "2018-01-01", "2026-06-30")]:
            for variant, subset in [("baseline", f), ("nonoverlap", f.loc[f.nonoverlap])]:
                v = subset.loc[subset.date.between(lo, hi)]
                summaries.append(dict(sample=sample, metric=metric, period=period, variant=variant,
                                      events=len(v), securities=v.permno.nunique(), companies=v.permco.nunique(),
                                      mean=v[metric].mean(), median=v[metric].median(),
                                      equal_security=v.groupby("permno")[metric].mean().mean(),
                                      equal_company=v.groupby("permco")[metric].mean().mean(),
                                      equal_date=v.groupby("date")[metric].mean().mean(),
                                      stock_return=v.stock_return.mean(), spy_return=v.spy_return.mean()))
        for identity in ["permno", "permco"]:
            c = contributions(f, metric, identity)
            assert np.isclose(c.contribution.sum(), f[metric].mean(), atol=1e-12)
            c.to_csv(out / f"contributors_{sample}_{identity}.csv", index=False)
            if identity == "permco":
                labels = features.groupby("permco").ticker.agg(lambda x: " / ".join(sorted(set(x.dropna().astype(str)))))
                c["ticker_labels_descriptive"] = c.permco.map(labels)
                c.to_csv(out / f"contributors_{sample}_{identity}.csv", index=False)
                positive_total = c.positive_sum.sum()
                for n in [1, 5, 10, 20]:
                    for side, ids in [("top", c.head(n).permco), ("bottom", c.tail(n).permco)]:
                        remaining = f.loc[~f.permco.isin(ids)]
                        influence.append(dict(sample=sample, side=side, removed_companies=n,
                                              removed_events=len(f)-len(remaining), diagnostic_mean=remaining[metric].mean()))
                    top = c.head(n)
                    concentration.append(dict(sample=sample, top_companies=n,
                                              event_share=top.event_share.sum(), contribution=top.contribution.sum(),
                                              share_of_positive_sum=top.positive_sum.sum()/positive_total,
                                              company_event_count_mean_spearman=c.events.corr(c["mean"], method="spearman")))
        print(f"Bootstrap {sample}: {len(f)} events", flush=True)
        cal = dates[(dates >= f.date.min()) & (dates <= f.date.max())]
        for block in [252, 504]:
            for row in crossed_intervals(f, metric, cal, block=block):
                uncertainty.append(dict(sample=sample, metric=metric, **row))
        pd.DataFrame(uncertainty).to_csv(out / "uncertainty.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(influence).to_csv(out / "influence_diagnostics.csv", index=False)
    pd.DataFrame(concentration).to_csv(out / "concentration.csv", index=False)

    profiles = [feature_profile(z, "all_qualified"), feature_profile(z.loc[z.excess_spy.notna()], "annual_spy_valid")]
    for status, f in z.groupby("status"):
        profiles.append(feature_profile(f, f"annual_status_{status}"))
    annual_valid = z.loc[z.excess_spy.notna()]
    for label, mask in [("original_controls_complete", annual_valid.excess_control.notna()),
                        ("momentum_controls_complete", annual_valid.new_excess.notna()),
                        ("capm_available", annual_valid.stock_car.notna())]:
        profiles.extend([feature_profile(annual_valid.loc[mask], label),
                         feature_profile(annual_valid.loc[~mask], label + "_excluded")])
    z.assign(year=z.date.dt.year).groupby(["year", "status"]).size().rename("events").to_csv(out / "annual_status_by_year.csv")
    z.assign(year=z.date.dt.year).groupby("year").agg(
        signals=("event_id", "size"), valid_spy=("excess_spy", "count"),
        original_pairs=("excess_control", "count"), momentum_pairs=("new_excess", "count"),
        capm_available=("stock_car", "count")).to_csv(out / "sample_funnel_by_year.csv")
    uncertain = reconstruct_candidates(features, manifests[BASE], checked, out)
    profiles.append(feature_profile(uncertain, "uncertain_history_candidates"))
    pd.DataFrame(profiles).to_csv(out / "coverage_profiles.csv", index=False)
    config = dict(study_id=STUDY, horizon=252, separation=252, identity="historical_permco",
                  draws=2000, seed=20261016, blocks=[252, 504], no_parameter_search=True)
    (out / "config.json").write_text(json.dumps(config, indent=2))
    code = [Path(__file__), ROOT / "src/ath_breakout/research/baseline_robustness.py"]
    manifest = dict(study_id=STUDY, run_id=stamp, status="completed_diagnostic",
                    config=config, source_events=len(z), selected_before_future_validity=len(kept),
                    selection_decisions_verified=decisions, uncertain_candidates=len(uncertain),
                    inputs=inputs, code_sha256={str(p.relative_to(ROOT)): sha256(p) for p in code},
                    protocol_sha256=sha256(ROOT / "research/ath/ATH_BASELINE_ROBUSTNESS_PLAN.md"),
                    limitations=["Known history; conditional history-quality population",
                                 "Crossed bootstrap is approximate; reused-control network not fully modeled",
                                 "No portfolio, costs, alpha proof or filter optimization"])
    manifest["artifacts"] = {p.name: sha256(p) for p in out.iterdir() if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(pd.DataFrame(summaries).query("period == 'all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == "__main__":
    main()
