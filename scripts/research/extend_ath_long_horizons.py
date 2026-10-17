"""Frozen ATH events held for 504/756 sessions; no signal or exit-rule changes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.research.extend_ath_annual import SOURCE, COOLDOWN, END, COLS, sha256, describe  # noqa: E402
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.signal_study import forward_arrays, moving_block_interval  # noqa: E402
from ath_breakout.research.high_breakout import holding_return  # noqa: E402
from ath_breakout.research.long_paths import closing_wealth_paths, wealth_excursions  # noqa: E402

STUDY = "ath_07_long_horizons_v001"
ANNUAL = ROOT / "outputs/research/ath/ath_06_annual_v001/20261015T221839273190Z"
HORIZONS = (504, 756)


def summary(z, label, horizon, period="all"):
    result = describe(z, label, period, horizon)
    result.update({"median_worst_close_loss": z.worst_close_loss.median(),
                   "median_stock_drawdown": z.stock_drawdown.median(),
                   "median_spy_drawdown": z.spy_drawdown.median(),
                   "fraction_stock_drawdown_below_minus50": z.stock_drawdown.le(-.5).mean()})
    return result


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True, exist_ok=False)
    m0 = json.loads((SOURCE / "manifest.json").read_text())
    expected_hashes = {x["path"]: x["sha256"] for x in m0["inputs"]}
    cache, inputs = {}, set()

    def load(year):
        if year not in cache:
            p = ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet"
            assert sha256(p) == expected_hashes[str(p.relative_to(ROOT))]
            cache[year] = pd.read_parquet(p, columns=COLS)
            inputs.add(p)
        return cache[year]

    spy_path = ROOT / "data/raw/yfinance/SPY.parquet"
    assert sha256(spy_path) == expected_hashes[str(spy_path.relative_to(ROOT))]
    spy = pd.read_parquet(spy_path).set_index("date")
    cp = COOLDOWN / "selection.parquet"
    assert sha256(cp) == json.loads((COOLDOWN / "manifest.json").read_text())["artifacts"][cp.name]
    selection = pd.read_parquet(cp).set_index("event_id").retained
    outputs, scalar_checks, path_checks = [], 0, 0
    for year in range(1994, 2027):
        ep, mp = [SOURCE / f"by_year/{kind}_{year}.parquet" for kind in ["events", "matches"]]
        for p in [ep, mp]:
            assert sha256(p) == m0["artifacts"][str(p.relative_to(SOURCE))]
            inputs.add(p)
        events, matches = pd.read_parquet(ep), pd.read_parquet(mp)
        if events.empty:
            continue
        q = pd.concat([events[["event_id", "date", "permno"]].assign(rank=0),
                       matches[["event_id", "date", "permno", "rank"]]], ignore_index=True)
        ids = pd.Index(sorted(q.permno.unique()))
        calendar = valid_nyse_sessions(f"{year}-01-01", f"{year+4}-01-31")
        d = pd.concat([load(y) for y in range(year, min(year+4, 2026)+1)], ignore_index=True)
        d = d.loc[d.permno.isin(ids) & d.date.le(calendar[-1])]
        assert not d.duplicated(["permno", "date"]).any()
        arrays = {n: d.pivot(index="date", columns="permno", values=n).reindex(index=calendar, columns=ids).to_numpy(float)
                  for n in ["open", "close", "total_return"]}
        terminal = d.assign(t=d.delisting_flag.eq("Y")).pivot(index="date", columns="permno", values="t").reindex(
            index=calendar, columns=ids).eq(True).to_numpy(bool)
        entries, cols = calendar.get_indexer(pd.DatetimeIndex(q.date))+1, ids.get_indexer(q.permno)
        sy = spy.reindex(calendar)
        year_outputs = []
        for horizon in HORIZONS:
            values, status, settled = forward_arrays(arrays["open"], arrays["close"], arrays["total_return"], terminal,
                entries, cols, horizon, calendar.searchsorted(END, side="right")-1)
            control = q.assign(value=values).loc[q["rank"].gt(0)].groupby("event_id").value.agg(["mean", "count"])
            er = entries[:len(events)]
            end = er+horizon-1
            with np.errstate(divide="ignore", invalid="ignore"):
                benchmark = sy.close.to_numpy()[er]/sy.open.to_numpy()[er] * sy.adj_close.to_numpy()[end]/sy.adj_close.to_numpy()[er]-1
            r = events[["event_id", "permno", "date"]].copy()
            r["horizon"], r["stock_return"], r["status"] = horizon, values[:len(events)], status[:len(events)]
            r["terminal_cash"], r["spy_return"] = settled[:len(events)], benchmark
            r["entry_date"], r["exit_date"] = calendar[er].to_numpy(), calendar[end].to_numpy()
            r["valid_control_count"] = r.event_id.map(control["count"]).fillna(0).astype(int)
            r["control_return"] = r.event_id.map(control["mean"]).where(r.valid_control_count.eq(5))
            r["excess_spy"], r["excess_control"] = r.stock_return-r.spy_return, r.stock_return-r.control_return
            r["cooldown21"] = r.event_id.map(selection)
            for col in ["worst_close_loss", "stock_drawdown", "spy_drawdown"]:
                r[col] = np.nan
            good = np.flatnonzero((status[:len(events)] == "ok") & np.isfinite(benchmark))
            if len(good):
                wealth = closing_wealth_paths(arrays["open"], arrays["close"], arrays["total_return"], terminal,
                                               er[good], cols[:len(events)][good], horizon)
                assert np.isfinite(wealth).all()
                assert np.allclose(wealth[:, -1]-1, r.stock_return.to_numpy()[good], atol=1e-10, rtol=1e-10)
                worst, drawdown = wealth_excursions(wealth)
                r.loc[r.index[good], "worst_close_loss"] = worst
                r.loc[r.index[good], "stock_drawdown"] = drawdown
                days = er[good, None]+np.arange(horizon)[None, :]
                spy_wealth = (sy.close.to_numpy()[er[good]]/sy.open.to_numpy()[er[good]])[:, None] * (
                    sy.adj_close.to_numpy()[days]/sy.adj_close.to_numpy()[er[good], None])
                assert np.isfinite(spy_wealth).all()
                _, spy_dd = wealth_excursions(spy_wealth)
                r.loc[r.index[good], "spy_drawdown"] = spy_dd
                path_checks += len(good)
            for i in np.linspace(0, len(q)-1, min(5, len(q)), dtype=int):
                if status[i] != "ok":
                    continue
                c = cols[i]
                h = pd.DataFrame({"open": arrays["open"][:, c], "close": arrays["close"][:, c],
                                  "total_return": arrays["total_return"][:, c], "delisting_flag": np.where(terminal[:, c], "Y", "N")})
                expected, state, _ = holding_return(h, entries[i], horizon)
                assert state.startswith("ok") and np.isclose(values[i], expected, atol=1e-10, rtol=1e-10)
                scalar_checks += 1
            year_outputs.append(r)
        year_frame = pd.concat(year_outputs, ignore_index=True)
        year_frame.to_parquet(out / f"by_year/long_{year}.parquet", index=False)
        outputs.append(year_frame)
        cache = {y: f for y, f in cache.items() if y >= year+1}
        print(f"{year}: 2y valid {year_outputs[0].excess_spy.notna().sum():,}; 3y valid {year_outputs[1].excess_spy.notna().sum():,}", flush=True)
    f = pd.concat(outputs, ignore_index=True)
    f.to_parquet(out / "long_returns.parquet", index=False)
    summaries, intervals = [], []
    for horizon in HORIZONS:
        h = f.loc[f.horizon.eq(horizon)]
        for group, z in [("all_spy_valid", h.loc[h.excess_spy.notna()]),
                         ("matched_valid", h.loc[h.excess_spy.notna() & h.excess_control.notna()]),
                         ("cooldown21_spy_valid", h.loc[h.excess_spy.notna() & h.cooldown21])]:
            summaries.append(summary(z, group, horizon))
            if group == "all_spy_valid":
                for label, start, end in [("1994_2009", "1994-01-01", "2009-12-31"),
                                          ("2010_2017", "2010-01-01", "2017-12-31"),
                                          ("2018_2026", "2018-01-01", "2026-06-30")]:
                    summaries.append(summary(z.loc[z.date.between(start, end)], group, horizon, label))
            metric = "excess_control" if group == "matched_valid" else "excess_spy"
            for block in [756, 1512]:
                lo, hi = moving_block_interval(z, metric, block=block)
                intervals.append({"group": group, "horizon": horizon, "metric": metric, "block_sessions": block,
                                  "mean": z[metric].mean(), "lower95": lo, "upper95": hi})
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(intervals).to_csv(out / "uncertainty.csv", index=False)
    old, annual_path = SOURCE / "forward_returns.parquet", ANNUAL / "annual_returns.parquet"
    am = json.loads((ANNUAL / "manifest.json").read_text())
    assert sha256(old) == m0["artifacts"][old.name]
    assert sha256(annual_path) == am["artifacts"][annual_path.name]
    combined = pd.concat([pd.read_parquet(old), pd.read_parquet(annual_path), f], ignore_index=True)
    valid = combined.loc[combined.excess_spy.notna()]
    common_ids = valid.groupby("event_id").horizon.nunique().loc[lambda x: x.eq(7)].index
    common = valid.loc[valid.event_id.isin(common_ids)]
    pd.DataFrame([describe(z, "common_spy_sample", horizon=h) for h, z in common.groupby("horizon")]).to_csv(out / "common_horizons.csv", index=False)
    f.groupby(["horizon", "status", "valid_control_count"]).size().rename("count").to_csv(out / "coverage.csv")
    manifest = {"study_id": STUDY, "run_id": stamp, "status": "completed_descriptive_long_extension",
                "horizons": HORIZONS, "source_events": len(f)//2, "common_events": len(common_ids),
                "scalar_checks": scalar_checks, "closing_path_endpoint_checks": path_checks,
                "protocol_sha256": sha256(ROOT / "research/ath/ATH_LONG_HORIZON_PLAN.md"),
                "source_manifest_sha256": sha256(SOURCE / "manifest.json"),
                "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in [Path(__file__),
                    ROOT / "src/ath_breakout/research/long_paths.py", ROOT / "scripts/research/extend_ath_annual.py"]},
                "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in sorted(inputs | {spy_path, cp, old, annual_path})],
                "limitations": ["Retrospective descriptive extension; primary 21-session test unchanged",
                                "History-quality selection; overlapping/reused events and controls",
                                "Gross cumulative returns, not per-year return or portfolio CAGR",
                                "Terminal proceeds held as cash; no successor holding or capital reuse",
                                "Closing drawdowns are not intraday risk; not evidence of a smooth trend",
                                "No causal alpha or untouched out-of-sample claim"]}
    manifest["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in out.rglob("*") if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(pd.DataFrame(summaries).to_string(index=False))
    print(pd.DataFrame(intervals).to_string(index=False))
    print(out, flush=True)


if __name__ == "__main__":
    main()
