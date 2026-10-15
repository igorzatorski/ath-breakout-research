"""Describe frozen 2024 breakout paths; no exit-rule fitting or simulation."""
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
from ath_breakout.research.event_paths import describe_path  # noqa: E402

SOURCE = ROOT / "outputs/research/high_breakouts/high_01_52w_vs_ath_pilot_v001/20261015T205046302698Z"
STUDY = "high_02_paths_pilot_v001"


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
    source_manifest = json.loads((SOURCE / "manifest.json").read_text())
    for name in ["events.parquet", "forward_returns.parquet"]:
        assert sha256(SOURCE / name) == source_manifest["artifacts"][name]
    events = pd.read_parquet(SOURCE / "events.parquet")
    baseline = pd.read_parquet(SOURCE / "forward_returns.parquet")
    baseline_by_event = baseline.pivot(index="event_id", columns="horizon", values="return")
    raw_paths = [ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet" for year in [2024, 2025]]
    source_hashes = {s["path"]: s["sha256"] for s in source_manifest["inputs"]}
    for path in raw_paths:
        assert sha256(path) == source_hashes[str(path.relative_to(ROOT))]
    columns = ["permno", "date", "open", "high", "low", "close", "price_adjustment_factor",
               "total_return", "delisting_flag"]
    raw = pd.concat([pd.read_parquet(p, columns=columns) for p in raw_paths], ignore_index=True)
    raw = raw.loc[raw.permno.isin(events.permno)].copy()
    raw.date = pd.to_datetime(raw.date)
    assert not raw.duplicated(["permno", "date"]).any()
    sessions = valid_nyse_sessions("2024-01-01", "2025-12-31")
    histories = {p: g.set_index("date").reindex(sessions) for p, g in raw.groupby("permno")}
    spy_path = ROOT / "data/raw/yfinance/SPY.parquet"
    assert sha256(spy_path) == source_hashes[str(spy_path.relative_to(ROOT))]
    spy = pd.read_parquet(spy_path).set_index("date").reindex(sessions)
    records = []
    for event_id, event in events.iterrows():
        start = sessions.get_loc(event.entry_date)
        window = histories[event.permno].iloc[start:start+126]
        level = event.prior_252_high if event.group == "52w_only" else event.prior_ath_local
        result, wealth = describe_path(window, level, event.prior_252_high)
        result.update({"event_id": event_id, "permno": event.permno, "ticker": event.ticker,
                       "signal_date": event.date, "entry_date": event.entry_date, "group": event.group})
        if result["status"] == "ok":
            spy_after5 = float(spy.adj_close.iloc[start+125] / spy.adj_close.iloc[start+4] - 1)
            result["spy_return_after5"] = spy_after5
            result["excess_after5"] = result["return_after5"] - spy_after5
            expected = baseline_by_event.loc[event_id, [5, 21, 63, 126]].to_numpy()
            assert np.allclose(wealth[[4, 20, 62, 125]] - 1, expected, atol=1e-12)
        records.append(result)
        if event_id and event_id % 2500 == 0:
            print(f"Paths: {event_id}/{len(events)}", flush=True)
    paths = pd.DataFrame(records)
    paths.to_parquet(out / "paths.parquet", index=False)
    paths.to_csv(out / "paths.csv", index=False)
    valid = paths.loc[paths.status.eq("ok")].copy()
    cohort_rows, landmark_rows, overview = [], [], []
    for group in ("all_52w", "52w_only", "ath_local_history", "ath_uncertain"):
        z = valid if group == "all_52w" else valid.loc[valid.group.eq(group)]
        # Pooled all-52W uses its 252-session level for a consistent warning.
        below = "below_252_by5" if group == "all_52w" else "below_level_by5"
        below_before20 = "below_252_before20" if group == "all_52w" else "below_level_before20"
        overview.append({"group": group, "events": len(z), "securities": z.permno.nunique(),
                         "winner20_fraction": z.cohort.eq("winner20").mean(),
                         "loser_fraction": z.cohort.eq("loser").mean(),
                         "median_max_close_return": z.max_close_return.median(),
                         "median_min_close_return": z.min_close_return.median(),
                         "hit_plus20_close_fraction": z.first_plus20_close.notna().mean(),
                         "hit20_then_finish_below20_fraction": (z.first_plus20_close.notna() & z.cohort.ne("winner20")).mean(),
                         "intraday_complete_events": int(z.intraday_complete.sum())})
        for cohort, c in z.groupby("cohort"):
            cohort_rows.append({"group": group, "cohort": cohort, "events": len(c), "securities": c.permno.nunique(),
                                "median_return126": c.return_126.median(),
                                "below_level_by5_fraction": c[below].mean(),
                                "below_level_before20_fraction": pd.to_numeric(c[below_before20]).mean(),
                                "median_min_close_before20": c.min_close_before20.median(),
                                "p10_min_close_before20": c.min_close_before20.quantile(.1),
                                "min_close_before20_le_minus5_fraction": c.min_close_before20.le(-.05).mean()
                                    if cohort == "winner20" else np.nan,
                                "min_close_before20_le_minus10_fraction": c.min_close_before20.le(-.1).mean()
                                    if cohort == "winner20" else np.nan,
                                "median_min_price_before20": c.min_price_before20.median(),
                                "median_day_first20": c.first_plus20_close.median(),
                                "median_max_close_return": c.max_close_return.median(),
                                "median_min_close_return": c.min_close_return.median()})
        landmark = z.loc[z.landmark5_eligible.eq(True)].copy()
        landmark["warning"] = landmark[below].astype(bool)
        for warning, c in landmark.groupby("warning"):
            landmark_rows.append({"group": group, "warning_by5": warning, "events": len(c), "securities": c.permno.nunique(),
                                  "mean_return_after5": c.return_after5.mean(), "median_return_after5": c.return_after5.median(),
                                  "mean_spy_after5": c.spy_return_after5.mean(), "mean_excess_after5": c.excess_after5.mean(),
                                  "equal_security_mean_excess_after5": c.groupby("permno").excess_after5.mean().mean(),
                                  "future_loss_fraction": c.return_after5.lt(0).mean(),
                                  "final_winner20_fraction": c.cohort.eq("winner20").mean()})
    pd.DataFrame(overview).to_csv(out / "overview.csv", index=False)
    pd.DataFrame(cohort_rows).to_csv(out / "cohorts.csv", index=False)
    pd.DataFrame(landmark_rows).to_csv(out / "landmark5.csv", index=False)
    paths.groupby(["group", "status"]).size().rename("events").to_csv(out / "coverage.csv")
    # Round descriptive examples, selected by the largest final returns, not trading recommendations.
    examples = valid.loc[valid.group.eq("ath_local_history")].nlargest(10, "return_126")
    examples.to_csv(out / "retrospective_examples.csv", index=False)
    manifest = {"study_id": STUDY, "run_id": stamp, "status": "completed_descriptive_path_pilot",
                "source_run": str(SOURCE.relative_to(ROOT)), "source_manifest_sha256": sha256(SOURCE / "manifest.json"),
                "protocol_sha256": sha256(ROOT / "research/ath/HIGH_PATH_PILOT_PLAN.md"),
                "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in
                                  [Path(__file__), ROOT / "src/ath_breakout/research/event_paths.py"]},
                "raw_input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in [*raw_paths, spy_path]},
                "events": len(events), "valid_paths": len(valid), "horizon_checks": len(valid) * 4,
                "config": {"horizon": 126, "winner_final_total_return_min": .20,
                           "loser_final_total_return_max_exclusive": 0, "landmark_session": 5},
                "limitations": ["Retrospective cohorts are not tradable labels", "Single previously seen year and overlapping events",
                                "ATH qualifications unchanged", "No exit simulation or high/low ordering assumption",
                                "Landmark returns start AFTER day5 close; only still-quoted survivors included",
                                "Price breach levels are not ordinary-dividend-adjusted", "No causal or alpha claim"]}
    manifest["artifacts"] = {p.name: sha256(p) for p in out.iterdir() if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(pd.DataFrame(cohort_rows).loc[lambda x: x.group.eq("ath_local_history")].to_string(index=False))
    print(pd.DataFrame(landmark_rows).to_string(index=False))
    print(out, flush=True)


if __name__ == "__main__":
    main()
