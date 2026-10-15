"""Three frozen exit families on the SAME qualified 2024 ATH entries."""
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
from ath_breakout.research.exit_rules import (  # noqa: E402
    signal_atr, simulate_exit, matched_spy_return,
)

STUDY = "high_03_exit_families_pilot_v001"
SOURCE = ROOT / "outputs/research/high_breakouts/high_01_52w_vs_ath_pilot_v001/20261015T205046302698Z"
RULES = ("hold_126", "failed_breakout", "atr_trend")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/high_breakouts/{STUDY}/{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    protocol = ROOT / "research/ath/EXIT_PILOT_PLAN.md"
    config = {"study_id": STUDY, "group": "ath_local_history", "signal_year": 2024,
              "rules": RULES, "max_holding_sessions": 126, "atr_simple_mean_window": 20,
              "initial_atr_multiple": 2, "trailing_atr_multiple": 3,
              "atr_basis": "frozen_at_signal_close", "trigger": "closing_price_strictly_below_level",
              "fill": "next_exchange_session_observed_open", "cost_bps_each_side": 10,
              "source_run": str(SOURCE.relative_to(ROOT)), "parameter_search": False}
    (out / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    source_manifest = json.loads((SOURCE / "manifest.json").read_text())
    for name in ["events.parquet", "forward_returns.parquet"]:
        assert sha256(SOURCE / name) == source_manifest["artifacts"][name]
    all_events = pd.read_parquet(SOURCE / "events.parquet")
    all_events["event_id"] = all_events.index
    events = all_events.loc[all_events.group.eq("ath_local_history")].copy()
    forward = pd.read_parquet(SOURCE / "forward_returns.parquet")
    baseline = forward.loc[forward.horizon.eq(126)].set_index("event_id")
    source_hashes = {s["path"]: s["sha256"] for s in source_manifest["inputs"]}
    raw_paths = [ROOT / f"data/raw/crsp/daily_by_year/daily_{y}.parquet" for y in [2023, 2024, 2025]]
    for path in raw_paths:
        assert sha256(path) == source_hashes[str(path.relative_to(ROOT))]
    columns = ["permno", "date", "open", "high", "low", "close", "price_adjustment_factor",
               "total_return", "delisting_flag", "ordinary_dividend", "nonordinary_dividend"]
    daily = pd.concat([pd.read_parquet(p, columns=columns) for p in raw_paths], ignore_index=True)
    daily.date = pd.to_datetime(daily.date)
    daily = daily.loc[daily.permno.isin(events.permno) & daily.date.ge("2023-11-01")]
    assert not daily.duplicated(["permno", "date"]).any()
    sessions = valid_nyse_sessions("2023-11-01", "2025-12-31")
    histories = {p: g.set_index("date").reindex(sessions) for p, g in daily.groupby("permno")}
    atrs = {p: signal_atr(g) for p, g in histories.items()}
    spy_path = ROOT / "data/raw/yfinance/SPY.parquet"
    assert sha256(spy_path) == source_hashes[str(spy_path.relative_to(ROOT))]
    spy = pd.read_parquet(spy_path).set_index("date").reindex(sessions)
    records = []
    for n, event in enumerate(events.itertuples()):
        start = sessions.get_loc(event.entry_date)
        window = histories[event.permno].iloc[start:start+126]
        assert len(window) == 126
        atr = atrs[event.permno].loc[event.date]
        spy_window = spy.iloc[start:start+126]
        for rule in RULES:
            result = simulate_exit(window, rule, event.prior_ath_local, atr)
            result.update({"event_id": event.event_id, "permno": event.permno, "ticker": event.ticker,
                           "signal_date": event.date, "entry_date": event.entry_date, "rule": rule,
                           "signal_atr": atr, "baseline_gross_return": baseline.loc[event.event_id, "return"],
                           "spy_full126": baseline.loc[event.event_id, "spy_return"]})
            if result["status"] == "ok":
                exit_i = result["exit_index"]
                result["exit_date"] = sessions[start+exit_i]
                result["spy_matched_window"] = matched_spy_return(spy_window, exit_i, result["exit_reason"])
                result["net_excess_full126"] = result["net_return"] - result["spy_full126"]
                result["net_excess_matched"] = result["net_return"] - result["spy_matched_window"]
                result["atr_entry_fraction"] = atr / (window.open.iloc[0] / window.price_adjustment_factor.iloc[0])
                if rule == "hold_126":
                    assert np.isclose(result["gross_return"], result["baseline_gross_return"], atol=1e-12)
            records.append(result)
        if n and n % 1000 == 0:
            print(f"Exit comparisons: {n}/{len(events)}", flush=True)
    results = pd.DataFrame(records)
    results.to_parquet(out / "all_results.parquet", index=False)
    results.groupby(["rule", "status"]).size().rename("events").to_csv(out / "coverage.csv")
    valid_count = results.assign(valid=results.status.eq("ok")).groupby("event_id").valid.sum()
    common = valid_count.index[valid_count.eq(3)]
    paired = results.loc[results.event_id.isin(common)].copy()
    paired.to_csv(out / "paired_events.csv", index=False)
    base = paired.loc[paired.rule.eq("hold_126")].set_index("event_id")
    summary = []
    for rule, z in paired.groupby("rule", sort=False):
        big = z.loc[z.baseline_gross_return.ge(.2)]
        losers = z.loc[z.baseline_gross_return.lt(0)]
        delta = z.net_return - z.event_id.map(base.net_return)
        summary.append({"rule": rule, "events": len(z), "securities": z.permno.nunique(),
                        "mean_gross": z.gross_return.mean(), "mean_net": z.net_return.mean(),
                        "median_net": z.net_return.median(), "loss_frequency_net": z.net_return.lt(0).mean(),
                        "p05_net": z.net_return.quantile(.05), "p01_net": z.net_return.quantile(.01),
                        "mean_win_net": z.loc[z.net_return.gt(0), "net_return"].mean(),
                        "mean_loss_net": z.loc[z.net_return.lt(0), "net_return"].mean(),
                        "big_gain20_net_fraction": z.net_return.ge(.2).mean(),
                        "mean_holding_sessions": z.holding_sessions.mean(), "median_holding_sessions": z.holding_sessions.median(),
                        "mean_net_excess_full126": z.net_excess_full126.mean(),
                        "mean_spy_matched_window": z.spy_matched_window.mean(),
                        "mean_net_excess_matched": z.net_excess_matched.mean(),
                        "equal_security_mean_net": z.groupby("permno").net_return.mean().mean(),
                        "equal_security_net_excess_matched": z.groupby("permno").net_excess_matched.mean().mean(),
                        "mean_paired_delta_vs_hold": delta.mean(), "fraction_better_than_hold": delta.gt(1e-12).mean(),
                        "baseline_big_winners": len(big), "baseline_big_winners_kept_gross20": int(big.gross_return.ge(.2).sum()),
                        "baseline_big_winners_mean_net": big.net_return.mean(),
                        "baseline_losers_mean_net": losers.net_return.mean()})
    summary = pd.DataFrame(summary)
    summary.to_csv(out / "summary.csv", index=False)
    paired.groupby(["rule", "exit_reason"]).size().rename("events").to_csv(out / "exit_reasons.csv")
    paired.assign(month=paired.signal_date.dt.to_period("M")).groupby(["rule", "month"])[
        ["net_return", "net_excess_matched"]].mean().to_csv(out / "monthly.csv")
    # Arithmetic audit of the opening-exit factor, including distribution dates.
    identity_max_error = 0.0
    identity_rows = 0
    for p, history in histories.items():
        previous = (history.close / history.price_adjustment_factor).shift(1)
        reconstructed = ((history.close+history.ordinary_dividend+history.nonordinary_dividend)
                         / history.price_adjustment_factor) / previous - 1
        valid = (history.close.gt(0) & previous.gt(0) & history.delisting_flag.eq("N")
                 & history.total_return.notna() & reconstructed.notna())
        error = (reconstructed-history.total_return).abs().loc[valid]
        identity_max_error = max(identity_max_error, float(error.max()) if len(error) else 0)
        identity_rows += len(error)
    # Raw daily CRSP returns are rounded. This tolerance is broader than that precision.
    assert identity_max_error < 1e-5
    manifest = {"study_id": STUDY, "run_id": stamp, "status": "completed_fixed_family_pilot",
                "config": config, "source_manifest_sha256": sha256(SOURCE / "manifest.json"),
                "protocol_sha256": sha256(protocol), "source_events": len(events), "common_events": len(common),
                "baseline_reconciliation_checks": int((results.rule.eq("hold_126") & results.status.eq("ok")).sum()),
                "distribution_identity_check": {"rows": identity_rows, "max_absolute_error": identity_max_error,
                                                "tolerance": 1e-5},
                "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in
                                  [Path(__file__), ROOT / "src/ath_breakout/research/exit_rules.py"]},
                "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in [*raw_paths, spy_path]},
                "limitations": ["Single previously seen signal year; no out-of-sample claim",
                                "Qualified local-history ATH group only; unresolved inception-history provenance",
                                "Overlapping independent event positions, no capital or re-entry/portfolio constraints",
                                "Closing triggers and next-opening fills, not intraday stops",
                                "Fixed ATR conventions, no optimized-parameter claim",
                                "Gross SPY benchmark versus net stock returns; no risk/factor alpha estimate",
                                "Terminal value realized once with zero-interest cash; settlement timing not simulated"]}
    manifest["artifacts"] = {p.name: sha256(p) for p in out.iterdir() if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(summary.to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == "__main__":
    main()
