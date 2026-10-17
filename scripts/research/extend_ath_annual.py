"""Add 252-session returns to frozen ATH events, using local CRSP observations."""
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
from ath_breakout.research.signal_study import forward_arrays, moving_block_interval  # noqa: E402

SOURCE = ROOT / "outputs/research/ath/ath_04_signal_matched_v002/20261015T214148297829Z"
COOLDOWN = ROOT / "outputs/research/ath/ath_05_cooldown21_v001/20261015T220442543623Z"
STUDY = "ath_06_annual_v001"
END = pd.Timestamp("2026-06-30")
COLS = ["permno", "date", "open", "close", "total_return", "delisting_flag"]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(z, group, period="all", horizon=252):
    return {"group": group, "period": period, "horizon": horizon, "events": len(z),
            "securities": z.permno.nunique(), "mean_stock": z.stock_return.mean(),
            "median_stock": z.stock_return.median(), "mean_spy": z.spy_return.mean(),
            "mean_excess_spy": z.excess_spy.mean(), "median_excess_spy": z.excess_spy.median(),
            "mean_controls": z.control_return.mean(), "mean_excess_controls": z.excess_control.mean(),
            "equal_security_excess_spy": z.groupby("permno").excess_spy.mean().mean(),
            "equal_date_excess_spy": z.groupby("date").excess_spy.mean().mean(),
            "loss_fraction": z.stock_return.lt(0).mean(), "q05_stock": z.stock_return.quantile(.05),
            "q95_stock": z.stock_return.quantile(.95)}


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True, exist_ok=False)
    manifest0 = json.loads((SOURCE / "manifest.json").read_text())
    source_hashes = {x["path"]: x["sha256"] for x in manifest0["inputs"]}
    raw_root = ROOT / "data/raw/crsp/daily_by_year"
    cache = {}
    inputs = set()

    def load(year):
        if year not in cache:
            path = raw_root / f"daily_{year}.parquet"
            assert sha256(path) == source_hashes[str(path.relative_to(ROOT))]
            cache[year] = pd.read_parquet(path, columns=COLS)
            inputs.add(path)
        return cache[year]

    spy_path = ROOT / "data/raw/yfinance/SPY.parquet"
    assert sha256(spy_path) == source_hashes[str(spy_path.relative_to(ROOT))]
    spy = pd.read_parquet(spy_path).set_index("date")
    selection_path = COOLDOWN / "selection.parquet"
    cm = json.loads((COOLDOWN / "manifest.json").read_text())
    assert sha256(selection_path) == cm["artifacts"][selection_path.name]
    selection = pd.read_parquet(selection_path).set_index("event_id").retained
    results, checks = [], 0
    for year in range(1994, 2027):
        ep = SOURCE / f"by_year/events_{year}.parquet"
        mp = SOURCE / f"by_year/matches_{year}.parquet"
        for p in [ep, mp]:
            assert sha256(p) == manifest0["artifacts"][str(p.relative_to(SOURCE))]
            inputs.add(p)
        events, matches = pd.read_parquet(ep), pd.read_parquet(mp)
        if events.empty:
            continue
        queries = pd.concat([events[["event_id", "date", "permno"]].assign(rank=0),
                             matches[["event_id", "date", "permno", "rank"]]], ignore_index=True)
        selected = pd.Index(sorted(queries.permno.unique()))
        calendar = valid_nyse_sessions(f"{year}-01-01", f"{year+2}-01-31")
        source = pd.concat([load(y) for y in range(year, min(year+2, 2026)+1)], ignore_index=True)
        source = source.loc[source.permno.isin(selected) & source.date.le(calendar[-1])]
        assert not source.duplicated(["permno", "date"]).any()
        arrays = {name: source.pivot(index="date", columns="permno", values=name).reindex(
            index=calendar, columns=selected).to_numpy(float) for name in ["open", "close", "total_return"]}
        terminal = source.assign(t=source.delisting_flag.eq("Y")).pivot(index="date", columns="permno", values="t").reindex(
            index=calendar, columns=selected).eq(True).to_numpy(bool)
        entries = calendar.get_indexer(pd.DatetimeIndex(queries.date))+1
        columns = selected.get_indexer(queries.permno)
        available = calendar.searchsorted(END, side="right")-1
        value, status, terminal_hit = forward_arrays(arrays["open"], arrays["close"], arrays["total_return"],
                                                    terminal, entries, columns, 252, available)
        q = queries.assign(value=value)
        event_values = q.loc[q["rank"].eq(0)]
        controls = q.loc[q["rank"].gt(0)].groupby("event_id").value.agg(["mean", "count"])
        er = entries[:len(events)]
        end = er+251
        sy = spy.reindex(calendar)
        with np.errstate(divide="ignore", invalid="ignore"):
            benchmark = sy.close.to_numpy()[er]/sy.open.to_numpy()[er] * sy.adj_close.to_numpy()[end]/sy.adj_close.to_numpy()[er]-1
        r = events[["event_id", "permno", "date"]].copy()
        r["horizon"] = 252
        r["stock_return"] = event_values.value.to_numpy()
        r["status"] = status[:len(events)]
        r["terminal_cash"] = terminal_hit[:len(events)]
        r["spy_return"] = benchmark
        r["entry_date"] = calendar[er].to_numpy()
        r["exit_date"] = calendar[end].to_numpy()
        r["valid_control_count"] = r.event_id.map(controls["count"]).fillna(0).astype(int)
        r["control_return"] = r.event_id.map(controls["mean"]).where(r.valid_control_count.eq(5))
        r["excess_spy"] = r.stock_return-r.spy_return
        r["excess_control"] = r.stock_return-r.control_return
        r["cooldown21"] = r.event_id.map(selection)
        assert r.cooldown21.notna().all()
        r.to_parquet(out / f"by_year/annual_{year}.parquet", index=False)
        results.append(r)
        for i in np.linspace(0, len(queries)-1, min(6, len(queries)), dtype=int):
            if status[i] != "ok":
                continue
            col = columns[i]
            h = pd.DataFrame({"open": arrays["open"][:, col], "close": arrays["close"][:, col],
                              "total_return": arrays["total_return"][:, col],
                              "delisting_flag": np.where(terminal[:, col], "Y", "N")})
            expected, state, _ = holding_return(h, entries[i], 252)
            assert state.startswith("ok") and np.isclose(value[i], expected, atol=1e-10, rtol=1e-10)
            checks += 1
        cache = {k: v for k, v in cache.items() if k >= year+1}
        print(f"{year}: {len(r):,} events; {r.excess_spy.notna().sum():,} valid annual SPY pairs", flush=True)
    annual = pd.concat(results, ignore_index=True)
    annual.to_parquet(out / "annual_returns.parquet", index=False)
    summaries = []
    for group, z in [("all_spy_valid", annual.loc[annual.excess_spy.notna()]),
                     ("matched_valid", annual.loc[annual.excess_spy.notna() & annual.excess_control.notna()]),
                     ("cooldown21_spy_valid", annual.loc[annual.excess_spy.notna() & annual.cooldown21]),
                     ("cooldown21_matched", annual.loc[annual.excess_spy.notna() & annual.excess_control.notna() & annual.cooldown21])]:
        summaries.append(describe(z, group))
        if group == "all_spy_valid":
            for label, start, end in [("1994_2009", "1994-01-01", "2009-12-31"),
                                      ("2010_2017", "2010-01-01", "2017-12-31"),
                                      ("2018_2026", "2018-01-01", "2026-06-30")]:
                summaries.append(describe(z.loc[z.date.between(start, end)], group, label))
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
    old_path = SOURCE / "forward_returns.parquet"
    assert sha256(old_path) == manifest0["artifacts"][old_path.name]
    old = pd.read_parquet(old_path)
    combined = pd.concat([old, annual], ignore_index=True)
    valid = combined.loc[combined.excess_spy.notna()]
    common_ids = valid.groupby("event_id").horizon.nunique().loc[lambda x: x.eq(5)].index
    common = valid.loc[valid.event_id.isin(common_ids)]
    common_summary = [describe(z, "common_spy_sample", horizon=h) for h, z in common.groupby("horizon")]
    pd.DataFrame(common_summary).to_csv(out / "common_horizons.csv", index=False)
    intervals = []
    for group, z in [("all_spy_valid", annual.loc[annual.excess_spy.notna()]),
                     ("matched_valid", annual.loc[annual.excess_control.notna() & annual.excess_spy.notna()]),
                     ("cooldown21_spy_valid", annual.loc[annual.excess_spy.notna() & annual.cooldown21])]:
        metrics = ["excess_control"] if group == "matched_valid" else ["excess_spy"]
        for metric in metrics:
            for block in [252, 504]:
                lo, hi = moving_block_interval(z, metric, block=block)
                intervals.append({"group": group, "metric": metric, "block_sessions": block,
                                  "mean": z[metric].mean(), "lower95": lo, "upper95": hi})
    pd.DataFrame(intervals).to_csv(out / "uncertainty.csv", index=False)
    annual.groupby(["status", "valid_control_count"]).size().rename("count").to_csv(out / "coverage.csv")
    manifest = {"study_id": STUDY, "run_id": stamp, "status": "completed_descriptive_annual_extension",
                "horizon": 252, "data_end": str(END.date()), "source_events": len(annual),
                "common_horizon_events": len(common_ids), "scalar_checks": checks,
                "source_manifest_sha256": sha256(SOURCE / "manifest.json"),
                "protocol_sha256": sha256(ROOT / "research/ath/ATH_ANNUAL_PLAN.md"),
                "script_sha256": sha256(Path(__file__)),
                "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)}
                           for p in sorted(inputs | {spy_path, old_path, selection_path})],
                "limitations": ["Retrospective extension after shorter horizons inspected; 21-session primary unchanged",
                                "Conditional quality-selected population, not all market ATHs", "Repeated/overlapping annual windows",
                                "Gross arithmetic event means, not portfolio CAGR or risk-adjusted alpha",
                                "Late signals censored at fixed data coverage; reused controls and firms remain dependent"]}
    manifest["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in out.rglob("*") if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(pd.DataFrame(summaries).to_string(index=False))
    print(pd.DataFrame(intervals).to_string(index=False))
    print(out, flush=True)


if __name__ == "__main__":
    main()
