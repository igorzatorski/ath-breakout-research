"""Rebuild frozen eligible pools; test incremental annual ATH information."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.momentum_controls import lagged_momentum, match_momentum_controls  # noqa: E402
from ath_breakout.research.signal_study import forward_arrays, match_controls, moving_block_interval  # noqa: E402
from ath_breakout.research.high_breakout import holding_return  # noqa: E402
from study_ath_signal import bounds, COLS  # noqa: E402
from extend_ath_annual import SOURCE, END, sha256  # noqa: E402

ANNUAL = ROOT / "outputs/research/ath/ath_06_annual_v001/20261015T221839273190Z"
STUDY = "ath_08_momentum_control_v001"


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True)
    print(out, flush=True)
    manifest0 = json.loads((SOURCE / "manifest.json").read_text())
    hashes = {i["path"]: i["sha256"] for i in manifest0["inputs"]}
    inputs = {}

    def checked(path, expected):
        h = sha256(path)
        assert h == expected, path
        inputs[str(path.relative_to(ROOT))] = h
        return pd.read_parquet(path)

    am = json.loads((ANNUAL / "manifest.json").read_text())
    annual = checked(ANNUAL / "annual_returns.parquet", am["artifacts"]["annual_returns.parquet"])
    mp = ROOT / "data/processed/crsp/universe_memberships.parquet"
    membership = checked(mp, hashes[str(mp.relative_to(ROOT))])
    formation = membership[["effective_date", "formation_date"]].drop_duplicates().sort_values("effective_date")
    keys = pd.MultiIndex.from_frame(membership[["effective_date", "permno"]])
    sp = ROOT / "outputs/research/ath/shared_inputs/high_seed_before_1993.parquet"
    seed = checked(sp, hashes[str(sp.relative_to(ROOT))])
    hv = np.isfinite(seed.prior_comparable_high) & seed.prior_comparable_high.gt(0)
    bound = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    prior = dict(zip(seed.loc[np.isfinite(bound), "permno"], bound[np.isfinite(bound)]))
    legacy = set(seed.loc[~hv | seed.missing_high_rows.gt(0) | seed.prior_comparable_high.lt(seed.prior_comparable_close), "permno"])
    gaps, cache = set(), {}

    def load(year):
        if year not in cache:
            path = ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet"
            # Read only research columns, but verify the full source hash once.
            h = sha256(path)
            assert h == hashes[str(path.relative_to(ROOT))]
            inputs[str(path.relative_to(ROOT))] = h
            cache[year] = pd.read_parquet(path, columns=COLS)
        return cache[year]

    all_results, all_balance, audits = [], [], []
    checks = 0
    tail = None
    for year in range(1993, 2027):
        d = load(year).sort_values(["permno", "date"]).reset_index(drop=True).copy()
        close, high, observed, bad = bounds(d)
        d["adjusted_close"], d["adjusted_high"], d["observed_bound"] = close, high, observed
        cumulative = d.groupby("permno").observed_bound.cummax().groupby(d.permno).ffill()
        d["prior_ath"] = np.fmax(cumulative.groupby(d.permno).shift(), d.permno.map(prior))
        pb = bad.groupby(d.permno).cummax().groupby(d.permno).shift(fill_value=False)
        d["history_uncertain"] = d.permno.isin(legacy) | d.permno.isin(gaps) | pb
        if year >= 1994:
            ep, bp = [SOURCE / f"by_year/{name}_{year}.parquet" for name in ["events", "matches"]]
            events = checked(ep, manifest0["artifacts"][str(ep.relative_to(SOURCE))])
            old_matches = checked(bp, manifest0["artifacts"][str(bp.relative_to(SOURCE))])
            lb = pd.concat([tail, d[["permno", "date", "close", "volume", "total_return"]]], ignore_index=True)
            cal = valid_nyse_sessions(f"{year-1}-01-01", f"{year}-12-31")
            rr = lb.total_return.where(np.isfinite(lb.total_return) & lb.total_return.ge(-1))
            rets = lb.assign(rr=rr).pivot(index="date", columns="permno", values="rr").reindex(cal)
            vol = rets.rolling(63, min_periods=63).std()*np.sqrt(252)
            mom = lagged_momentum(rets)
            dv = (lb.close*lb.volume).where(np.isfinite(lb.close) & lb.close.gt(0) & np.isfinite(lb.volume) & lb.volume.ge(0))
            adv = lb.assign(dv=dv).pivot(index="date", columns="permno", values="dv").reindex(cal).rolling(21, min_periods=21).mean()
            idx = pd.MultiIndex.from_frame(d[["date", "permno"]])
            for name, arr in [("adv21", adv), ("vol63", vol), ("momentum", mom)]:
                d[name] = arr.stack().reindex(idx).to_numpy()
            del lb, rets, vol, mom, adv
            dm = pd.merge_asof(pd.DataFrame({"date": sorted(d.date.unique())}), formation, left_on="date", right_on="effective_date", direction="backward")
            d = d.merge(dm, on="date", how="left", validate="many_to_one")
            member = pd.MultiIndex.from_frame(d[["effective_date", "permno"]]).isin(keys)
            eligible = member & d.adv21.ge(1e7) & d.adjusted_close.notna() & d.prior_ath.notna()
            quality = ~d.history_uncertain & d.adjusted_high.notna()
            signal = d.adjusted_close.gt(d.prior_ath)
            reconstructed = d.loc[eligible & quality & signal]
            assert set(zip(reconstructed.date, reconstructed.permno)) == set(zip(events.date, events.permno))
            features = d.set_index(["date", "permno"])
            eventidx = pd.MultiIndex.from_frame(events[["date", "permno"]])
            for col in ["market_cap", "vol63", "adv21", "prior_ath"]:
                assert np.allclose(events[col], features[col].reindex(eventidx), equal_nan=True, rtol=1e-9)
            events["momentum"] = features.momentum.reindex(eventidx).to_numpy()
            events[["event_id", "date", "permno", "momentum"]].to_parquet(out / f"by_year/features_{year}.parquet", index=False)
            pool = d.loc[eligible & quality & ~signal & d.market_cap.gt(0) & np.isfinite(d.market_cap) & d.vol63.gt(0) & np.isfinite(d.vol63)]
            pools = dict(tuple(pool.groupby("date")))
            match_rows, balance_rows = [], []
            for date, ev in events.groupby("date", sort=True):
                ev = ev.loc[ev.market_cap.gt(0) & np.isfinite(ev.market_cap) & ev.vol63.gt(0) & np.isfinite(ev.vol63)]
                controls = pools.get(date, pool.iloc[:0])
                original = match_controls(ev, controls)
                old = old_matches.loc[old_matches.date.eq(date)]
                expected = {int(i): z.sort_values("rank").permno.astype(int).tolist() for i, z in old.groupby("event_id")}
                for e in ev.itertuples():
                    assert original.get(e.permno, []) == expected.get(e.event_id, [])
                new = match_momentum_controls(ev, controls)
                by_id = controls.set_index("permno")
                for e in ev.itertuples():
                    for kind, selected in [("old", original.get(e.permno, [])), ("momentum", new.get(e.permno, []))]:
                        for rank, p in enumerate(selected, 1):
                            c = by_id.loc[p]
                            row = {"event_id": e.event_id, "date": date, "permno": p, "rank": rank,
                                   "event_permco": e.permco, "control_permco": c.permco,
                                   "event_momentum": e.momentum, "control_momentum": c.momentum,
                                   "momentum_gap": c.momentum-e.momentum,
                                   "size_ratio": c.market_cap/e.market_cap, "vol_ratio": c.vol63/e.vol63}
                            balance_rows.append(dict(row, kind=kind))
                            if kind == "momentum":
                                match_rows.append(row)
            columns = ["event_id", "date", "permno", "rank", "event_permco", "control_permco", "event_momentum", "control_momentum", "momentum_gap", "size_ratio", "vol_ratio"]
            matches = pd.DataFrame(match_rows, columns=columns)
            matches.to_parquet(out / f"by_year/matches_{year}.parquet", index=False)
            balance = pd.DataFrame(balance_rows, columns=columns+["kind"])
            all_balance.append(balance)
            r = annual.loc[annual.date.dt.year.eq(year)].copy()
            assert set(r.event_id) == set(events.event_id)
            r["momentum"] = r.event_id.map(events.set_index("event_id").momentum)
            r["new_matched_at_signal"] = r.event_id.isin(matches.event_id)
            r["new_valid_controls"] = 0
            r["new_control_return"] = np.nan
            if len(matches):
                selected = pd.Index(sorted(matches.permno.unique()))
                calendar = valid_nyse_sessions(f"{year}-01-01", f"{year+2}-01-31")
                source = pd.concat([load(y) for y in range(year, min(year+2, 2026)+1)], ignore_index=True)
                source = source.loc[source.permno.isin(selected) & source.date.le(calendar[-1])]
                arrays = {n: source.pivot(index="date", columns="permno", values=n).reindex(index=calendar, columns=selected).to_numpy(float) for n in ["open", "close", "total_return"]}
                term = source.assign(t=source.delisting_flag.eq("Y")).pivot(index="date", columns="permno", values="t").reindex(index=calendar, columns=selected).eq(True).to_numpy(bool)
                entries = calendar.get_indexer(pd.DatetimeIndex(matches.date))+1
                cols = selected.get_indexer(matches.permno)
                value, status, terminal = forward_arrays(arrays["open"], arrays["close"], arrays["total_return"], term, entries, cols, 252, calendar.searchsorted(END, side="right")-1)
                q = matches.assign(value=value, status=status, terminal_cash=terminal)
                q.to_parquet(out / f"by_year/control_returns_{year}.parquet", index=False)
                means = q.groupby("event_id").value.agg(["count", "mean"])
                r["new_valid_controls"] = r.event_id.map(means["count"]).fillna(0).astype(int)
                r["new_control_return"] = r.event_id.map(means["mean"]).where(r.new_valid_controls.eq(5))
                for i in np.linspace(0, len(q)-1, min(6, len(q)), dtype=int):
                    if status[i] != "ok":
                        continue
                    c = cols[i]
                    h = pd.DataFrame({n: arrays[n][:, c] for n in arrays})
                    h["delisting_flag"] = np.where(term[:, c], "Y", "N")
                    v, state, _ = holding_return(h, entries[i], 252)
                    assert state.startswith("ok") and np.isclose(v, value[i], atol=1e-10, rtol=1e-10)
                    checks += 1
            r["new_excess"] = r.stock_return-r.new_control_return
            r["change"] = r.new_excess-r.excess_control
            r.to_parquet(out / f"by_year/events_returns_{year}.parquet", index=False)
            all_results.append(r)
            audits.append({"year": year, "events": len(events), "momentum_available": int(events.momentum.notna().sum()), "matched_at_signal": int(matches.event_id.nunique()), "new_valid_pairs": int((r.new_excess.notna() & r.excess_spy.notna()).sum())})
            print(audits[-1], flush=True)
            del features, pool, pools, reconstructed, balance
        _, _, observed, bad = bounds(d)
        for p, h in pd.Series(observed, index=d.index).groupby(d.permno).max().dropna().items():
            prior[p] = max(prior.get(p, h), h)
        gaps.update(d.loc[bad, "permno"].unique())
        tail = d[["permno", "date", "close", "volume", "total_return"]].copy()
        cache = {k: v for k, v in cache.items() if k > year}
    result = pd.concat(all_results, ignore_index=True)
    result.to_parquet(out / "event_returns.parquet", index=False)
    balance = pd.concat(all_balance, ignore_index=True)
    balance.to_parquet(out / "match_balance.parquet", index=False)
    pd.DataFrame(audits).to_csv(out / "coverage.csv", index=False)
    new = result.loc[result.new_excess.notna() & result.excess_spy.notna()]
    common = new.loc[new.excess_control.notna()]
    assert not result.event_id.duplicated().any() and len(result) == 75884
    assert balance.loc[balance.kind.eq("momentum"), "momentum_gap"].abs().le(.1+1e-12).all()
    summaries = []
    for group, z in [("new_available", new), ("common", common), ("common_cooldown21", common.loc[common.cooldown21])]:
        for period, start, end in [("all", "1994-01-01", "2026-06-30"), ("1994_2009", "1994-01-01", "2009-12-31"), ("2010_2017", "2010-01-01", "2017-12-31"), ("2018_2025", "2018-01-01", "2026-06-30")]:
            p = z.loc[z.date.between(start, end)]
            summaries.append({"group": group, "period": period, "events": len(p), "securities": p.permno.nunique(),
                              **{c: p[c].mean() for c in ["stock_return", "spy_return", "control_return", "new_control_return", "excess_spy", "excess_control", "new_excess", "change"]},
                              "equal_security_new_excess": p.groupby("permno").new_excess.mean().mean(), "equal_date_new_excess": p.groupby("date").new_excess.mean().mean()})
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
    common.assign(year=common.date.dt.year).groupby("year").agg(events=("event_id", "size"), stock=("stock_return", "mean"), spy=("spy_return", "mean"), old_excess=("excess_control", "mean"), new_excess=("new_excess", "mean"), change=("change", "mean")).to_csv(out / "annual.csv")
    intervals = []
    for group, z in [("common", common), ("common_cooldown21", common.loc[common.cooldown21])]:
        for c in ["excess_control", "new_excess", "change"]:
            for block in [252, 504]:
                lo, hi = moving_block_interval(z, c, block=block)
                intervals.append({"group": group, "metric": c, "block": block, "mean": z[c].mean(), "lower95": lo, "upper95": hi})
    pd.DataFrame(intervals).to_csv(out / "uncertainty.csv", index=False)
    b = balance.loc[balance.event_id.isin(common.event_id)].copy()
    b["abs_momentum_gap"] = b.momentum_gap.abs()
    b.groupby("kind")[["event_momentum", "control_momentum", "momentum_gap", "abs_momentum_gap"]].agg(["count", "mean", "median"]).to_csv(out / "balance.csv")
    metadata = {"study_id": STUDY, "run_id": stamp, "events": len(result), "common_events": len(common), "scalar_checks": checks,
                "protocol_sha256": sha256(ROOT / "research/ath/ATH_MOMENTUM_CONTROL_PLAN.md"), "inputs": inputs,
                "code": {str(p.relative_to(ROOT)): sha256(p) for p in [Path(__file__), ROOT / "src/ath_breakout/research/momentum_controls.py"]}}
    metadata["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in out.rglob("*") if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(metadata, indent=2))
    print(pd.DataFrame(summaries).to_string(index=False), flush=True)
    print(pd.DataFrame(intervals).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
