"""Run frozen futures v001 research prototype and same-date SPY comparators."""

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from ath_breakout.research.trend_following_futures.model import (
    Config,
    equity_metrics,
    simulate,
    spy_benchmark,
)
from run.futures_fetch import COMMIT, MAPPING, OUT as RAW

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/trend_following_futures/baseline_v001"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_panels():
    audit = ROOT / "outputs/trend_following_futures/source_audit"
    coverage = pd.read_csv(audit / "coverage.csv")
    if (
        coverage.adjustment_mismatches.sum()
        or coverage.unexplained_roll_contracts.sum()
    ):
        raise ValueError("Unresolved source stitching exceptions")
    prepared = pd.read_parquet(audit / "daily_markets.parquet")
    spy = pd.read_parquet(ROOT / "data/raw/yfinance/SPY.parquet").set_index("date")
    dates = spy.index[
        (spy.index >= pd.Timestamp(coverage.first_date.max()))
        & (spy.index <= pd.Timestamp(coverage.last_date.min()))
    ]
    raw_prices, adjusted, rolls, staleness = {}, {}, {}, []
    points, costs = [], []
    for root in MAPPING:
        market = prepared.loc[prepared.root.eq(root)].set_index("date").sort_index()
        union = market.index.union(dates).sort_values()
        aligned = market.reindex(union).ffill().reindex(dates)
        mark_dates = (
            pd.Series(market.index, index=market.index)
            .reindex(union)
            .ffill()
            .reindex(dates)
        )
        stale = pd.Series(mark_dates.to_numpy() < dates, index=dates)
        consecutive = stale.astype(int).groupby((~stale).cumsum()).cumsum()
        eligible = (
            consecutive.max() <= 3
            and not aligned[["adjusted", "PRICE"]].isna().any().any()
        )
        staleness.append(
            dict(
                root=root,
                stale_mark_sessions=int(stale.sum()),
                maximum_consecutive_stale=int(consecutive.max()),
                eligible=bool(eligible),
                exclusion_reason=""
                if eligible
                else "priced-mark gap exceeds three NYSE sessions",
            )
        )
        if not eligible:
            continue
        cumulative_rolls = (
            market.roll_events.cumsum().reindex(union).ffill().reindex(dates)
        )
        rolls[root] = cumulative_rolls.diff().fillna(0)
        raw_prices[root] = aligned.PRICE
        adjusted[root] = aligned.adjusted
        points.append(float(market.point_value.iloc[-1]))
        costs.append(
            float(
                market.commission_per_unit.iloc[-1]
                + market.spread_price_cost.iloc[-1] * market.point_value.iloc[-1]
            )
        )
    config = pd.read_csv(RAW / "data/futures/csvconfig/instrumentconfig.csv").set_index(
        "Instrument"
    )
    if config.loc[list(MAPPING.values()), ["Percentage", "PerTrade"]].ne(0).any().any():
        raise ValueError("Unsupported nonzero commission components")
    registry = json.loads(
        (ROOT / "research/trend_following_futures/universe.json").read_text()
    )
    lookup = {r["root"]: r["asset_class"] for r in registry["markets"]}
    groups = [lookup[root] for root in adjusted]
    if len(adjusted) < 12 or len(set(groups)) != 4:
        raise ValueError("Insufficient eligible markets or missing asset class")
    return (
        pd.DataFrame(adjusted),
        pd.DataFrame(raw_prices),
        pd.DataFrame(rolls),
        np.array(points),
        np.array(costs),
        groups,
        spy.adj_close,
        pd.DataFrame(staleness),
    )


def chart(curves, market_count):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    import matplotlib.dates as mdates

    colors = {
        "futures_trend": "#245788",
        "futures_always_long": "#9b6b22",
        "spy_buy_hold": "#343a40",
        "spy_target_10": "#7a4e85",
    }
    labels = {
        "futures_trend": "Futures trend: monthly 12m + risk sizing",
        "futures_always_long": "Always-long futures: same risk model",
        "spy_buy_hold": "SPY buy-and-hold incl. dividends",
        "spy_target_10": "SPY 10% vol target, max 100% invested",
    }
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True, layout="constrained")
    for name, series in curves.items():
        axes[0].plot(
            series.index,
            series / series.iloc[0],
            label=labels[name],
            color=colors[name],
            linewidth=1.5,
            linestyle="--" if name == "futures_always_long" else "-",
        )
        axes[1].plot(
            series.index,
            series / series.cummax() - 1,
            color=colors[name],
            linewidth=1.25,
            linestyle="--" if name == "futures_always_long" else "-",
        )
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Growth of USD 1 (log scale)")
    axes[0].legend(loc="upper left", fontsize=9, frameon=False)
    axes[1].set_ylabel("Close-equity drawdown")
    axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    axes[1].set_xlabel("Date")
    dates = curves.index
    axes[1].set_xticks(dates[np.linspace(0, len(dates) - 1, 6, dtype=int)])
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        f"{market_count}-market futures research prototype vs S&P 500 ETF\n{dates[0].date()}–{dates[-1].date()} | Modeled costs, zero cash yield; no independent OOS",
        fontsize=14,
    )
    fig.savefig(OUT / "comparison.png", dpi=160)
    fig.savefig(OUT / "comparison.svg")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw_manifest = json.loads((RAW / "download_manifest.json").read_text())
    for record in raw_manifest["files"]:
        if "sha256" in record and digest(RAW / record["path"]) != record["sha256"]:
            raise ValueError("Raw source fingerprint changed")
    adjusted, raw_prices, rolls, points, costs, groups, spy, staleness = build_panels()
    staleness.to_csv(OUT / "staleness.csv", index=False)
    cfg = Config()
    curves, metrics = {}, {}
    for name, always_long in [("futures_trend", False), ("futures_always_long", True)]:
        print(f"Running {name}...", flush=True)
        ledger, positions, decisions, pnl, fees = simulate(
            adjusted, raw_prices, rolls, points, costs, groups, cfg, always_long
        )
        curves[name] = ledger.equity
        stats = equity_metrics(ledger.equity)
        stats.update(
            gross_pnl=float(ledger.gross_pnl.sum()),
            rebalance_cost=float(ledger.rebalance_cost.sum()),
            roll_cost=float(ledger.roll_cost.sum()),
            average_gross_notional=float(ledger.gross_notional_ratio.mean()),
            maximum_gross_notional=float(ledger.gross_notional_ratio.max()),
            maximum_margin_proxy=float(ledger.margin_proxy_ratio.max()),
            margin_proxy_breach_sessions=int(
                ledger.margin_proxy_ratio.gt(cfg.margin_proxy_limit).sum()
            ),
            monthly_decisions=int(decisions.reason.eq("monthly").sum()),
            emergency_decisions=int(
                decisions.reason.eq("margin_proxy_reduction").sum()
            ),
        )
        metrics[name] = stats
        ledger.to_csv(OUT / f"{name}_daily.csv")
        positions.to_parquet(OUT / f"{name}_positions.parquet")
        decisions.to_csv(OUT / f"{name}_decisions.csv", index=False)
        pnl.to_parquet(OUT / f"{name}_market_pnl.parquet")
        fees.to_parquet(OUT / f"{name}_market_costs.parquet")
        pd.DataFrame(
            dict(
                gross_pnl=pnl.sum(),
                costs=fees.sum(),
                net_pnl=(pnl - fees).sum(),
                asset_class=groups,
            ),
            index=adjusted.columns,
        ).to_csv(OUT / f"{name}_contributions.csv")
    anchor = curves["futures_trend"].index[0]
    benchmark_series = spy.loc[: adjusted.index[-1]]
    for name, target in [("spy_buy_hold", None), ("spy_target_10", 0.10)]:
        ledger = spy_benchmark(
            benchmark_series, anchor, cfg.capital, target_volatility=target
        )
        curves[name] = ledger.equity
        stats = equity_metrics(ledger.equity)
        stats["execution_cost"] = float(ledger.execution_cost.sum())
        metrics[name] = stats
        ledger.to_csv(OUT / f"{name}_daily.csv")
    curves = pd.DataFrame(curves)
    if curves.isna().any().any():
        raise ValueError("Comparison date alignment failed")
    for name in metrics:
        metrics[name]["correlation_to_spy"] = float(
            curves[name].pct_change().corr(curves.spy_buy_hold.pct_change())
        )
    curves.to_parquet(OUT / "equity_curves.parquet")
    returns = curves.pct_change().iloc[1:]
    annual = (1 + returns).groupby(returns.index.year).prod() - 1
    annual.to_csv(OUT / "annual_returns.csv", index_label="year")
    table = pd.DataFrame(metrics).T
    table.to_csv(OUT / "metrics.csv", index_label="strategy")
    (OUT / "metrics.json").write_text(
        json.dumps(metrics, indent=2, allow_nan=False), encoding="utf-8"
    )
    chart(curves, len(adjusted.columns))
    source_files = [
        "run/futures_fetch.py",
        "run/futures_audit.py",
        "run/futures_backtest.py",
        "src/ath_breakout/research/trend_following_futures/model.py",
        "tests/research/test_futures_trend.py",
        "research/trend_following_futures/BASELINE_V001_PLAN.md",
        "research/trend_following_futures/DATA_AUDIT.md",
        "research/trend_following_futures/universe.json",
    ]
    manifest = dict(
        source_repository=raw_manifest["repository"],
        source_commit=COMMIT,
        source_download_manifest_sha256=digest(RAW / "download_manifest.json"),
        source_audit_sha256=digest(
            ROOT / "outputs/trend_following_futures/source_audit/coverage.csv"
        ),
        data_source="Public shipped pysystemtrade CSV research snapshot; no broker connection",
        config=asdict(cfg),
        roots=list(adjusted.columns),
        provider_mapping={r: MAPPING[r] for r in adjusted.columns},
        exclusions=staleness.loc[~staleness.eligible].to_dict("records"),
        point_values=dict(zip(adjusted.columns, points.tolist())),
        one_way_unit_costs=dict(zip(adjusted.columns, costs.tolist())),
        valuation_anchor=str(anchor.date()),
        first_execution=str(curves.index[1].date()),
        last_date=str(curves.index[-1].date()),
        modeled_settlement="last source-date mark; next full NYSE-session close execution",
        unit_rounding="fractional source research units",
        cash_yield=0,
        margin="illustrative 10%-of-gross proxy, no historical margin schedules",
        independent_oos=False,
        code_sha256={p: digest(ROOT / p) for p in source_files},
        git_head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        versions=dict(pandas=pd.__version__, numpy=np.__version__),
        output_sha256={
            p.name: digest(p)
            for p in OUT.iterdir()
            if p.is_file() and p.name != "manifest.json"
        },
    )
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8"
    )
    display = table[
        [
            "cagr",
            "annualized_volatility",
            "sharpe",
            "max_drawdown",
            "final_equity",
            "correlation_to_spy",
        ]
    ]
    report = [
        "# Futures trend v001: first research prototype",
        "",
        "Exploratory market-level futures simulation, not a validated executable futures track record. No optimization or independent OOS.",
        "",
        f"Common equity anchor {anchor.date()}, first execution {curves.index[1].date()}, last mark {curves.index[-1].date()}. {len(adjusted.columns)} eligible market families of 20 candidates; initial capital USD 10 million.",
        "EUR, JPY and CORN were excluded before portfolio performance calculation because priced-mark gaps exceeded the frozen three-session limit.",
        "Monthly own-market 12-calendar-month direction, long/short; 60-session volatility/covariance, 10% target, sector allocation and caps.",
        "Signal at close D executes close D+1 and first earns D+1 to D+2 changes. Negative adjusted levels are permitted; only price differences drive P&L and trend.",
        "",
        "## Comparison",
        "",
        "Rates are decimal fractions (0.01 = 1%). SPY includes dividends; all cash yields are zero.",
        "",
        display.to_markdown(),
        "",
        "## Annual returns",
        "",
        annual.to_markdown(),
        "",
        "## Interpretation boundaries",
        "",
        "The always-long futures control uses the same sizing model, helping distinguish direction from diversified risk allocation.",
        "SPY buy-and-hold is full equity exposure. SPY target_10 uses lagged monthly 60-session volatility scaling, capped at 100% investment; no borrowing.",
        "Realized volatility need not equal 10% or match across portfolios. Treat the full-risk SPY comparison as context, not an alpha test.",
        f"Trend gross notional averaged {metrics['futures_trend']['average_gross_notional']:.2f} NAV and peaked at {metrics['futures_trend']['maximum_gross_notional']:.2f} NAV. The 4x sizing cap applies at decision time, not continuously between monthly trades.",
        "",
        "## Source and data audit",
        "",
        f"[pysystemtrade pinned source](https://github.com/pst-group/pysystemtrade/tree/{COMMIT}/data/futures) supplies adjusted/multiple-price files and roll information.",
        "Comparable adjusted intraday changes were reconciled against same-contract changes or the previous forward on a roll; coverage audit records zero mismatches.",
        "Intraday source dates were collapsed to last valid daily rows. Missing NYSE-session marks were carried only within a three-session threshold; counts are in staleness.csv.",
        "Source history ends March 2024 and common history is constrained by RUSSELL_mini starting March 2015. No claim about performance after March 2024.",
        "Provider rolls are inherited (some commodity histories use seasonal/deferred contracts), not an assumed front-month strategy.",
        "",
        "## Material implementation limitations",
        "",
        "Fractional source units are not integer standard-contract holdings. SILVER source point value is 1,000 oz; standard SI uses another unit size.",
        "Historical product/venue continuity, executable delivery/first-notice compliance, volume and historical spread/margin schedules remain unverified.",
        "One optional RUSSELL_mini roll-calendar CSV is absent; source series transitions are observed from multiple-price IDs.",
        "Fees/spreads are static source estimates per research unit, applied to quantity changes and both roll legs. No fund fees or taxes.",
        "The margin proxy is illustrative, not a broker margin-call/liquidation model. Decisions are delayed one full session; fills at source marks remain an approximation.",
        "Raw data and upstream license remain local and ignored by Git. Source code is independently authored; upstream code is read as documentation, never imported or executed.",
        "",
        "## Reproduce",
        "",
        "```powershell",
        ".venv/Scripts/python.exe run/futures_fetch.py",
        ".venv/Scripts/python.exe -m run.futures_audit",
        ".venv/Scripts/python.exe -m run.futures_backtest",
        "```",
        "",
        "Artifacts: `outputs/trend_following_futures/baseline_v001/`. Frozen methodology: BASELINE_V001_PLAN.md.",
        "",
    ]
    (ROOT / "research/trend_following_futures/BASELINE_V001_RESULTS.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(display.to_string(), flush=True)
    print("Annual returns:", flush=True)
    print(annual.to_string(), flush=True)
    print(f"Artifacts: {OUT}", flush=True)


if __name__ == "__main__":
    main()
