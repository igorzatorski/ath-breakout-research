# Cross-market SHA diagnostic: predeclared extension

2026-10-24, before viewing BTC/QQQ performance.

User requested BTC and Nasdaq tests, full per-configuration trade statistics,
and an explanation of SPY drawdown. Keep SPY grid and saved artifacts intact.

## Markets and data

- SPY: reuse the exact previous source and 400-pair results.
- QQQ: Nasdaq-100 ETF proxy, not Nasdaq Composite. The existing QQQ snapshot
  lacks dividend actions. Obtain a separate public Yahoo daily snapshot with
  unadjusted-for-dividends OHLC plus actions, without overwriting that file.
- BTC-USD: public Yahoo daily USD spot reference, not a specific exchange's
  guaranteed execution prices; no dividends or splits. Retain source timezone.
- Cut off both new sources at 2026-10-05 (end exclusive 2026-10-06), matching
  the SPY cutoff. Use all available history per source, with 50 initial bars of
  warm-up and first execution on the next bar. Native-history comparisons have
  different periods; do not attribute differences solely to market identity.
- Add a common-history comparison of SPY/QQQ/BTC for fixed EMA(10,10) only,
  starting on the first common calendar date after every source's 50-bar warm-up
  and ending 2026-10-05. Calculate indicators on their full prior history but
  reset portfolio state/capital for the shared evaluation. ETF executions use
  real sessions and BTC includes weekends; no invented equity bars.

## Fixed strategy and statistics

Identical pre/post EMA grid 1..20 (400 pairs for each new market), signal rules,
100% long/cash, next-real-open execution, fee 10 bps + slippage 5 bps per side,
fractional quantities, zero cash interest, neutral-state handling, dividends
and terminal valuation as the SPY baseline. No stop is added.
QQQ data are split-adjusted by Yahoo; explicit split events are not additional
share multiplication. Verify the provider convention and any split dates before
use. Reject incomplete actions rather than silently assume zero dividends.

BTC Sharpe uses 365 observations/year, ETFs 252; CAGR uses elapsed calendar time.
Report calendar-day durations for comparisons. Annualization is metadata, not
a selected parameter. Cost levels are a controlled assumption, not broker quotes.

For every one of the 400 pairs in every market retain win rate, completed trade
count, mean/median holding sessions and calendar days, mean net trade return,
mean winning/losing return, worst trade, dollar profit factor, exposure, CAGR,
Sharpe and drawdown. Win rate excludes open positions; all trade returns include
the configured costs/dividend accounting. Dollar profit factor is sum of positive
completed-trade dollar P&L divided by absolute sum of negative dollar P&L.

Save full metric CSV/parquet, trade/equity artifacts, at least win-rate and
mean-duration matrices alongside return/risk maps. Compare EMA(10,10) and the
full-sample leaders with the ledger simulator. State that leaders are chosen
after the fact and neither independent OOS validation nor production choices.

## SPY drawdown explanation

Trace the actual 10/10 and 18/20 maximum close-equity drawdowns: peak, trough,
recovery, affected transactions and worst single trade. Distinguish portfolio
drawdown across multiple trades from stop distance or loss on a single trade.
Explain lag, next-open gaps, false starts and opportunity cost using observed
events where possible. Saved per-trade losses and the equity path control the
explanation; do not attribute everything to bull markets without evidence.
