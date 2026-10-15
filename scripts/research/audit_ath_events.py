"""Local-only diagnostic ATH extraction; no portfolio or forward-return claims."""
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


def previous_high(highs, seed=None):
    """Exclude the current row; preserve prior highs across missing observations."""
    result = highs.cummax().ffill().shift(1)
    if seed is not None:
        result = result.clip(lower=seed).fillna(seed)
    return result


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/ath_01_signal_baseline_v001/{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    raw = ROOT / "data/raw/crsp"
    seed_path = raw / "ath_seed_before_1993.parquet"
    seeds = pd.read_parquet(seed_path)
    assert not seeds.permno.duplicated().any()
    prior = seeds.set_index("permno").prior_comparable_high.to_dict()
    seeded = set(prior)
    missing_history = set()
    inputs = [seed_path]
    columns = ["permno", "date", "high", "close", "price_adjustment_factor"]
    for y in range(1993, year):
        path = raw / f"daily_by_year/daily_{y}.parquet"
        inputs.append(path)
        d = pd.read_parquet(path, columns=columns)
        assert not d.duplicated(["permno", "date"]).any()
        valid = np.isfinite(d.high) & d.high.gt(0) & np.isfinite(d.price_adjustment_factor) & d.price_adjustment_factor.gt(0)
        missing_history.update(d.loc[~valid, "permno"].unique())
        high = (d.loc[valid, "high"] / d.loc[valid, "price_adjustment_factor"]).groupby(d.loc[valid, "permno"]).max()
        for p, value in high.items():
            prior[p] = max(value, prior.get(p, value))
        print(f"Historical highs: {y}", flush=True)

    path = raw / f"daily_by_year/daily_{year}.parquet"
    inputs.append(path)
    d = pd.read_parquet(path).sort_values(["permno", "date"]).reset_index(drop=True)
    d["date"] = pd.to_datetime(d.date)
    assert not d.duplicated(["permno", "date"]).any()
    valid_factor = np.isfinite(d.price_adjustment_factor) & d.price_adjustment_factor.gt(0)
    d["adjusted_high"] = (d.high / d.price_adjustment_factor).where(valid_factor & d.high.gt(0) & np.isfinite(d.high))
    d["adjusted_close"] = (d.close / d.price_adjustment_factor).where(valid_factor & d.close.gt(0) & np.isfinite(d.close))
    d["prior_ath"] = np.nan
    d["prior_missing_high"] = False
    for p, g in d.groupby("permno", sort=False):
        d.loc[g.index, "prior_ath"] = previous_high(g.adjusted_high, prior.get(p)).values
        d.loc[g.index, "prior_missing_high"] = g.adjusted_high.isna().cummax().shift(1, fill_value=False).values | (p in missing_history)
    d["pre1993_close_seed_only"] = d.permno.isin(seeded)
    # Liquidity uses 21 actual NYSE sessions, not the last 21 available rows.
    tail_path = raw / f"daily_by_year/daily_{year-1}.parquet"
    tail = pd.read_parquet(tail_path, columns=["permno", "date", "close", "volume"])
    tail = tail.loc[pd.to_datetime(tail.date).ge(f"{year-1}-11-01")]
    liquidity = pd.concat([tail, d[["permno", "date", "close", "volume"]]], ignore_index=True)
    liquidity["date"] = pd.to_datetime(liquidity.date)
    sessions = valid_nyse_sessions(f"{year-1}-11-01", f"{year}-12-31")
    liquidity["dollar_volume"] = (liquidity.close * liquidity.volume).where(
        liquidity.close.gt(0) & liquidity.volume.ge(0) & np.isfinite(liquidity.close) & np.isfinite(liquidity.volume))
    wide = liquidity.pivot(index="date", columns="permno", values="dollar_volume").reindex(sessions)
    avg = wide.rolling(21, min_periods=21).mean().stack().rename("adv21").reset_index()
    avg.columns = ["date", "permno", "adv21"]
    d = d.merge(avg, on=["date", "permno"], how="left", validate="one_to_one")
    membership_path = ROOT / "data/processed/crsp/universe_memberships.parquet"
    inputs.append(membership_path)
    membership = pd.read_parquet(membership_path)
    formation = membership[["effective_date", "formation_date"]].drop_duplicates().sort_values("effective_date")
    dates = pd.merge_asof(pd.DataFrame({"date": sorted(d.date.unique())}), formation,
                          left_on="date", right_on="effective_date", direction="backward")
    assert (dates.formation_date < dates.date).all()
    d = d.merge(dates, on="date", how="left", validate="many_to_one")
    keys = pd.MultiIndex.from_frame(membership[["effective_date", "permno"]])
    assert not keys.duplicated().any()
    d["pit_member"] = pd.MultiIndex.from_frame(d[["effective_date", "permno"]]).isin(keys)
    candidates = d.loc[d.adjusted_close.gt(d.prior_ath)].copy()
    candidates["exclusion_reason"] = np.select(
        [~candidates.pit_member, candidates.adv21.isna(), candidates.adv21.lt(10_000_000)],
        ["not_pit_member", "incomplete_21_session_liquidity", "adv21_below_10m"], default="")
    events = candidates.loc[candidates.exclusion_reason.eq("")].copy()
    events["repeated_in_year"] = events.duplicated("permno")
    entry_sessions = valid_nyse_sessions(f"{year}-01-01", f"{year+1}-01-10")
    next_dates = pd.Series(entry_sessions[1:], index=entry_sessions[:-1])
    events["entry_date"] = events.date.map(next_dates)
    # Include next January to avoid falsely censoring the final December signal.
    next_path = raw / f"daily_by_year/daily_{year+1}.parquet"
    inputs.append(next_path)
    open_columns = ["permno", "date", "open", "price_adjustment_factor"]
    opens = pd.concat([d[open_columns], pd.read_parquet(next_path, columns=open_columns)])
    events = events.merge(opens.rename(columns={"date": "entry_date", "open": "entry_open",
                                                "price_adjustment_factor": "entry_price_factor"}),
                          on=["permno", "entry_date"], how="left", validate="one_to_one")
    events["missing_entry_open"] = ~np.isfinite(events.entry_open) | events.entry_open.le(0)
    events["entry_adjusted_open"] = (events.entry_open / events.entry_price_factor).where(
        np.isfinite(events.entry_price_factor) & events.entry_price_factor.gt(0))
    events["breakout_pct"] = events.adjusted_close / events.prior_ath - 1
    events["high_below_close"] = events.adjusted_high.lt(events.adjusted_close)
    events["seed_verified"] = ~events.pre1993_close_seed_only
    events.to_parquet(out / "events.parquet", index=False)
    events.to_csv(out / "events.csv", index=False)
    candidates.loc[candidates.exclusion_reason.ne("")].to_csv(out / "exclusions.csv", index=False)
    samples = pd.concat([events.groupby("permno", sort=True).head(1).head(6), events.nlargest(3, "breakout_pct"),
                         events.loc[events.price_adjustment_factor.ne(1)].groupby("permno").head(1).head(3),
                         events.loc[events.missing_entry_open].head(3)]).drop_duplicates(["permno", "date"])
    # Independent scalar recomputation for sampled securities from raw partitions.
    checks = []
    ids = set(samples.permno)
    independent = {p: seeds.set_index("permno").prior_comparable_high.get(p, np.nan) for p in ids}
    for y in range(1993, year + 1):
        h = pd.read_parquet(raw / f"daily_by_year/daily_{y}.parquet", columns=columns)
        h = h.loc[h.permno.isin(ids)]
        for event in samples.itertuples():
            history = h.loc[h.permno.eq(event.permno) & pd.to_datetime(h.date).lt(event.date)]
            values = (history.high / history.price_adjustment_factor).where(
                history.high.gt(0) & history.price_adjustment_factor.gt(0))
            maximum = values.loc[np.isfinite(values) & values.gt(0)].max()
            key = (event.permno, event.date)
            old = independent.get(key, independent[event.permno])
            independent[key] = np.nanmax([old, maximum]) if pd.notna(old) or pd.notna(maximum) else np.nan
    for e in samples.itertuples():
        expected = independent[(e.permno, e.date)]
        checks.append({"permno": e.permno, "ticker": e.ticker, "date": str(e.date.date()),
                       "prior_ath": e.prior_ath, "independent_prior_ath": expected,
                       "match": bool(np.isclose(e.prior_ath, expected)),
                       "adjusted_close": e.adjusted_close, "entry_nominal_open": e.entry_open,
                       "entry_adjusted_open": e.entry_adjusted_open,
                       "pre1993_seed_uncertain": e.pre1993_close_seed_only})
    pd.DataFrame(checks).to_csv(out / "sample_checks.csv", index=False)
    summary = {"year": year, "raw_rows": len(d), "raw_breakouts": len(candidates),
               "excluded": candidates.loc[candidates.exclusion_reason.ne(""), "exclusion_reason"].value_counts().to_dict(),
               "events": len(events), "securities": int(events.permno.nunique()),
               "repeated_in_year": int(events.repeated_in_year.sum()),
               "missing_entry_open": int(events.missing_entry_open.sum()),
               "pre1993_seed_uncertain_events": int(events.pre1993_close_seed_only.sum()),
               "prior_missing_high_events": int(events.prior_missing_high.sum()),
               "high_below_close_events": int(events.high_below_close.sum()),
               "independent_samples": len(checks), "independent_samples_match": all(x["match"] for x in checks),
               "status": "diagnostic_only_seed_definition_unresolved", "forward_returns_computed": False}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    manifest = {"study_id": "ath_01_signal_baseline_v001", "stage": "signal_diagnostic", "summary": summary,
                "source_files": [{"path": str(p.relative_to(ROOT)), "size": p.stat().st_size,
                                  "mtime_ns": p.stat().st_mtime_ns} for p in inputs],
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "limitation": "Pre-1993 seed uses closes, not highs. Missing historical highs and unverified listing coverage may understate ATH. No vendor requery or return/alpha claim."}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(out, flush=True)


if __name__ == "__main__":
    main()
