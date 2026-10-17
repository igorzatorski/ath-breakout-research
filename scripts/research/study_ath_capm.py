"""Fixed annual CAPM event diagnostic with old and momentum-matched controls."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.capm_events import capm_event_arrays  # noqa: E402
from ath_breakout.research.signal_study import forward_arrays, moving_block_interval  # noqa: E402
from extend_ath_annual import SOURCE, END, sha256, COLS  # noqa: E402
from fetch_capm_factors import TARGET  # noqa: E402

MOM = ROOT / "outputs/research/ath/ath_08_momentum_control_v001/20261015T224210801657Z"
STUDY = "ath_09_capm_v001"


def summary(z, group, period):
    metrics = ["stock_car", "old_car", "momentum_car", "old_gap", "momentum_gap", "beta", "old_beta", "momentum_beta"]
    return {"group": group, "period": period, "events": len(z), "securities": z.permno.nunique(),
            **{c: z[c].mean() for c in metrics},
            "median_stock_car": z.stock_car.median(), "median_beta": z.beta.median(),
            "equal_security_stock_car": z.groupby("permno").stock_car.mean().mean(),
            "equal_security_gap": z.groupby("permno").momentum_gap.mean().mean(),
            "equal_date_gap": z.groupby("date").momentum_gap.mean().mean()}


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    (out / "by_year").mkdir(parents=True)
    print(out, flush=True)
    mm = json.loads((MOM / "manifest.json").read_text())
    sm = json.loads((SOURCE / "manifest.json").read_text())
    hashes = {i["path"]: i["sha256"] for i in sm["inputs"]}
    inputs = {}

    def checked(path, expected=None):
        h = sha256(path)
        if expected:
            assert h == expected, path
        inputs[str(path.relative_to(ROOT))] = h
        return pd.read_parquet(path)

    original = checked(MOM / "event_returns.parquet", mm["artifacts"]["event_returns.parquet"])
    f = checked(TARGET / "factors.parquet").set_index("date")
    factor_days = valid_nyse_sessions("1993-01-01", END)
    assert f.reindex(factor_days)[["mkt_rf", "rf"]].notna().all().all()
    cache = {}

    def load(year):
        if year not in cache:
            p = ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet"
            h = sha256(p)
            assert h == hashes[str(p.relative_to(ROOT))]
            inputs[str(p.relative_to(ROOT))] = h
            cache[year] = pd.read_parquet(p, columns=COLS)
        return cache[year]

    results, audits, checks = [], [], 0
    for year in range(1994, 2027):
        ev = original.loc[original.date.dt.year.eq(year)].copy()
        oldp = SOURCE / f"by_year/matches_{year}.parquet"
        newp = MOM / f"by_year/matches_{year}.parquet"
        old = checked(oldp, sm["artifacts"][str(oldp.relative_to(SOURCE))])
        new = checked(newp, mm["artifacts"][str(newp.relative_to(MOM))])
        base = ["event_id", "date", "permno"]
        q = pd.concat([ev[base].assign(kind="stock", rank=0), old[base+["rank"]].assign(kind="old"), new[base+["rank"]].assign(kind="momentum")], ignore_index=True)
        unique = q[["date", "permno"]].drop_duplicates().reset_index(drop=True)
        # A calendar year can have fewer than 252 sessions (notably 2001).
        # Two earlier years guarantee room; unavailable raw 1992 stays missing.
        calendar = valid_nyse_sessions(f"{year-2}-01-01", f"{year+2}-01-31")
        selected = pd.Index(sorted(unique.permno.unique()))
        raw = pd.concat([load(y) for y in range(max(1993, year-2), min(year+2, 2026)+1)], ignore_index=True)
        raw = raw.loc[raw.permno.isin(selected) & raw.date.le(calendar[-1])]
        assert not raw.duplicated(["date", "permno"]).any()
        arrays = {c: raw.pivot(index="date", columns="permno", values=c).reindex(index=calendar, columns=selected).to_numpy(float) for c in ["open", "close", "total_return"]}
        term = raw.assign(t=raw.delisting_flag.eq("Y")).pivot(index="date", columns="permno", values="t").reindex(index=calendar, columns=selected).eq(True).to_numpy(bool)
        s = calendar.get_indexer(pd.DatetimeIndex(unique.date))
        c = selected.get_indexer(unique.permno)
        val, state, terminal_cash = forward_arrays(arrays["open"], arrays["close"], arrays["total_return"], term, s+1, c, 252, calendar.searchsorted(END, side="right")-1)
        factors = f.reindex(calendar)
        market, rf = factors.mkt_rf.to_numpy(), factors.rf.to_numpy()
        beta, alpha_pre, observations, car = capm_event_arrays(arrays["total_return"], term, market, rf, s, c, state == "ok")
        uq = unique.assign(beta=beta, pre_intercept=alpha_pre, estimation_count=observations, car=car, stock_return=val, forward_status=state, terminal_cash=terminal_cash)
        uq.to_parquet(out / f"by_year/unique_security_dates_{year}.parquet", index=False)
        for i in np.linspace(0, len(uq)-1, min(8, len(uq)), dtype=int):
            si, ci = s[i], c[i]
            pre = np.arange(si-252, si)
            y = arrays["total_return"][pre, ci]-rf[pre]
            ok = np.isfinite(y) & np.isfinite(market[pre]) & (arrays["total_return"][pre, ci] >= -1)
            assert ok.sum() == observations[i]
            if np.isfinite(beta[i]):
                expected = np.linalg.lstsq(np.column_stack([np.ones(ok.sum()), market[pre][ok]]), y[ok], rcond=None)[0]
                assert np.allclose(expected, [alpha_pre[i], beta[i]], atol=1e-10, rtol=1e-10)
                checks += 1
            if np.isfinite(car[i]):
                total = 0.
                after = False
                for t in range(si+2, si+253):
                    rr = 0. if after else arrays["total_return"][t, ci]
                    total += rr-rf[t]-(0. if after else beta[i]*market[t])
                    after = after or bool(term[t, ci])
                assert np.isclose(total, car[i], atol=1e-10, rtol=1e-10)
                checks += 1
        q = q.merge(uq, on=["date", "permno"], how="left", validate="many_to_one")
        q.to_parquet(out / f"by_year/query_results_{year}.parquet", index=False)
        stock = q.loc[q.kind.eq("stock")].set_index("event_id")
        ev = ev.set_index("event_id")
        assert np.allclose(ev.stock_return, stock.stock_return.reindex(ev.index), equal_nan=True, atol=1e-10, rtol=1e-10)
        ev["beta"] = stock.beta
        ev["beta_n"] = stock.estimation_count
        ev["stock_car"] = stock.car
        for kind in ["old", "momentum"]:
            ctr = q.loc[q.kind.eq(kind)]
            valid_count = ctr.groupby("event_id").car.count()
            ev[f"{kind}_valid_controls"] = valid_count.reindex(ev.index).fillna(0).astype(int)
            ev[f"{kind}_car"] = ctr.groupby("event_id").car.mean().reindex(ev.index).where(ev[f"{kind}_valid_controls"].eq(5))
            ev[f"{kind}_beta"] = ctr.groupby("event_id").beta.mean().reindex(ev.index).where(ev[f"{kind}_valid_controls"].eq(5))
            ev[f"{kind}_gap"] = ev.stock_car-ev[f"{kind}_car"]
            # Reconcile the new controls with the previously validated annual basket.
            if kind == "momentum":
                gross = ctr.groupby("event_id").stock_return.agg(["mean", "count"])
                expected = gross["mean"].where(gross["count"].eq(5)).reindex(ev.index)
                assert np.allclose(expected, ev.new_control_return, equal_nan=True, atol=1e-10, rtol=1e-10)
        ev = ev.reset_index()
        ev.to_parquet(out / f"by_year/event_results_{year}.parquet", index=False)
        results.append(ev)
        audit = {"year": year, "events": len(ev), "valid_annual_stock": int(ev.stock_return.notna().sum()), "valid_beta": int(ev.beta.notna().sum()), "stock_car": int(ev.stock_car.notna().sum()), "common": int((ev.old_gap.notna() & ev.momentum_gap.notna()).sum())}
        audits.append(audit)
        print(audit, flush=True)
        cache = {y: v for y, v in cache.items() if y >= year-1}
    result = pd.concat(results, ignore_index=True)
    assert len(result) == 75884 and not result.event_id.duplicated().any()
    result.to_parquet(out / "event_results.parquet", index=False)
    pd.DataFrame(audits).to_csv(out / "coverage.csv", index=False)
    common = result.loc[result.old_gap.notna() & result.momentum_gap.notna()]
    samples = [("stock_available", result.loc[result.stock_car.notna()]), ("old_pairs", result.loc[result.old_gap.notna()]), ("momentum_pairs", result.loc[result.momentum_gap.notna()]), ("common", common), ("common_cooldown21", common.loc[common.cooldown21])]
    summaries = []
    for group, z in samples:
        for period, lo, hi in [("all", "1994-01-01", "2026-06-30"), ("1994_2009", "1994-01-01", "2009-12-31"), ("2010_2017", "2010-01-01", "2017-12-31"), ("2018_2025", "2018-01-01", "2026-06-30")]:
            summaries.append(summary(z.loc[z.date.between(lo, hi)], group, period))
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
    common.assign(year=common.date.dt.year).groupby("year").agg(events=("event_id", "size"), stock_car=("stock_car", "mean"), old_car=("old_car", "mean"), momentum_car=("momentum_car", "mean"), old_gap=("old_gap", "mean"), momentum_gap=("momentum_gap", "mean"), beta=("beta", "mean")).to_csv(out / "annual.csv")
    intervals = []
    for group, z in [("stock_available", samples[0][1]), ("common", common), ("common_cooldown21", common.loc[common.cooldown21])]:
        for metric in (["stock_car"] if group == "stock_available" else ["stock_car", "old_gap", "momentum_gap"]):
            for block in [252, 504]:
                low, high = moving_block_interval(z, metric, block=block)
                intervals.append({"group": group, "metric": metric, "block": block, "mean": z[metric].mean(), "lower95": low, "upper95": high})
    pd.DataFrame(intervals).to_csv(out / "uncertainty.csv", index=False)
    meta = {"study_id": STUDY, "run_id": stamp, "status": "completed_retrospective_capm_car", "events": len(result), "common_events": len(common), "scalar_checks": checks, "post_full_sessions": 251, "beta_sessions": 252, "beta_min_valid": 200,
            "inputs": inputs, "factor_download": json.loads((TARGET / "download.json").read_text()), "protocol_sha256": sha256(ROOT / "research/ath/ATH_CAPM_PLAN.md"),
            "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in [Path(__file__), ROOT / "src/ath_breakout/research/capm_events.py"]}}
    meta["artifacts"] = {str(p.relative_to(out)): sha256(p) for p in out.rglob("*") if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(meta, indent=2))
    print(pd.DataFrame(summaries).to_string(index=False), flush=True)
    print(pd.DataFrame(intervals).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
