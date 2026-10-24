"""Offline 400-pair SPY EMA sensitivity study; full-sample exploration only."""

import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ath_breakout.research.sha.backtest import (
    ExecutionConfig,
    simulate_long_cash,
    summarize,
)
from ath_breakout.research.sha.grid import build_signals, neighbor_sharpe, simulate_grid

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/smoothed_heikin_ashi/grid_20_20"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot_maps(metrics):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import PercentFormatter

    fig, axes = plt.subplots(1, 2, figsize=(15, 7), layout="constrained")
    for ax, field, label in zip(
        axes,
        ["cagr", "sharpe_252"],
        ["CAGR after costs", "Sharpe (252 sessions, zero risk-free)"],
    ):
        matrix = metrics.pivot(index="pre_span", columns="post_span", values=field)
        assert matrix.shape == (20, 20) and matrix.notna().all().all()
        image = ax.imshow(
            matrix.to_numpy(),
            origin="lower",
            cmap="viridis",
            extent=(0.5, 20.5, 0.5, 20.5),
            aspect="equal",
        )
        best = metrics.loc[
            np.isclose(metrics[field], metrics[field].max(), rtol=0, atol=1e-12)
        ]
        ax.scatter(
            [10],
            [10],
            marker="s",
            s=110,
            facecolors="none",
            edgecolors="white",
            linewidths=1.6,
            label="Reference 10/10",
        )
        ax.scatter(
            best.post_span,
            best.pre_span,
            marker="x",
            s=85,
            color="black",
            linewidths=2,
            label="Full-sample maximum",
        )
        ax.set(
            title=label,
            xlabel="EMA length AFTER HA (observed sessions)",
            ylabel="EMA length BEFORE HA (observed sessions)",
        )
        ax.set_xticks(range(1, 21))
        ax.set_yticks(range(1, 21))
        ax.tick_params(labelsize=9)
        bar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        if field == "cagr":
            bar.ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.legend(
            handles=[
                Line2D(
                    [],
                    [],
                    marker="s",
                    color="#334155",
                    markerfacecolor="none",
                    linestyle="none",
                    label="Reference 10/10",
                ),
                Line2D(
                    [],
                    [],
                    marker="x",
                    color="black",
                    linestyle="none",
                    label="Full-sample maxima (ties included)",
                ),
            ],
            loc="upper center",
            bbox_to_anchor=(0.5, -0.14),
            frameon=False,
            fontsize=9,
        )
    fig.suptitle(
        "SPY daily | SHA EMA grid: 400 configurations\n14 Apr 1993–5 Oct 2026 | Exploratory full history; no independent OOS",
        fontsize=14,
    )
    fig.supxlabel(
        "100% SPY / cash · next-open fills · commission 0.10% + slippage 0.05% per side · dividends included · cash yield 0%",
        fontsize=9,
    )
    fig.savefig(OUTPUT / "heatmaps.png", dpi=170)
    fig.savefig(OUTPUT / "heatmaps.svg")
    plt.close(fig)


def main():
    started = datetime.now(timezone.utc)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "data/raw/yfinance/SPY.parquet"
    baseline_dir = ROOT / "outputs/smoothed_heikin_ashi/baseline_ema10_10"
    baseline_manifest = json.loads((baseline_dir / "manifest.json").read_text())
    if sha256(source) != baseline_manifest["source_sha256"]:
        raise ValueError("Source differs from baseline; do not silently change sample")
    raw = pd.read_parquet(source)
    if (
        set(raw.ticker) != {"SPY"}
        or not raw.prices_split_adjusted.eq(True).all()
        or raw.stock_splits.isna().any()
        or raw.stock_splits.ne(0).any()
    ):
        raise ValueError("Unsupported input instrument or split treatment")
    prices = raw.set_index(pd.to_datetime(raw.date))
    config = ExecutionConfig()
    if asdict(config) != baseline_manifest["execution"]:
        raise ValueError("Execution settings differ from baseline")
    print("Building all 400 causal signal series...", flush=True)
    signals = build_signals(prices, 20, 50)
    print("Simulating 400 independent long/cash portfolios...", flush=True)
    metrics, equity, exposure, trades = simulate_grid(prices, signals, 51, config)
    assert (
        len(metrics) == 400 and not metrics.duplicated(["pre_span", "post_span"]).any()
    )
    assert np.isfinite(metrics[["cagr", "sharpe_252", "max_drawdown"]]).all().all()
    metrics = neighbor_sharpe(metrics)
    old = json.loads((baseline_dir / "metrics.json").read_text())
    row10 = metrics.loc[metrics.pre_span.eq(10) & metrics.post_span.eq(10)].iloc[0]
    for field, expected in old["sha_10_10"].items():
        if expected is not None:
            np.testing.assert_allclose(
                row10[field], expected, rtol=1e-9, atol=1e-8, err_msg=field
            )
    selected = {(10, 10)}
    for field in ["cagr", "sharpe_252"]:
        ties = metrics.loc[
            np.isclose(metrics[field], metrics[field].max(), rtol=0, atol=1e-12)
        ]
        selected.update(
            (int(row.pre_span), int(row.post_span)) for row in ties.itertuples()
        )
    print(f"Checking full-history ledger parity for {sorted(selected)}...", flush=True)
    for before, after in sorted(selected):
        ledger, fills, reference_trades = simulate_long_cash(
            prices, signals[(before, after)], 51, config
        )
        np.testing.assert_allclose(
            ledger.equity, equity[(before, after)], rtol=1e-10, atol=1e-7
        )
        actual = metrics.loc[
            metrics.pre_span.eq(before) & metrics.post_span.eq(after)
        ].iloc[0]
        for field, expected in summarize(ledger, fills, reference_trades).items():
            if expected is not None:
                np.testing.assert_allclose(
                    actual[field],
                    expected,
                    rtol=1e-9,
                    atol=1e-7,
                    err_msg=f"{before}/{after} {field}",
                )
        ledger.to_csv(OUTPUT / f"checked_{before}_{after}_daily.csv")
        fills.to_csv(OUTPUT / f"checked_{before}_{after}_fills.csv", index=False)
    hold = pd.Series(1, index=prices.index)
    ledger, fills, hold_trades = simulate_long_cash(prices, hold, 51, config)
    benchmark = summarize(ledger, fills, hold_trades)
    for field, expected in old["buy_and_hold"].items():
        if expected is not None:
            np.testing.assert_allclose(
                benchmark[field], expected, rtol=1e-10, atol=1e-7
            )
    ledger.to_csv(OUTPUT / "buy_and_hold_daily.csv")
    (OUTPUT / "benchmark.json").write_text(
        json.dumps(benchmark, indent=2, allow_nan=False), encoding="utf-8"
    )
    metrics["cagr_rank"] = metrics.cagr.rank(ascending=False, method="min").astype(int)
    metrics["sharpe_rank"] = metrics.sharpe_252.rank(
        ascending=False, method="min"
    ).astype(int)
    metrics.to_csv(OUTPUT / "all_400_metrics.csv", index=False)
    metrics.to_parquet(OUTPUT / "all_400_metrics.parquet", index=False)
    trades.to_parquet(OUTPUT / "all_trades.parquet", index=False)
    # Flat descriptive column names keep parquet consumers interoperable.
    for name, frame in [
        ("daily_equity", equity),
        ("daily_exposure", exposure),
        ("signals", signals),
    ]:
        frame = frame.copy()
        frame.columns = [f"pre_{a}_post_{b}" for a, b in frame.columns]
        frame.to_parquet(OUTPUT / f"{name}.parquet")
    for field in ["cagr", "sharpe_252", "max_drawdown"]:
        metrics.pivot(index="pre_span", columns="post_span", values=field).to_csv(
            OUTPUT / f"matrix_{field}.csv"
        )
    plot_maps(metrics)
    summary = dict(
        configurations=400,
        distinct_signal_histories=int(signals.T.drop_duplicates().shape[0]),
        best_cagr_pairs=[
            list(pair)
            for pair in metrics.loc[
                np.isclose(metrics.cagr, metrics.cagr.max(), rtol=0, atol=1e-12),
                ["pre_span", "post_span"],
            ].itertuples(index=False, name=None)
        ],
        positive_cagr=int(metrics.cagr.gt(0).sum()),
        beating_hold_cagr=int(metrics.cagr.gt(benchmark["cagr"]).sum()),
        beating_hold_sharpe=int(metrics.sharpe_252.gt(benchmark["sharpe_252"]).sum()),
        cagr_min=float(metrics.cagr.min()),
        cagr_median=float(metrics.cagr.median()),
        cagr_max=float(metrics.cagr.max()),
        sharpe_min=float(metrics.sharpe_252.min()),
        sharpe_median=float(metrics.sharpe_252.median()),
        sharpe_max=float(metrics.sharpe_252.max()),
        best_cagr=metrics.loc[metrics.cagr.idxmax()].to_dict(),
        best_sharpe=metrics.loc[metrics.sharpe_252.idxmax()].to_dict(),
    )
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8"
    )
    tracked = [
        "run/sha_grid.py",
        "src/ath_breakout/research/sha/grid.py",
        "src/ath_breakout/research/sha/indicator.py",
        "src/ath_breakout/research/sha/backtest.py",
        "research/smoothed_heikin_ashi/GRID_20_20_PLAN.md",
        "tests/research/sha/test_grid.py",
    ]
    manifest = dict(
        started_utc=started.isoformat(),
        finished_utc=datetime.now(timezone.utc).isoformat(),
        source=str(source),
        source_sha256=sha256(source),
        source_rows=len(prices),
        source_start=str(prices.index[0].date()),
        source_end=str(prices.index[-1].date()),
        valuation_anchor=str(equity.index[0].date()),
        first_execution=str(equity.index[1].date()),
        pre_spans=list(range(1, 21)),
        post_spans=list(range(1, 21)),
        configurations=400,
        warmup_bars=50,
        execution=asdict(config),
        cash_rate=0,
        baseline_manifest_sha256=sha256(baseline_dir / "manifest.json"),
        code_sha256={p: sha256(ROOT / p) for p in tracked},
        output_sha256={
            p.name: sha256(p)
            for p in OUTPUT.iterdir()
            if p.is_file() and p.name != "manifest.json"
        },
        git_head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        python_packages=dict(numpy=np.__version__, pandas=pd.__version__),
        reference_checked_pairs=sorted(selected),
        validation="All 400 synthetic ledger parity; full-history selected equity and metric parity; frozen 10/10 and benchmark reproduced",
        inference="Exploratory same-sample maxima; no independent OOS or significance claim",
    )
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    columns = [
        "pre_span",
        "post_span",
        "cagr",
        "sharpe_252",
        "max_drawdown",
        "completed_trades",
        "median_holding_calendar_days",
        "neighbor_mean_sharpe",
        "neighbor_worst_sharpe",
    ]
    report = [
        "# SPY SHA EMA: 20 x 20 grid",
        "",
        "Exploratory full-history sensitivity; not independent out-of-sample validation.",
        "",
        f"400 pairs: EMA before HA 1..20 x EMA after HA 1..20. Evaluation: {equity.index[1].date()} to {equity.index[-1].date()}.",
        "Signal initialization and 50-bar warm-up unchanged. Real next-open fills; fractional shares; long/cash; neutral retains target.",
        "USD 100,000; commission 10 bps + slippage 5 bps per side including reinvestment; cash yield 0%.",
        "Dividend entitlement, ex-date credit approximation and final-close valuation follow the baseline plan.",
        "",
        "## Grid summary",
        "",
        f"Positive CAGR: {summary['positive_cagr']}/400. Higher CAGR than buy-and-hold: {summary['beating_hold_cagr']}/400.",
        f"Higher Sharpe than buy-and-hold: {summary['beating_hold_sharpe']}/400.",
        f"CAGR range {summary['cagr_min']:.2%} to {summary['cagr_max']:.2%}; median {summary['cagr_median']:.2%}.",
        f"Sharpe range {summary['sharpe_min']:.3f} to {summary['sharpe_max']:.3f}; median {summary['sharpe_median']:.3f}.",
        f"Buy-and-hold: CAGR {benchmark['cagr']:.2%}, Sharpe {benchmark['sharpe_252']:.3f}, max drawdown {benchmark['max_drawdown']:.2%}.",
        "",
        "## Top 10 by full-sample CAGR",
        "",
        "CAGR and drawdown are decimal fractions; e.g. 0.05 = 5%.",
        "",
        metrics.nlargest(10, "cagr")[columns].to_markdown(index=False),
        "",
        "## Top 10 by full-sample Sharpe",
        "",
        metrics.nlargest(10, "sharpe_252")[columns].to_markdown(index=False),
        "",
        "## Reference 10/10",
        "",
        metrics.loc[metrics.pre_span.eq(10) & metrics.post_span.eq(10)].to_markdown(
            index=False
        ),
        "",
        "## Parameter neighborhoods and limits",
        "",
        f"All 400 parameter pairs generated {summary['distinct_signal_histories']} distinct signal histories on this sample; trials are not independent.",
        f"Tied maximum CAGR pairs (absolute tolerance 1e-12): {summary['best_cagr_pairs']}.",
        f"The displayed CAGR leader's immediate neighbors have mean Sharpe {summary['best_cagr']['neighbor_mean_sharpe']:.3f} and minimum Sharpe {summary['best_cagr']['neighbor_worst_sharpe']:.3f}.",
        "Neighbor statistics use adjacent pairs in a clipped 3x3 window excluding the center (3 to 8 neighbors).",
        "They describe sensitivity on the same history, not statistical independence or out-of-sample stability.",
        "At a boundary, settings beyond the tested range are unknown. All 400 trials are retained, including losses.",
        "Maxima were selected after seeing all 400 results and are subject to selection bias. No parameter is declared best for future trading.",
        "SPY is an ETF proxy for S&P 500. Source is an existing unrefreshed snapshot; PyneSys numerical parity remains unverified.",
        "",
        "## Verification and reproduce",
        "",
        "All 400 configurations matched the ledger simulator on synthetic input with costs, dividends and gaps.",
        f"Full-history equity/metric reference checks: {sorted(selected)}. Existing 10/10 and buy-and-hold results reproduced.",
        "Daily equity, signals, exposure, trades, all metrics, heatmaps and fingerprints:",
        "`outputs/smoothed_heikin_ashi/grid_20_20/` (Git ignored).",
        "",
        "```powershell",
        ".venv/Scripts/python.exe run/sha_grid.py",
        "```",
        "",
        f"Source SHA256: `{manifest['source_sha256']}`.",
        "",
    ]
    (ROOT / "research/smoothed_heikin_ashi/GRID_20_20_RESULTS.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Saved: {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
