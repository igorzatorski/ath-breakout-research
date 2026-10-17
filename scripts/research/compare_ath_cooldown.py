"""One frozen 21-session repeated-event sensitivity, using local study artifacts."""
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
from ath_breakout.research.event_selection import cooldown_event_ids  # noqa: E402

SOURCE = ROOT / "outputs/research/ath/ath_04_signal_matched_v002/20261015T214148297829Z"
STUDY = "ath_05_cooldown21_v001"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def joint_intervals(primary, metric, block, draws=2000):
    """Common signal-date blocks for baseline/retained means and their difference."""
    calendar = valid_nyse_sessions(primary.date.min(), primary.date.max())
    base = primary.groupby("date")[metric].agg(["sum", "count"]).reindex(calendar, fill_value=0)
    retained = primary.loc[primary.retained].groupby("date")[metric].agg(["sum", "count"]).reindex(calendar, fill_value=0)
    values = np.column_stack([base.to_numpy(), retained.to_numpy()])
    n = len(values)
    block = min(block, n)
    extended = np.concatenate([values, values[:block-1]])
    prefix = np.vstack([np.zeros(4), np.cumsum(extended, axis=0)])
    totals = prefix[np.arange(n)+block] - prefix[np.arange(n)]
    rng = np.random.default_rng(20261015)
    estimates = []
    for _ in range(draws):
        z = totals[rng.integers(0, n, size=int(np.ceil(n/block)))].sum(axis=0)
        if z[1] and z[3]:
            baseline, kept = z[0]/z[1], z[2]/z[3]
            estimates.append([baseline, kept, kept-baseline])
    bounds = np.quantile(estimates, [.025, .975], axis=0)
    point = [primary[metric].mean(), primary.loc[primary.retained, metric].mean()]
    point.append(point[1]-point[0])
    return [{"metric": metric, "block_sessions": block, "estimate": label,
             "mean": point[i], "lower95": bounds[0, i], "upper95": bounds[1, i]}
            for i, label in enumerate(["baseline", "cooldown21", "cooldown_minus_baseline"])]


def describe(z, variant, period, comparison):
    return {"variant": variant, "period": period, "comparison": comparison,
            "events": len(z), "securities": z.permno.nunique(),
            "mean_stock": z.stock_return.mean(), "median_stock": z.stock_return.median(),
            "mean_spy": z.spy_return.mean(), "mean_controls": z.control_return.mean(),
            "mean_excess_spy": z.excess_spy.mean(), "mean_excess_controls": z.excess_control.mean(),
            "median_excess_controls": z.excess_control.median(),
            "loss_fraction": z.stock_return.lt(0).mean(),
            "equal_security_excess_controls": z.groupby("permno").excess_control.mean().mean(),
            "equal_date_excess_controls": z.groupby("date").excess_control.mean().mean()}


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/ath/{STUDY}/{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    source_manifest = json.loads((SOURCE / "manifest.json").read_text())
    inputs = [SOURCE / "forward_returns.parquet", *sorted((SOURCE / "by_year").glob("events_*.parquet"))]
    for path in inputs:
        assert sha256(path) == source_manifest["artifacts"][str(path.relative_to(SOURCE))]
    events = pd.concat([pd.read_parquet(p) for p in inputs[1:]], ignore_index=True)
    assert len(events) == source_manifest["events"]
    calendar = valid_nyse_sessions("1994-01-01", "2026-06-30")
    kept = set(cooldown_event_ids(events, calendar, cooldown=21))
    events["retained"] = events.event_id.isin(kept)
    # Check the greedy rule independently against every previous accepted signal.
    checked = 0
    for _, g in events.sort_values(["permno", "date"]).groupby("permno"):
        previous = None
        for event in g.itertuples():
            position = calendar.get_loc(event.date)
            expected = previous is None or position-previous > 21
            assert expected == event.retained
            if expected:
                previous = position
            checked += 1
    events[["event_id", "permno", "date", "retained"]].to_parquet(out / "selection.parquet", index=False)
    f = pd.read_parquet(inputs[0])
    h = f.loc[f.horizon.eq(21)].copy()
    h["retained"] = h.event_id.isin(kept)
    h.to_parquet(out / "primary_events.parquet", index=False)
    primary = h.loc[h.excess_spy.notna() & h.excess_control.notna()].copy()
    source_summary = pd.read_csv(SOURCE / "summary.csv")
    original = source_summary.loc[source_summary.group.eq("matched_primary") & source_summary.horizon.eq(21)].iloc[0]
    assert len(primary) == original.events
    assert np.isclose(primary.excess_control.mean(), original.mean_excess_control, atol=1e-12)
    summaries = []
    periods = [("all", "1994-01-01", "2026-06-30"), ("1994_2009", "1994-01-01", "2009-12-31"),
               ("2010_2017", "2010-01-01", "2017-12-31"), ("2018_2026", "2018-01-01", "2026-06-30")]
    for label, start, end in periods:
        for comparison, sample in [("matched", primary), ("spy_only", h.loc[h.excess_spy.notna()])]:
            z = sample.loc[sample.date.between(start, end)]
            for variant, subset in [("baseline", z), ("cooldown21", z.loc[z.retained]), ("skipped", z.loc[~z.retained])]:
                summaries.append(describe(subset, variant, label, comparison))
    summary = pd.DataFrame(summaries)
    summary.to_csv(out / "summary.csv", index=False)
    intervals = []
    for metric in ["excess_spy", "excess_control"]:
        for block in [126, 252]:
            intervals.extend(joint_intervals(primary, metric, block))
    pd.DataFrame(intervals).to_csv(out / "uncertainty.csv", index=False)
    h.groupby(["retained", "status", "matched_at_signal", "valid_control_count"]).size().rename("count").to_csv(out / "coverage.csv")
    primary.assign(year=primary.date.dt.year).groupby(["year", "retained"])[
        ["stock_return", "spy_return", "control_return", "excess_spy", "excess_control"]].agg(["count", "mean"]).to_csv(out / "annual.csv")
    config = {"study_id": STUDY, "horizon": 21, "cooldown_following_sessions": 21,
              "earliest_next_signal_session_difference": 22, "skipped_signals_reset_clock": False,
              "selection_before_future_validity": True, "parameter_search": False,
              "bootstrap_draws": 2000, "bootstrap_blocks": [126, 252], "random_seed": 20261015}
    (out / "config.json").write_text(json.dumps(config, indent=2))
    manifest = {"study_id": STUDY, "run_id": stamp, "status": "completed_sampling_sensitivity",
                "config": config, "source_run": str(SOURCE.relative_to(ROOT)),
                "source_manifest_sha256": sha256(SOURCE / "manifest.json"),
                "source_events": len(events), "retained_before_future_filters": len(kept),
                "selection_invariants_checked": checked,
                "matched_baseline": len(primary), "matched_retained": int(primary.retained.sum()),
                "protocol_sha256": sha256(ROOT / "research/ath/ATH_COOLDOWN_PLAN.md"),
                "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in
                                  [Path(__file__), ROOT / "src/ath_breakout/research/event_selection.py"]},
                "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in inputs],
                "limitations": ["Same quality-selected population; historical exclusions unchanged",
                                "Not a portfolio or optimized filter", "Remaining cross-company/control dependence",
                                "Sensitivity changes event weighting, not causal proof or alpha",
                                "Known history, not untouched out-of-sample"]}
    manifest["artifacts"] = {p.name: sha256(p) for p in out.iterdir() if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(summary.loc[summary.comparison.eq("matched")].to_string(index=False))
    print(pd.DataFrame(intervals).loc[lambda x: x.metric.eq("excess_control")].to_string(index=False))
    print(out, flush=True)


if __name__ == "__main__":
    main()
