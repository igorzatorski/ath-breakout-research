"""Unfiltered local-history ATH event study with contemporaneous matched controls."""
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
from ath_breakout.research.high_breakout import holding_return  # noqa: E402
from ath_breakout.research.signal_study import (  # noqa: E402
    forward_arrays, match_controls, moving_block_interval,
)

STUDY = "ath_04_signal_matched_v002"
END = pd.Timestamp("2026-06-30")
HORIZONS = (5, 21, 63, 126)
COLS = ["permno", "permco", "ticker", "date", "high", "close", "open", "volume",
        "price_adjustment_factor", "total_return", "market_cap", "delisting_flag"]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bounds(d):
    factor = d.price_adjustment_factor
    close = (d.close/factor).where(np.isfinite(factor) & factor.gt(0) & np.isfinite(d.close) & d.close.gt(0))
    high = (d.high/factor).where(np.isfinite(factor) & factor.gt(0) & np.isfinite(d.high) & d.high.gt(0)
                               & (d.close.isna() | d.high.ge(d.close)))
    # The closing price remains a lower bound even if a daily high is missing.
    observed = np.fmax(close, high)
    bad = high.isna() & d.delisting_flag.ne("Y")
    return close, high, observed, bad


def describe(z, group, horizon):
    if z.empty:
        return {"group": group, "horizon": horizon, "events": 0}
    return {"group": group, "horizon": horizon, "events": len(z), "securities": z.permno.nunique(),
            "mean_stock": z.stock_return.mean(), "median_stock": z.stock_return.median(),
            "q05_stock": z.stock_return.quantile(.05), "q95_stock": z.stock_return.quantile(.95),
            "loss_fraction": z.stock_return.lt(0).mean(), "mean_spy": z.spy_return.mean(),
            "mean_control": z.control_return.mean(), "mean_excess_spy": z.excess_spy.mean(),
            "mean_excess_control": z.excess_control.mean(), "median_excess_control": z.excess_control.median(),
            "equal_security_excess_control": z.groupby("permno").excess_control.mean().mean(),
            "equal_date_excess_control": z.groupby("date").excess_control.mean().mean(),
            "equal_security_excess_spy": z.groupby("permno").excess_spy.mean().mean(),
            "terminal_events": int(z.terminal_cash.sum())}


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True, exist_ok=False)
    config = {"study_id": STUDY, "signal_start": "1994-01-03", "data_end": str(END.date()),
              "primary_horizon": 21, "horizons": HORIZONS, "min_adv21": 10000000,
              "match_k": 5, "size_ratio_caliper": 2, "vol_ratio_caliper": 1.5, "vol_window": 63,
              "pre1993_seed": "isolated_WRDS_high_export; incomplete_high_history_excluded", "invalid_prior_high": "exclude_from_primary",
              "costs": "gross_signal_study", "parameters_optimized": False}
    (out / "config.json").write_text(json.dumps(config, indent=2))
    raw_root = ROOT / "data/raw/crsp/daily_by_year"
    seed_path = ROOT / "outputs/research/ath/shared_inputs/high_seed_before_1993.parquet"
    seed = pd.read_parquet(seed_path)
    assert not seed.permno.duplicated().any()
    high_valid = np.isfinite(seed.prior_comparable_high) & seed.prior_comparable_high.gt(0)
    seed_bound = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    prior = dict(zip(seed.loc[np.isfinite(seed_bound), "permno"], seed_bound[np.isfinite(seed_bound)]))
    # Conservative: missing pre-period highs, including unpriced vendor rows,
    # are not silently assumed harmless. Report this narrower population.
    incomplete = (~high_valid | seed.missing_high_rows.gt(0)
                  | seed.prior_comparable_high.lt(seed.prior_comparable_close))
    legacy = set(seed.loc[incomplete, "permno"])
    gaps = set()
    memberships_path = ROOT / "data/processed/crsp/universe_memberships.parquet"
    membership = pd.read_parquet(memberships_path)
    formation = membership[["effective_date", "formation_date"]].drop_duplicates().sort_values("effective_date")
    keys = pd.MultiIndex.from_frame(membership[["effective_date", "permno"]])
    assert not keys.duplicated().any()
    spy_path = ROOT / "data/raw/yfinance/SPY.parquet"
    spy = pd.read_parquet(spy_path).set_index("date").sort_index()
    tail = None
    summaries, audits, all_forward = [], [], []
    offset = 0
    scalar_checks = 0
    for year in range(1993, 2027):
        path = raw_root / f"daily_{year}.parquet"
        d = pd.read_parquet(path, columns=COLS).sort_values(["permno", "date"]).reset_index(drop=True)
        d.date = pd.to_datetime(d.date)
        assert not d.duplicated(["permno", "date"]).any()
        close, high, observed, bad = bounds(d)
        d["adjusted_close"], d["adjusted_high"], d["observed_bound"] = close, high, observed
        cumulative = d.groupby("permno").observed_bound.cummax()
        cumulative = cumulative.groupby(d.permno).ffill()
        d["prior_ath"] = np.fmax(cumulative.groupby(d.permno).shift(), d.permno.map(prior))
        prior_bad = bad.groupby(d.permno).cummax().groupby(d.permno).shift(fill_value=False)
        d["history_uncertain"] = d.permno.isin(legacy) | d.permno.isin(gaps) | prior_bad
        if year >= 1994:
            lookback = pd.concat([tail, d[["permno", "date", "close", "volume", "total_return"]]], ignore_index=True)
            rolling_sessions = valid_nyse_sessions(f"{year-1}-08-01", f"{year}-12-31")
            dv = (lookback.close*lookback.volume).where(np.isfinite(lookback.close) & lookback.close.gt(0)
                                                      & np.isfinite(lookback.volume) & lookback.volume.ge(0))
            adv = lookback.assign(dv=dv).pivot(index="date", columns="permno", values="dv").reindex(rolling_sessions).rolling(21,min_periods=21).mean()
            rr = lookback.total_return.where(np.isfinite(lookback.total_return) & lookback.total_return.ge(-1))
            vol = lookback.assign(rr=rr).pivot(index="date",columns="permno",values="rr").reindex(rolling_sessions).rolling(63,min_periods=63).std()*np.sqrt(252)
            index = pd.MultiIndex.from_frame(d[["date", "permno"]])
            d["adv21"] = adv.stack().reindex(index).to_numpy()
            d["vol63"] = vol.stack().reindex(index).to_numpy()
            date_map = pd.merge_asof(pd.DataFrame({"date": sorted(d.date.unique())}), formation,
                                     left_on="date", right_on="effective_date", direction="backward")
            d = d.merge(date_map, on="date", how="left", validate="many_to_one")
            member = pd.MultiIndex.from_frame(d[["effective_date", "permno"]]).isin(keys)
            eligible = member & d.adv21.ge(10000000) & d.adjusted_close.notna() & d.prior_ath.notna()
            signal = d.adjusted_close.gt(d.prior_ath)
            quality = ~d.history_uncertain & d.adjusted_high.notna()
            events = d.loc[eligible & signal & quality].copy()
            events["event_id"] = np.arange(offset, offset+len(events))
            offset += len(events)
            assert (events.formation_date < events.date).all()
            pool = d.loc[eligible & quality & d.market_cap.gt(0) & np.isfinite(d.market_cap) & d.vol63.gt(0) & np.isfinite(d.vol63)].copy()
            match_rows = []
            for date, day_events in events.groupby("date", sort=True):
                day_events = day_events.loc[day_events.market_cap.gt(0) & np.isfinite(day_events.market_cap) & day_events.vol63.gt(0) & np.isfinite(day_events.vol63)]
                controls = pool.loc[pool.date.eq(date) & ~pool.adjusted_close.gt(pool.prior_ath)]
                matched = match_controls(day_events, controls)
                by_id = controls.set_index("permno")
                for e in day_events.itertuples():
                    for rank, p in enumerate(matched.get(e.permno, []), start=1):
                        control = by_id.loc[p]
                        match_rows.append({"event_id": e.event_id, "date": date, "permno": p, "rank": rank,
                                           "control_permco": control.permco, "event_permco": e.permco,
                                           "size_ratio": control.market_cap/e.market_cap,
                                           "vol_ratio": control.vol63/e.vol63})
            matches = pd.DataFrame(match_rows, columns=["event_id","date","permno","rank","control_permco","event_permco","size_ratio","vol_ratio"])
            events.to_parquet(out / f"by_year/events_{year}.parquet", index=False)
            matches.to_parquet(out / f"by_year/matches_{year}.parquet", index=False)
            audit = {"year": year, "eligible_stock_days": int(eligible.sum()),
                     "uncertain_history_potential_signals": int((eligible & signal & ~quality).sum()),
                     "primary_events": len(events), "matched_at_signal": int(matches.event_id.nunique())}
            audits.append(audit)
            if not events.empty:
                queries = pd.concat([events[["event_id","date","permno"]].assign(rank=0), matches[["event_id","date","permno","rank"]]], ignore_index=True)
                selected = queries.permno.unique()
                future = pd.read_parquet(raw_root / f"daily_{year+1}.parquet", columns=["permno","date","open","close","total_return","delisting_flag"]) if year < 2026 else pd.DataFrame()
                source = pd.concat([d[["permno","date","open","close","total_return","delisting_flag"]], future], ignore_index=True)
                source = source.loc[source.permno.isin(selected)]
                calendar = valid_nyse_sessions(f"{year}-01-01", f"{year+1}-07-31")
                ids = pd.Index(sorted(selected))
                arrays = {name: source.pivot(index="date",columns="permno",values=name).reindex(index=calendar,columns=ids).to_numpy(float)
                          for name in ["open","close","total_return"]}
                terminals = source.assign(terminal=source.delisting_flag.eq("Y")).pivot(index="date",columns="permno",values="terminal").reindex(index=calendar,columns=ids).fillna(False).to_numpy(bool)
                e_rows = calendar.get_indexer(pd.DatetimeIndex(queries.date))+1
                c_cols = ids.get_indexer(queries.permno)
                available_end = calendar.searchsorted(END,side="right")-1
                spy_year = spy.reindex(calendar)
                year_results = []
                for horizon in HORIZONS:
                    values, status, terminal = forward_arrays(arrays["open"], arrays["close"], arrays["total_return"], terminals, e_rows, c_cols, horizon, available_end)
                    q = queries.assign(value=values,status=status,terminal=terminal)
                    event_q = q.loc[q["rank"].eq(0)].copy()
                    er = e_rows[:len(events)]
                    end_rows = er+horizon-1
                    with np.errstate(divide="ignore",invalid="ignore"):
                        benchmark = (spy_year.close.to_numpy()[er]/spy_year.open.to_numpy()[er]
                                     * spy_year.adj_close.to_numpy()[end_rows]/spy_year.adj_close.to_numpy()[er]-1)
                    controls = q.loc[q["rank"].gt(0)].groupby("event_id").value.agg(["mean","count"])
                    result = events[["event_id","permno","date"]].copy()
                    result["horizon"] = horizon
                    result["stock_return"] = event_q.value.to_numpy()
                    result["status"] = event_q.status.to_numpy()
                    result["terminal_cash"] = event_q.terminal.to_numpy()
                    result["spy_return"] = benchmark
                    result["matched_at_signal"] = result.event_id.isin(matches.event_id)
                    result["valid_control_count"] = result.event_id.map(controls["count"]).fillna(0).astype(int)
                    result["control_return"] = result.event_id.map(controls["mean"]).where(result.valid_control_count.eq(5))
                    result["excess_spy"] = result.stock_return-result.spy_return
                    result["excess_control"] = result.stock_return-result.control_return
                    year_results.append(result)
                    # Compare scalar and vector engines on preselected positions, including controls.
                    for qi in np.linspace(0,len(queries)-1,min(5,len(queries)),dtype=int):
                        if status[qi] != "ok":
                            continue
                        col = c_cols[qi]
                        history = pd.DataFrame({"open":arrays["open"][:,col],"close":arrays["close"][:,col],
                                                "total_return":arrays["total_return"][:,col],"delisting_flag":np.where(terminals[:,col],"Y","N")})
                        expected, expected_status, _ = holding_return(history,e_rows[qi],horizon)
                        assert expected_status.startswith("ok") and np.isclose(values[qi],expected,rtol=1e-10,atol=1e-10)
                        scalar_checks += 1
                f = pd.concat(year_results, ignore_index=True)
                f.to_parquet(out / f"by_year/forward_{year}.parquet", index=False)
                all_forward.append(f)
            print(f"{year}: {len(events):,} quality-qualified ATH events; {audit['matched_at_signal']:,} matched", flush=True)
        # Advance history through ALL raw rows, not just eligible/universe dates.
        # d may have been merged/reordered; recompute bounds on its own current order.
        _, _, observed_now, bad_now = bounds(d)
        maxima = pd.Series(observed_now,index=d.index).groupby(d.permno).max()
        for p,h in maxima.dropna().items():
            prior[p] = max(prior.get(p,h),h)
        gaps.update(d.loc[bad_now,"permno"].unique())
        cutoff = pd.Timestamp(year,12,31)-pd.Timedelta(days=150)
        tail = d.loc[d.date.ge(cutoff),["permno","date","close","volume","total_return"]].copy()
    f = pd.concat(all_forward, ignore_index=True)
    f.to_parquet(out / "forward_returns.parquet", index=False)
    pd.DataFrame(audits).to_csv(out / "sample_audit.csv",index=False)
    for horizon in HORIZONS:
        h = f.loc[f.horizon.eq(horizon)]
        spy_valid = h.loc[h.excess_spy.notna()]
        paired = h.loc[h.excess_spy.notna() & h.excess_control.notna()]
        summaries.append(describe(spy_valid,"all_primary_vs_spy",horizon))
        summaries.append(describe(paired,"matched_primary",horizon))
        for label,start,end in [("1994_2009","1994-01-01","2009-12-31"),("2010_2017","2010-01-01","2017-12-31"),("2018_2026","2018-01-01",str(END.date()))]:
            summaries.append(describe(paired.loc[paired.date.between(start,end)],label,horizon))
    summary = pd.DataFrame(summaries)
    summary.to_csv(out / "summary.csv",index=False)
    primary = f.loc[f.horizon.eq(21) & f.excess_spy.notna() & f.excess_control.notna()]
    intervals = []
    for col in ["excess_spy","excess_control"]:
        for block in [126,252]:
            lo,hi = moving_block_interval(primary,col,block=block)
            intervals.append({"metric":col,"block_sessions":block,"mean":primary[col].mean(),"lower95":lo,"upper95":hi})
    pd.DataFrame(intervals).to_csv(out / "uncertainty.csv",index=False)
    f.assign(year=f.date.dt.year).groupby(["year","horizon"])[["stock_return","spy_return","control_return","excess_spy","excess_control"]].agg(["count","mean"]).to_csv(out / "annual.csv")
    f.groupby(["horizon","status","matched_at_signal","valid_control_count"]).size().rename("count").to_csv(out / "coverage.csv")
    inputs = [seed_path,memberships_path,spy_path,*sorted(raw_root.glob("daily_*.parquet"))]
    manifest = {"study_id":STUDY,"run_id":stamp,"status":"completed_conditional_local_history_study",
                "config":config,"events":offset,"scalar_return_checks":scalar_checks,
                "wrds_repair":"successful isolated pre-1993 high export; incomplete seeds conservatively excluded",
                "pre1993_seed_rows":len(seed),"pre1993_quality_excluded":int(incomplete.sum()),
                "code_sha256":{str(p.relative_to(ROOT)):sha256(p) for p in [Path(__file__),ROOT/"src/ath_breakout/research/signal_study.py"]},
                "protocol_sha256":sha256(ROOT/"research/ath/ATH_SIGNAL_STUDY_PLAN.md"),
                "inputs":[{"path":str(p.relative_to(ROOT)),"sha256":sha256(p)} for p in inputs],
                "limitations":["Conditional quality-selected local-history sample, not all market ATHs",
                               "Pre-1993 maxima queried live; later listing inception not independently reconciled",
                               "Missing/unpriced pre-period vendor rows conservatively excluded; selection may be substantial", "Overlapping/repeated events",
                               "Controls match size and volatility, not sector or past momentum", "Gross arithmetic event returns, no portfolio or alpha estimate",
                               "Chronological checks use previously available history, not untouched OOS"]}
    manifest["artifacts"]={str(p.relative_to(out)):sha256(p) for p in out.rglob("*") if p.is_file()}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print(summary.loc[summary.horizon.eq(21)].to_string(index=False),flush=True)
    print(pd.DataFrame(intervals).to_string(index=False),flush=True)
    print(out,flush=True)


if __name__=="__main__":
    main()
