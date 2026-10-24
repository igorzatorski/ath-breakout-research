"""Run the single predeclared SPY SHA EMA(10,10) long/cash baseline offline."""

import hashlib
import json
import subprocess
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


ROOT = Path(__file__).resolve().parents[1]


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / "data/raw/yfinance/SPY.parquet"
    output = ROOT / "outputs/smoothed_heikin_ashi/baseline_ema10_10"
    output.mkdir(parents=True, exist_ok=True)
    raw = pd.read_parquet(source)
    if set(raw.ticker) != {"SPY"} or not raw.prices_split_adjusted.eq(True).all():
        raise ValueError("This baseline requires split-adjusted SPY data only")
    if raw.stock_splits.isna().any() or raw.stock_splits.ne(0).any():
        raise ValueError("Split events require separate accounting, unsupported here")
    prices = raw.set_index(pd.to_datetime(raw.date))
    config = SHAConfig.tradingview_reference()
    execution = ExecutionConfig()
    indicator = smoothed_heikin_ashi(prices, config)
    expected = (
        mcal.get_calendar("NYSE")
        .valid_days(prices.index[0], prices.index[-1])
        .tz_localize(None)
    )
    if not prices.index.equals(expected):
        raise ValueError(
            "Snapshot dates differ from the expected NYSE session calendar"
        )
    start = config.warmup_bars + 1
    hold_signals = pd.Series(1, index=prices.index)
    hold_signals.iloc[: config.warmup_bars] = 0
    results = {}
    ledgers = {}
    for name, signals in [
        ("sha_10_10", indicator.signal),
        ("buy_and_hold", hold_signals),
    ]:
        ledger, fills, trades = simulate_long_cash(prices, signals, start, execution)
        # Independent daily reconciliation from previous-close units and net fills.
        fill_groups = (
            {date: group for date, group in fills.groupby("date")}
            if not fills.empty
            else {}
        )
        for i in range(1, len(ledger)):
            date = ledger.index[i]
            prev = ledger.iloc[i - 1]
            day_fills = fill_groups.get(date, pd.DataFrame())
            expected_cash = prev.cash + prev.units * prices.loc[date, "dividends"]
            expected_units = prev.units
            for fill in day_fills.itertuples():
                expected_cash += fill.cash_flow
                expected_units += fill.units if fill.side == "buy" else -fill.units
            if not np.isclose(expected_cash, ledger.cash.iloc[i], atol=1e-7):
                raise AssertionError("Cash reconciliation failed")
            if not np.isclose(expected_units, ledger.units.iloc[i], atol=1e-9):
                raise AssertionError("Unit reconciliation failed")
            if not np.isclose(
                expected_cash + expected_units * prices.loc[date, "close"],
                ledger.equity.iloc[i],
            ):
                raise AssertionError("Equity reconciliation failed")
        ledger.to_csv(output / f"{name}_daily.csv")
        fills.to_csv(output / f"{name}_fills.csv", index=False)
        trades.to_csv(output / f"{name}_trades.csv", index=False)
        results[name] = summarize(ledger, fills, trades)
        ledgers[name] = ledger
    prices[["open", "high", "low", "close", "dividends"]].join(indicator).to_csv(
        output / "indicator.csv"
    )
    table = pd.DataFrame(results).T
    table.to_csv(output / "metrics.csv", index_label="strategy")
    (output / "metrics.json").write_text(
        json.dumps(results, indent=2, allow_nan=False), encoding="utf-8"
    )
    files = [
        "src/ath_breakout/research/sha/indicator.py",
        "src/ath_breakout/research/sha/backtest.py",
        "run/sha_backtest.py",
        "research/smoothed_heikin_ashi/BASELINE_10_10_PLAN.md",
    ]
    manifest = dict(
        source=str(source),
        source_sha256=fingerprint(source),
        source_start=str(prices.index[0].date()),
        source_end=str(prices.index[-1].date()),
        source_rows=len(prices),
        valuation_anchor=str(ledgers["sha_10_10"].index[0].date()),
        first_execution_session=str(prices.index[start].date()),
        indicator=asdict(config),
        execution=asdict(execution),
        cash_rate=0,
        signal_prices="split-adjusted OHLC; no dividend adjustment",
        dividends="ex-date cash entitlement from prior close holdings; next open reinvestment with costs",
        terminal_policy="mark to close; no liquidation",
        completed_daily_bars=True,
        code_sha256={name: fingerprint(ROOT / name) for name in files},
        git_head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        git_status=subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True
        ).strip(),
        numpy_version=np.__version__,
        pandas_version=pd.__version__,
        validation="NYSE calendar, hand tests, daily cash/units/equity reconciliation",
        research_status="Exploratory full history; no independent OOS; no grid; PyneSys parity unverified",
    )
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    report = [
        "# SPY SHA EMA(10,10): first historical backtest",
        "",
        "Exploratory single configuration. No optimization, grid or independent out-of-sample validation.",
        "",
        f"Source: {manifest['source_start']} through {manifest['source_end']} ({len(prices):,} sessions).",
        f"Initial cash anchor: {manifest['valuation_anchor']}; first execution session: {manifest['first_execution_session']}.",
        "USD 100,000; 10 bps commission + 5 bps adverse slippage per side; zero cash interest.",
        "",
        "## Results",
        "",
        "Returns, CAGR, drawdown, exposure and win rate below are decimal fractions (0.01 = 1%).",
        "Fees and slippage costs are cumulative USD cash amounts, not percentage-point performance attribution.",
        table.T.to_markdown(),
        "",
        "## Interpretation and accounting",
        "",
        f"SHA CAGR is {results['sha_10_10']['cagr']:.2%}, versus {results['buy_and_hold']['cagr']:.2%} for buy-and-hold.",
        f"Maximum drawdowns are {results['sha_10_10']['max_drawdown']:.2%} and {results['buy_and_hold']['max_drawdown']:.2%}, respectively.",
        f"Median completed holding period is {results['sha_10_10']['median_holding_sessions']:.0f} sessions / {results['sha_10_10']['median_holding_calendar_days']:.0f} calendar days.",
        "The baseline sacrifices substantial return for lower drawdown; its historical Sharpe is also lower.",
        "",
        "Signals use completed daily SHA on real split-adjusted OHLC. Green means fully invested, red cash;",
        "neutral retains target. Orders execute on the next real open. No shorts, stops or leverage.",
        "Dividend cash is credited on ex-date to previous-close holders and reinvested at that open",
        "if remaining long. This approximates actual payable-date timing. Reinvestment incurs costs.",
        "Both strategies use the same dates, capital and dividend/cost assumptions.",
        "CAGR uses elapsed calendar years (365.25 days); Sharpe uses 252 sessions, sample standard deviation",
        "and zero risk-free rate. Drawdown is measured at closes, not intraday. Exposure is the fraction",
        "of evaluation closes invested; it does not measure overnight holdings precisely on exit days.",
        "Completed-trade durations exclude the separately marked open trade. Terminal holdings are",
        "valued at the final close, without a hypothetical liquidation charge.",
        "",
        "## Limits",
        "",
        "SPY is an ETF proxy for S&P 500. Results use an existing vendor snapshot ending 2026-10-05;",
        "the source was not refreshed. No independent OOS, statistical alpha test or parameter selection",
        "has been conducted. EMA(10,10) numerical parity against the original PyneSys script is unverified.",
        "A single market and full-period statistics do not demonstrate robustness or a live-ready strategy.",
        "",
        "## Reproduce",
        "",
        "```powershell",
        ".venv/Scripts/python.exe run/sha_backtest.py",
        "```",
        "",
        "Generated ledgers, fills, trades, metrics and manifest:",
        "`outputs/smoothed_heikin_ashi/baseline_ema10_10/` (ignored by Git).",
        f"Source SHA256: `{manifest['source_sha256']}`.",
        "",
    ]
    (ROOT / "research/smoothed_heikin_ashi/BASELINE_10_10_RESULTS.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(
        table[
            [
                "final_equity",
                "cagr",
                "sharpe_252",
                "max_drawdown",
                "completed_trades",
                "median_holding_sessions",
            ]
        ].to_string()
    )
    print(f"Artifacts: {output}")


if __name__ == "__main__":
    main()
