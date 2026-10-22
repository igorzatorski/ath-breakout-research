"""Frozen SPY price Z-score event study. Run from repository root."""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/zscore/v001"
SOURCE = ROOT / "data/raw/yfinance/SPY.parquet"


def prepare(p):
    p = p.sort_values("date").reset_index(drop=True).copy()
    if p.date.duplicated().any() or not p.date.is_monotonic_increasing:
        raise ValueError("Invalid dates")
    if p[["open", "close", "adj_close"]].isna().any().any() or (p[["open", "close", "adj_close"]] <= 0).any().any():
        raise ValueError("Invalid prices")
    factor = p.adj_close / p.close
    p["entry_date"] = p.date.shift(-1)
    p["exit_date"] = p.date.shift(-5)
    p["forward_return"] = p.adj_close.shift(-5) / (p.open * factor).shift(-1) - 1
    p["price_return"] = p.close.shift(-5) / p.open.shift(-1) - 1
    for lookback in (30, 60):
        roll = p.close.rolling(lookback)
        p[f"z{lookback}"] = (p.close - roll.mean()) / roll.std(ddof=1).replace(0, np.nan)
    return p


def nonoverlap(mask):
    result = np.zeros(len(mask), dtype=bool)
    last_exit = -1
    for i in np.flatnonzero(mask):
        if i >= last_exit:
            result[i] = True
            last_exit = i + 5
    return result


def stats(x):
    return dict(n=len(x), mean=x.mean(), median=x.median(), win_rate=(x > 0).mean(),
                p05=x.quantile(.05), p95=x.quantile(.95), worst=x.min(),
                mean_less_20bps=x.mean() - .002)


def bootstrap(r, mask, draws=2000, block=20):
    rng = np.random.default_rng(42)
    means, differences = [], []
    n = len(r)
    for _ in range(draws):
        starts = rng.integers(0, n - block + 1, size=int(np.ceil(n / block)))
        idx = (starts[:, None] + np.arange(block)).ravel()[:n]
        selected = r[idx][mask[idx]]
        if len(selected):
            means.append(selected.mean())
            differences.append(selected.mean() - r[idx].mean())
    return dict(mean_ci=np.quantile(means, [.025, .975]).tolist(),
                excess_ci=np.quantile(differences, [.025, .975]).tolist())


def main(threshold=-1, ticker="SPY", start=None):
    SOURCE = ROOT / "data/raw/yfinance" / ("SPY.parquet" if ticker == "SPY" else "QQQ_zscore.parquet")
    suffix = "v001" if threshold == -1 else "v002_minus2"
    if ticker != "SPY" or start:
        suffix = f"{ticker}_{abs(threshold)}" + (f"_from_{start}" if start else "")
    OUT = ROOT / "outputs/zscore" / suffix
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_parquet(SOURCE)
    p = prepare(raw)
    eligible = p[["z30", "z60", "forward_return"]].notna().all(axis=1)
    if start:
        eligible &= p.date >= pd.Timestamp(start)
    d = p.loc[eligible].copy()
    rows, intervals = [], {}
    for window in (30, 60):
        signal = (d[f"z{window}"] <= threshold).to_numpy()
        d[f"signal{window}"] = signal
        d[f"nonoverlap{window}"] = nonoverlap(signal)
        intervals[str(window)] = bootstrap(d.forward_return.to_numpy(), signal)
        intervals[str(window)]["block60_sensitivity"] = bootstrap(d.forward_return.to_numpy(), signal, block=60)
        for label, dates in [("full", np.ones(len(d), bool)),
                             ("1993-2009", d.date.dt.year <= 2009),
                             ("2010-2017", d.date.dt.year.between(2010, 2017)),
                             ("2018-end", d.date.dt.year >= 2018)]:
            for kind, mask in [("unconditional", np.ones(len(d), bool)),
                               ("all_signals", signal),
                               ("nonoverlap", d[f"nonoverlap{window}"].to_numpy())]:
                x = d.loc[np.asarray(dates) & mask]
                rows.append(dict(window=window, period=label, sample=kind,
                                 **stats(x.forward_return), mean_price_return=x.price_return.mean()))
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "summary.csv", index=False)
    d.to_csv(OUT / "events.csv", index=False)
    manifest = dict(source=str(SOURCE.relative_to(ROOT)), sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    raw_rows=len(raw), start=str(raw.date.min()), end=str(raw.date.max()),
                    eligible_start=str(d.date.min()), eligible_end=str(d.date.max()),
                    windows=[30, 60], threshold=threshold, holding_sessions=5, bootstrap_block=20,
                    bootstrap_draws=2000, seed=42, intervals=intervals)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = f"# {ticker} Z-score research: threshold {threshold}\n\nSee PLAN.md for methodology.\n\n"
    if threshold == -1 and ticker == "SPY" and not start:
        report += ("The 30-session signal has a modest positive historical mean-return association, "
               "not a material win-rate improvement. Its 95% block-bootstrap excess interval is "
               "above zero in this sample (uncorrected for testing two windows); the 60-session "
               "interval includes zero. These are exploratory findings, not independently validated alpha. "
               "The 30-session non-overlapping sample averages 0.393% gross and 0.193% after an "
               "illustrative 20bps round trip, with a 57.7% win rate and a -19.6% worst holding window. "
               "The adverse tail is worse than the unconditional sample. No live trading or leverage "
               "conclusion follows. A 60-session bootstrap block was added after the first result "
               "as an explicitly post-result dependence sensitivity; it leaves the qualitative conclusion unchanged.\n\n")
    report += f"Source: local Yahoo {ticker}, {raw.date.min().date()} to {raw.date.max().date()}; {len(d)} complete signal dates from {d.date.min().date()} to {d.date.max().date()}.\n\n"
    report += summary.to_markdown(index=False, floatfmt=".5f")
    report += "\n\n## Block bootstrap (all signal days)\n\n" + json.dumps(intervals, indent=2)
    report += "\n\nAll returns are decimal, unlevered, before financing and execution costs except the explicitly labeled 20bps sensitivity. Non-overlap is a separate event sample, not a full portfolio backtest. Dividend-adjusted open is a proxy. No inference about stops, futures rolls, CFD financing, margin liquidation or leverage is supported. Historical splits are inspected diagnostics, not independent out-of-sample validation. Neither window was selected as a winner.\n"
    report_name = "RESULTS.md" if threshold == -1 else "RESULTS_MINUS2.md"
    if ticker != "SPY" or start:
        report_name = f"RESULTS_{suffix}.md"
    (ROOT / "research/zscore" / report_name).write_text(report, encoding="utf-8")
    print(summary.to_string(index=False))
    print(json.dumps(intervals, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=int, choices=[-1, -2], default=-1)
    parser.add_argument("--ticker", choices=["SPY", "QQQ"], default="SPY")
    parser.add_argument("--start", help="Optional earliest signal date (warmup uses full history)")
    args = parser.parse_args()
    main(args.threshold, args.ticker, args.start)
