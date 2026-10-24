"""Declared cross-market grid, per-pair trade statistics and drawdown audit."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from ath_breakout.research.sha import SHAConfig, smoothed_heikin_ashi
from ath_breakout.research.sha.backtest import (
    ExecutionConfig,
    simulate_long_cash,
    summarize,
)
from ath_breakout.research.sha.diagnostics import (
    annual_comparison,
    drawdown_episode,
    trade_statistics,
)
from ath_breakout.research.sha.grid import build_signals, simulate_grid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/smoothed_heikin_ashi/cross_market"
SOURCES = dict(
    SPY="SPY.parquet",
    QQQ="sha_QQQ_20261005.parquet",
    BTC_USD="sha_BTC_USD_20261005.parquet",
)
ANNUALIZATION = dict(SPY=252, QQQ=252, BTC_USD=365)


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")


def finite_dict(row):
    return {
        k: None if pd.isna(v) else v.item() if isinstance(v, np.generic) else v
        for k, v in row.items()
    }


def plot_statistics(metrics, asset, directory, first_date, last_date):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    # One shared scale per metric, identical axes; every observed pair retained.
    panels = [
        ("cagr", "CAGR after costs", True),
        ("sharpe", "Annualized Sharpe", False),
        ("win_rate", "Win rate: completed net trades", True),
        ("mean_holding_calendar_days", "Mean holding period: calendar days", False),
        ("max_drawdown", "Maximum close-equity drawdown", True),
        ("completed_trades", "Completed trades", False),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(17, 11))
    fig.subplots_adjust(
        left=0.065, right=0.965, bottom=0.09, top=0.87, wspace=0.40, hspace=0.36
    )
    for ax, (field, title, percent) in zip(axes.flat, panels):
        matrix = metrics.pivot(index="pre_span", columns="post_span", values=field)
        assert matrix.shape == (20, 20) and matrix.notna().all().all()
        image = ax.imshow(
            matrix, origin="lower", extent=(0.5, 20.5, 0.5, 20.5), cmap="viridis"
        )
        ax.set(title=title, xlabel="EMA after HA", ylabel="EMA before HA")
        ax.set_xticks([1, 5, 10, 15, 20])
        ax.set_yticks([1, 5, 10, 15, 20])
        ax.scatter([10], [10], marker="s", facecolors="none", edgecolors="white", s=85)
        bar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.025)
        if percent:
            bar.ax.yaxis.set_major_formatter(PercentFormatter(1))
    fig.suptitle(
        f"{asset}: 400 SHA EMA configurations | {first_date}–{last_date}\nExploratory full history; square = 10/10; panel color scales differ",
        fontsize=15,
    )
    fig.supxlabel(
        f"Next-open fills · 0.10% commission + 0.05% slippage per side · cash yield 0% · Sharpe annualization {ANNUALIZATION[asset]} bars/year",
        fontsize=10,
    )
    fig.savefig(directory / "statistics_maps.png", dpi=150)
    plt.close(fig)


def load_prices(asset):
    path = ROOT / "data/raw/yfinance" / SOURCES[asset]
    raw = pd.read_parquet(path)
    prices = raw.set_index(pd.to_datetime(raw.date))
    smoothed_heikin_ashi(prices, SHAConfig.tradingview_reference())
    required = prices[["open", "close", "dividends", "stock_splits"]].to_numpy(float)
    if (
        not np.isfinite(required).all()
        or not prices.prices_split_adjusted.eq(True).all()
    ):
        raise ValueError("Incomplete adjusted prices/actions")
    if "capital_gains" in prices and prices.capital_gains.ne(0).any():
        raise ValueError("Nonzero capital gain distributions need explicit accounting")
    if asset == "BTC_USD":
        expected = pd.date_range(prices.index[0], prices.index[-1], freq="D")
        if prices.dividends.ne(0).any() or prices.stock_splits.ne(0).any():
            raise ValueError("Unexpected BTC actions")
    else:
        expected = (
            mcal.get_calendar("NYSE")
            .valid_days(prices.index[0], prices.index[-1])
            .tz_localize(None)
        )
        for date in prices.index[prices.stock_splits.ne(0)]:
            i = prices.index.get_loc(date)
            # Yahoo reports already split-adjusted OHLC. Do not double shares.
            ratio = prices.open.iloc[i] / prices.close.iloc[i - 1]
            if i < 1 or not 0.8 < ratio < 1.2:
                raise ValueError("Split-day price discontinuity requires investigation")
    if not prices.index.equals(expected) or prices.index[-1] != pd.Timestamp(
        "2026-10-05"
    ):
        raise ValueError(f"Unexpected {asset} calendar or coverage")
    return path, prices


def plot_spy_drawdowns(episodes):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), layout="constrained")
    for ax, pair in zip(axes, [(18, 20), (10, 10)]):
        episode = next(
            e
            for e in episodes
            if e["asset"] == "SPY" and (e["pre_span"], e["post_span"]) == pair
        )
        ledger = pd.read_csv(
            OUT / "SPY" / f"checked_{pair[0]}_{pair[1]}_daily.csv", parse_dates=["date"]
        ).set_index("date")
        curve = ledger.equity.loc[episode["peak_date"] : episode["trough_date"]]
        curve = curve / curve.iloc[0] * 100
        ax.plot(curve.index, curve, color="#245788", linewidth=1.5)
        ax.axhline(100, color="#4b5563", linestyle="--", linewidth=1)
        ax.scatter([curve.index[-1]], [curve.iloc[-1]], color="#b57828", s=40, zorder=3)
        ax.annotate(
            f"{episode['max_drawdown']:.2%}",
            xy=(curve.index[-1], curve.iloc[-1]),
            xytext=(-65, 12),
            textcoords="offset points",
            fontsize=11,
        )
        ax.set(
            title=f"SHA {pair[0]}/{pair[1]} | {episode['peak_date']} to {episode['trough_date']}",
            ylabel="Portfolio equity (previous peak = 100)",
            ylim=(60, 103),
            xlabel="Date",
        )
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.set_xticks(curve.index[np.linspace(0, len(curve) - 1, 4, dtype=int)])
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("SPY: maximum portfolio drawdown spans multiple trades", fontsize=15)
    fig.supxlabel(
        "Real close-equity paths; costs and dividends included. SHA color reversal is not a fixed stop-loss.",
        fontsize=10,
    )
    fig.savefig(OUT / "SPY" / "drawdown_explanation.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    config = ExecutionConfig()
    sources, prices_by_asset, summaries, comparisons = {}, {}, {}, []
    drawdowns = []
    for asset in SOURCES:
        print(f"{asset}: loading and validating source...", flush=True)
        source, prices = load_prices(asset)
        sources[asset] = dict(
            path=str(source),
            sha256=hash_file(source),
            rows=len(prices),
            start=str(prices.index[0].date()),
            end=str(prices.index[-1].date()),
        )
        prices_by_asset[asset] = prices
        directory = OUT / asset
        directory.mkdir(exist_ok=True)
        if asset == "SPY":
            original = ROOT / "outputs/smoothed_heikin_ashi/grid_20_20"
            old_manifest = json.loads((original / "manifest.json").read_text())
            if old_manifest["source_sha256"] != sources[asset]["sha256"]:
                raise ValueError("SPY source changed")
            metrics = pd.read_parquet(original / "all_400_metrics.parquet")
            equity = pd.read_parquet(original / "daily_equity.parquet")
            trades = pd.read_parquet(original / "all_trades.parquet")
            exposure = pd.read_parquet(original / "daily_exposure.parquet")
        else:
            print(f"{asset}: running all 400 pairs...", flush=True)
            signals = build_signals(prices)
            metrics, equity, exposure, trades = simulate_grid(
                prices, signals, 51, config
            )
            equity.columns = [f"pre_{a}_post_{b}" for a, b in equity.columns]
            exposure.columns = equity.columns
            signals.columns = equity.columns
            signals.to_parquet(directory / "signals.parquet")
        metrics = trade_statistics(metrics, trades)
        scale = np.sqrt(ANNUALIZATION[asset] / 252)
        metrics["sharpe"] = metrics.pop("sharpe_252") * scale
        metrics["sharpe_annualization"] = ANNUALIZATION[asset]
        metrics["cagr_rank"] = metrics.cagr.rank(ascending=False, method="min").astype(
            int
        )
        metrics["sharpe_rank"] = metrics.sharpe.rank(
            ascending=False, method="min"
        ).astype(int)
        hold_ledger, hold_fills, hold_trades = simulate_long_cash(
            prices, pd.Series(1, index=prices.index), 51, config
        )
        benchmark = summarize(hold_ledger, hold_fills, hold_trades)
        benchmark["sharpe"] = benchmark.pop("sharpe_252") * scale
        benchmark["sharpe_annualization"] = ANNUALIZATION[asset]
        write_json(directory / "benchmark.json", benchmark)
        hold_ledger.to_csv(directory / "buy_and_hold_daily.csv")
        selected = {(10, 10), (18, 20)} if asset == "SPY" else {(10, 10)}
        for field in ["cagr", "sharpe"]:
            leaders = metrics.loc[
                np.isclose(metrics[field], metrics[field].max(), rtol=0, atol=1e-12)
            ]
            selected.update(
                (int(r.pre_span), int(r.post_span)) for r in leaders.itertuples()
            )
        print(f"{asset}: reference ledger checks {sorted(selected)}...", flush=True)
        for before, after in sorted(selected):
            signals_one = smoothed_heikin_ashi(prices, SHAConfig(before, after)).signal
            ledger, fills, reference_trades = simulate_long_cash(
                prices, signals_one, 51, config
            )
            actual = metrics.loc[
                metrics.pre_span.eq(before) & metrics.post_span.eq(after)
            ].iloc[0]
            np.testing.assert_allclose(
                ledger.equity,
                equity[f"pre_{before}_post_{after}"],
                rtol=1e-10,
                atol=1e-7,
            )
            for field, expected in summarize(ledger, fills, reference_trades).items():
                key = "sharpe" if field == "sharpe_252" else field
                value = (
                    expected * scale
                    if field == "sharpe_252" and expected is not None
                    else expected
                )
                if value is not None:
                    np.testing.assert_allclose(
                        actual[key],
                        value,
                        rtol=1e-9,
                        atol=1e-7,
                        err_msg=f"{asset} {before}/{after} {field}",
                    )
            ledger.to_csv(directory / f"checked_{before}_{after}_daily.csv")
            fills.to_csv(directory / f"checked_{before}_{after}_fills.csv", index=False)
            episode = drawdown_episode(ledger.equity)
            episode.update(asset=asset, pre_span=before, post_span=after)
            subset = trades.loc[trades.pre_span.eq(before) & trades.post_span.eq(after)]
            window = subset.loc[
                subset.entry_date.le(pd.Timestamp(episode["trough_date"]))
                & (
                    subset.exit_date.ge(pd.Timestamp(episode["peak_date"]))
                    | subset.exit_date.isna()
                )
            ]
            window.to_csv(
                directory / f"drawdown_{before}_{after}_overlapping_trades.csv",
                index=False,
            )
            episode["overlapping_trades"] = len(window)
            drawdowns.append(episode)
            annual_comparison(ledger.equity, hold_ledger.equity).to_csv(
                directory / f"annual_{before}_{after}.csv"
            )
        metrics.to_csv(directory / "all_400_metrics.csv", index=False)
        metrics.to_parquet(directory / "all_400_metrics.parquet", index=False)
        trades.to_parquet(directory / "all_trades.parquet", index=False)
        equity.to_parquet(directory / "daily_equity.parquet")
        exposure.to_parquet(directory / "daily_exposure.parquet")
        for field in [
            "cagr",
            "sharpe",
            "max_drawdown",
            "win_rate",
            "mean_holding_sessions",
            "mean_holding_calendar_days",
            "median_holding_calendar_days",
            "completed_trades",
            "mean_trade_return",
            "mean_winner_return",
            "mean_loser_return",
            "profit_factor_dollars",
            "exposure_fraction",
        ]:
            metrics.pivot(index="pre_span", columns="post_span", values=field).to_csv(
                directory / f"matrix_{field}.csv"
            )
        plot_statistics(
            metrics, asset, directory, equity.index[1].date(), equity.index[-1].date()
        )
        summary = dict(
            asset=asset,
            evaluation_start=str(equity.index[1].date()),
            evaluation_end=str(equity.index[-1].date()),
            benchmark=benchmark,
            positive_cagr=int(metrics.cagr.gt(0).sum()),
            beating_hold_cagr=int(metrics.cagr.gt(benchmark["cagr"]).sum()),
            beating_hold_sharpe=int(metrics.sharpe.gt(benchmark["sharpe"]).sum()),
            ema10_10=finite_dict(
                metrics.loc[metrics.pre_span.eq(10) & metrics.post_span.eq(10)]
                .iloc[0]
                .to_dict()
            ),
            best_cagr=finite_dict(metrics.loc[metrics.cagr.idxmax()].to_dict()),
            best_sharpe=finite_dict(metrics.loc[metrics.sharpe.idxmax()].to_dict()),
            cagr_range=[float(metrics.cagr.min()), float(metrics.cagr.max())],
            win_rate_range=[
                float(metrics.win_rate.min()),
                float(metrics.win_rate.max()),
            ],
            reference_checked_pairs=sorted(selected),
        )
        summaries[asset] = summary
        write_json(directory / "summary.json", summary)
        for label, row in [
            ("10/10", summary["ema10_10"]),
            ("best_CAGR", summary["best_cagr"]),
            ("best_Sharpe", summary["best_sharpe"]),
            ("buy_and_hold", benchmark),
        ]:
            comparisons.append(
                dict(
                    asset=asset,
                    variant=label,
                    evaluation_start=summary["evaluation_start"],
                    evaluation_end=summary["evaluation_end"],
                    **row,
                )
            )
        print(
            f"{asset}: 10/10 CAGR {summary['ema10_10']['cagr']:.2%}; hold {benchmark['cagr']:.2%}",
            flush=True,
        )
    # Only fixed 10/10 on the common date range; no new grid selection here.
    eligible = [p.index[51:] for p in prices_by_asset.values()]
    shared = eligible[0].intersection(eligible[1]).intersection(eligible[2])
    shared_start = shared[0]
    common = []
    for asset, prices in prices_by_asset.items():
        bar = int(prices.index.get_loc(shared_start))
        signal = smoothed_heikin_ashi(prices, SHAConfig.tradingview_reference()).signal
        for label, signals_one in [
            ("10/10", signal),
            ("buy_and_hold", pd.Series(1, index=prices.index)),
        ]:
            ledger, fills, trades_one = simulate_long_cash(
                prices, signals_one, bar, config
            )
            stats = summarize(ledger, fills, trades_one)
            stats["sharpe"] = stats.pop("sharpe_252") * np.sqrt(
                ANNUALIZATION[asset] / 252
            )
            common.append(
                dict(
                    asset=asset,
                    variant=label,
                    start=str(shared_start.date()),
                    end=str(prices.index[-1].date()),
                    **stats,
                )
            )
    pd.DataFrame(common).to_csv(OUT / "common_period_10_10.csv", index=False)
    pd.DataFrame(comparisons).to_csv(OUT / "native_history_comparison.csv", index=False)
    pd.DataFrame(drawdowns).to_csv(OUT / "drawdown_episodes.csv", index=False)
    plot_spy_drawdowns(drawdowns)
    write_json(OUT / "summary.json", summaries)
    code = [
        "run/sha_cross_market.py",
        "run/sha_fetch_cross_market.py",
        "src/ath_breakout/research/sha/diagnostics.py",
        "src/ath_breakout/research/sha/grid.py",
        "src/ath_breakout/research/sha/backtest.py",
        "src/ath_breakout/research/sha/indicator.py",
        "research/smoothed_heikin_ashi/CROSS_MARKET_PLAN.md",
    ]
    write_json(
        OUT / "manifest.json",
        dict(
            sources=sources,
            execution=asdict(config),
            annualization=ANNUALIZATION,
            shared_start=str(shared_start.date()),
            per_market_grid_pairs=400,
            no_independent_oos=True,
            code_sha256={p: hash_file(ROOT / p) for p in code},
            artifacts_sha256={
                str(p.relative_to(OUT)): hash_file(p)
                for p in OUT.rglob("*")
                if p.is_file() and p.name != "manifest.json"
            },
        ),
    )
    report = [
        "# SHA cross-market comparison and drawdown diagnostic",
        "",
        "Exploratory 400-pair daily EMA grids. SPY uses the saved grid; QQQ and BTC use separate public snapshots.",
        "QQQ is a Nasdaq-100 ETF proxy, not Nasdaq Composite. BTC-USD is Yahoo's USD reference series, not guaranteed exchange fills.",
        "All data end 2026-10-05. Native histories differ; comparisons below do not isolate a market effect.",
        "Long/cash, next-open fills, fees 10 bps + slippage 5 bps per side, dividends reinvested with costs, zero cash yield.",
        "ETF Sharpe annualization: 252; BTC: 365. CAGR uses elapsed calendar time. All strategies start after 50 warm-up bars.",
        "",
        "## Native-history comparison",
        "",
        "Rates below are decimal fractions (0.01 = 1%). Means exclude open trades.",
        "",
        pd.DataFrame(comparisons)[
            [
                "asset",
                "variant",
                "pre_span",
                "post_span",
                "cagr",
                "sharpe",
                "max_drawdown",
                "win_rate",
                "mean_holding_calendar_days",
                "median_holding_calendar_days",
                "completed_trades",
            ]
        ].to_markdown(index=False),
        "",
        "## Fixed 10/10 on common history",
        "",
        pd.DataFrame(common)[
            ["asset", "variant", "start", "end", "cagr", "sharpe", "max_drawdown"]
        ].to_markdown(index=False),
        "",
        "## Maximum drawdown episodes",
        "",
        pd.DataFrame(drawdowns).to_markdown(index=False),
        "",
        "A portfolio drawdown is measured from its prior equity high, potentially across many trades. It is not a single-trade stop distance.",
        f"SPY 18/20: worst completed trade {summaries['SPY']['best_cagr']['worst_trade_return']:.2%}; maximum losing streak {summaries['SPY']['best_cagr']['maximum_losing_streak']} trades.",
        f"SPY 10/10: worst completed trade {summaries['SPY']['ema10_10']['worst_trade_return']:.2%}; maximum losing streak {summaries['SPY']['ema10_10']['maximum_losing_streak']} trades.",
        "SHA color is a delayed transformation and is not a fixed stop. Red triggers only a next-open sale; gaps and repeated losing re-entries remain possible.",
        "For SPY 10/10 the worst drawdown spans 1999-07-16 to 2009-03-20; worst completed trade is materially smaller than that drawdown.",
        "",
        "## Complete per-pair outputs",
        "",
        "Each asset folder under `outputs/smoothed_heikin_ashi/cross_market/` includes all 400 rows, 13 numeric matrices,",
        "trade ledgers, daily equity/exposure and six-panel maps. Per-pair columns include mean/median duration (sessions and calendar days),",
        "win rate, mean trade/winner/loser returns, worst/best trade, dollar profit factor, exposure and completed/open counts.",
        "Maximum losing streak counts consecutive strictly negative completed trades; break-even trades reset the run.",
        "Profit factor uses dollar P&L; absolute trade sizes vary with accumulated capital. No-loss cases are undefined (missing), not invented ratios.",
        "Open trades are marked to last close and excluded from completed-trade statistics. No final forced-liquidation charge is applied.",
        "",
        "## Data and inference limits",
        "",
        "QQQ has one 2:1 split on 2000-03-20; Yahoo's OHLC is already split-adjusted, so no extra unit doubling is applied.",
        "Corporate-action flags, split-day continuity, complete expected calendars, finite OHLC and source hashes are checked.",
        "Dividend credit on ex-date approximates payable-date timing. BTC uses UTC daily bars; ETFs use exchange sessions.",
        "Same calendar dates do not mean identical observation counts or simultaneous closing timestamps.",
        "Costs are controlled assumptions, not verified broker-specific quotes. PyneSys parity remains unverified.",
        "Grid maxima and neighbor patterns are selected from inspected history and do not establish independent OOS alpha.",
        "",
        "```powershell",
        ".venv/Scripts/python.exe run/sha_fetch_cross_market.py",
        ".venv/Scripts/python.exe run/sha_cross_market.py",
        "```",
        "",
    ]
    (ROOT / "research/smoothed_heikin_ashi/CROSS_MARKET_RESULTS.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(
        pd.DataFrame(comparisons)[
            [
                "asset",
                "variant",
                "pre_span",
                "post_span",
                "cagr",
                "sharpe",
                "max_drawdown",
                "win_rate",
                "mean_holding_calendar_days",
            ]
        ].to_string(index=False),
        flush=True,
    )
    print("Common period:", flush=True)
    print(
        pd.DataFrame(common)[
            ["asset", "variant", "start", "cagr", "sharpe", "max_drawdown"]
        ].to_string(index=False),
        flush=True,
    )


if __name__ == "__main__":
    main()
