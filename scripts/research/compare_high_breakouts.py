"""Reproducible 2024 pilot: 252-session breakouts, ATH tags, aligned SPY returns."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.high_breakout import (  # noqa: E402
    holding_return, prior_252_high, spy_holding_return,
)

STUDY = "high_01_52w_vs_ath_pilot_v001"
HORIZONS = (5, 21, 63, 126)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def block_interval(events, column):
    """Exploratory resampling of signal months; not an independent-events t-test."""
    z = events.assign(month=events.date.dt.to_period("M"))
    blocks = z.groupby("month")[column].agg(["sum", "count"])
    rng = np.random.default_rng(20261015)
    sample = rng.integers(0, len(blocks), size=(2000, len(blocks)))
    means = blocks["sum"].to_numpy()[sample].sum(axis=1) / blocks["count"].to_numpy()[sample].sum(axis=1)
    return np.quantile(means, [.025, .975])


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / f"outputs/research/high_breakouts/{STUDY}/{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    raw = ROOT / "data/raw/crsp"
    seed_path = raw / "ath_seed_before_1993.parquet"
    seed = pd.read_parquet(seed_path)
    prior = seed.set_index("permno").prior_comparable_high.to_dict()
    seeded = set(prior)
    missing_high = set()
    sources = [seed_path]
    for year in range(1993, 2024):
        path = raw / f"daily_by_year/daily_{year}.parquet"
        sources.append(path)
        d = pd.read_parquet(path, columns=["permno", "high", "close", "price_adjustment_factor"])
        valid = (np.isfinite(d.high) & d.high.gt(0) & np.isfinite(d.price_adjustment_factor)
                 & d.price_adjustment_factor.gt(0) & (d.high.ge(d.close) | d.close.isna()))
        missing_high.update(d.loc[~valid, "permno"].unique())
        maxima = (d.high / d.price_adjustment_factor).where(valid).groupby(d.permno).max()
        for p, h in maxima.dropna().items():
            prior[p] = max(prior.get(p, h), h)
    print("Historical ATH bounds loaded; extracting 252-session signals", flush=True)
    paths = [raw / f"daily_by_year/daily_{y}.parquet" for y in (2022, 2023, 2024, 2025)]
    # 2022/2023 are already listed among the ATH inputs.
    sources += paths[2:]
    columns = ["permno", "ticker", "date", "open", "high", "close", "volume",
               "price_adjustment_factor", "total_return", "delisting_flag"]
    daily = pd.concat([pd.read_parquet(p, columns=columns) for p in paths], ignore_index=True)
    daily["date"] = pd.to_datetime(daily.date)
    daily = daily.loc[daily.date.ge("2022-11-01")].copy()
    if daily.duplicated(["permno", "date"]).any():
        raise ValueError("Duplicate raw PERMNO/session")
    sessions = valid_nyse_sessions("2022-11-01", "2025-12-31")
    high = (daily.high / daily.price_adjustment_factor).where(
        np.isfinite(daily.high) & daily.high.gt(0) & np.isfinite(daily.price_adjustment_factor)
        & daily.price_adjustment_factor.gt(0) & (daily.high.ge(daily.close) | daily.close.isna()))
    daily["adjusted_high"] = high
    daily["adjusted_close"] = (daily.close / daily.price_adjustment_factor).where(
        np.isfinite(daily.close) & daily.close.gt(0) & np.isfinite(daily.price_adjustment_factor)
        & daily.price_adjustment_factor.gt(0))
    memberships_path = ROOT / "data/processed/crsp/universe_memberships.parquet"
    sources.append(memberships_path)
    memberships = pd.read_parquet(memberships_path)
    formation = memberships[["effective_date", "formation_date"]].drop_duplicates().sort_values("effective_date")
    date_map = pd.merge_asof(pd.DataFrame({"date": sessions}), formation,
                            left_on="date", right_on="effective_date", direction="backward").set_index("date")
    member_keys = set(zip(memberships.effective_date, memberships.permno))
    events = []
    histories = {}
    for p, stock in daily.groupby("permno", sort=True):
        h = stock.set_index("date").reindex(sessions)
        histories[p] = h
        threshold = prior_252_high(h.adjusted_high)
        liquidity = (h.close * h.volume).where(
            np.isfinite(h.close) & h.close.gt(0) & np.isfinite(h.volume) & h.volume.ge(0)).rolling(21, min_periods=21).mean()
        prior_ath = h.adjusted_high.cummax().ffill().shift(1)
        # Prior state includes 2023; restrict its use to 2024 signal dates.
        if p in prior:
            prior_ath = prior_ath.clip(lower=prior[p]).fillna(prior[p])
        # Leading absent 2023 rows are not necessarily missing history (e.g. IPO).
        observed_missing = (h.permno.notna() & h.adjusted_high.isna()).cummax().shift(1, fill_value=False)
        mask = (h.index.year == 2024) & h.adjusted_close.gt(threshold)
        for date in h.index[mask]:
            row = h.loc[date]
            mapping = date_map.loc[date]
            in_universe = (mapping.effective_date, p) in member_keys
            reason = ("not_pit_member" if not in_universe else
                      "incomplete_liquidity" if pd.isna(liquidity.loc[date]) else
                      "below_liquidity_floor" if liquidity.loc[date] < 10_000_000 else "")
            candidate_ath = row.adjusted_close > prior_ath.loc[date]
            uncertain = p in seeded or p in missing_high or bool(observed_missing.loc[date])
            group = ("52w_only" if not candidate_ath else
                     "ath_uncertain" if uncertain else "ath_local_history")
            index = sessions.get_loc(date)
            events.append({"permno": p, "ticker": row.ticker, "date": date,
                           "entry_date": sessions[index + 1], "entry_index": index + 1,
                           "formation_date": mapping.formation_date,
                           "prior_252_high": threshold.loc[date], "prior_ath_local": prior_ath.loc[date],
                           "adjusted_close": row.adjusted_close, "adv21": liquidity.loc[date],
                           "group": group, "pre1993_seed_uncertain": p in seeded,
                           "historical_high_missing": p in missing_high or bool(observed_missing.loc[date]),
                           "exclusion_reason": reason})
    candidates = pd.DataFrame(events)
    candidates.loc[candidates.exclusion_reason.ne("")].to_csv(out / "exclusions.csv", index=False)
    events = candidates.loc[candidates.exclusion_reason.eq("")].copy().reset_index(drop=True)
    assert (events.formation_date < events.date).all()
    events["repeated_in_year"] = events.duplicated("permno")
    spy_path = ROOT / "data/raw/yfinance/SPY.parquet"
    sources.append(spy_path)
    spy = pd.read_parquet(spy_path).set_index("date").reindex(sessions)
    print(f"Computing forward returns for {len(events)} events", flush=True)
    result = []
    for n, event in enumerate(events.itertuples()):
        stock = histories[event.permno]
        for horizon in HORIZONS:
            r, status, terminal = holding_return(stock, event.entry_index, horizon)
            benchmark = spy_holding_return(spy, event.entry_index, horizon)
            result.append({"event_id": n, "permno": event.permno, "date": event.date,
                           "group": event.group, "horizon": horizon,
                           "exit_date": sessions[event.entry_index + horizon - 1],
                           "return": r, "spy_return": benchmark,
                           "excess": r - benchmark,
                           "net_return_10bps_side": (1 + r) * .999 / 1.001 - 1,
                           "status": status, "terminal_cash": terminal})
        if n and n % 2000 == 0:
            print(f"Returns: {n}/{len(events)}", flush=True)
    returns = pd.DataFrame(result)
    events.to_parquet(out / "events.parquet", index=False)
    events.to_csv(out / "events.csv", index=False)
    returns.to_parquet(out / "forward_returns.parquet", index=False)
    summary = []
    for horizon in HORIZONS:
        for group in ["all_52w", "52w_only", "ath_local_history", "ath_uncertain"]:
            all_rows = returns.loc[returns.horizon.eq(horizon)]
            if group != "all_52w":
                all_rows = all_rows.loc[all_rows.group.eq(group)]
            z = all_rows.loc[np.isfinite(all_rows.excess)]
            if len(z) == 0:
                continue
            lo, hi = block_interval(z, "excess")
            summary.append({"group": group, "horizon": horizon, "events": len(all_rows),
                            "valid_pairs": len(z), "securities": z.permno.nunique(),
                            "mean_return": z["return"].mean(), "median_return": z["return"].median(),
                            "mean_spy": z.spy_return.mean(), "mean_excess": z.excess.mean(),
                            "median_excess": z.excess.median(), "loss_frequency": z["return"].lt(0).mean(),
                            "q05_return": z["return"].quantile(.05), "q95_return": z["return"].quantile(.95),
                            "mean_net_excess": (z.net_return_10bps_side - z.spy_return).mean(),
                            "equal_security_mean_excess": z.groupby("permno").excess.mean().mean(),
                            "equal_signal_date_mean_excess": z.groupby("date").excess.mean().mean(),
                            "month_bootstrap_lo": lo, "month_bootstrap_hi": hi,
                            "terminal_cash": int(z.terminal_cash.sum())})
    summary = pd.DataFrame(summary)
    summary.to_csv(out / "summary.csv", index=False)
    returns.groupby(["group", "horizon", "status"]).size().rename("count").to_csv(out / "coverage.csv")
    # Independently recompute 20 thresholds from the raw rows and exact prior sessions.
    checks = []
    for e in events.sample(min(20, len(events)), random_state=20261015).itertuples():
        pos = e.entry_index - 1
        history = histories[e.permno].iloc[pos-252:pos]
        threshold = (history.high / history.price_adjustment_factor).max()
        checks.append({"permno": e.permno, "date": e.date, "threshold": e.prior_252_high,
                       "independent_threshold": threshold, "match": bool(np.isclose(threshold, e.prior_252_high))})
    pd.DataFrame(checks).to_csv(out / "sample_checks.csv", index=False)
    assert all(c["match"] for c in checks)
    primary = returns.loc[returns.horizon.eq(21)]
    primary.groupby([primary.date.dt.to_period("M"), "group"]).excess.agg(["count", "mean"]).to_csv(out / "monthly_primary.csv")
    print("Fingerprinting local inputs", flush=True)
    manifest = {"study_id": STUDY, "run_id": stamp, "status": "completed_descriptive_pilot",
                "signal_year": 2024, "primary_horizon": 21, "horizons": HORIZONS,
                "config": {"window": 252, "signal": "close > prior 252 session high", "adv21_min": 10000000,
                           "entry": "next exchange session observed open", "exit": "close of Hth holding session",
                           "terminal": "CIZ Y total return once, then zero-interest cash",
                           "cost_sensitivity_bps_per_side": 10, "bootstrap_seed": 20261015,
                           "bootstrap_replicates": 2000, "bootstrap_unit": "signal calendar month"},
                "events": len(events), "securities": int(events.permno.nunique()),
                "group_counts": events.group.value_counts().to_dict(),
                "exclusions": candidates.loc[candidates.exclusion_reason.ne(""), "exclusion_reason"].value_counts().to_dict(),
                "independent_checks": checks.__len__(), "independent_checks_pass": True,
                "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in
                                  [Path(__file__), ROOT / "src/ath_breakout/research/high_breakout.py"]},
                "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in sources],
                "limitations": ["Single previously seen year; not out-of-sample or alpha evidence",
                                "ATH seed/high history uncertainty explicitly separated; listing inception not independently verified",
                                "252 valid prior sessions excludes young listings and missing-high windows",
                                "Groups differ in size, volatility and other characteristics; no matched controls yet",
                                "Events overlap; 12 signal-month blocks do not remove all cross-month dependence",
                                "Terminal proceeds treated as liquidated value then cash; not actual settlement timing",
                                "Entry-day exotic distributions not separately modeled; daily total returns used after entry",
                                "SPY adjusted-close reinvestment proxy and same-day close/open entry; different vendor"]}
    manifest["artifacts"] = {p.name: sha256(p) for p in out.iterdir() if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(summary.loc[summary.horizon.eq(21)].to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == "__main__":
    main()
