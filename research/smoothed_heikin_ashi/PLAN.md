# Smoothed Heikin Ashi: initial research plan

## Status and scope

The first SPY EMA(10,10) backtest has now been implemented and executed.
Its specific pre-run assumptions supersede the unresolved initial proposals
below: see [baseline plan](BASELINE_10_10_PLAN.md) and
[results](BASELINE_10_10_RESULTS.md). The 20 x 20 grid has subsequently been
authorized and executed separately; see [grid plan](GRID_20_20_PLAN.md) and
[results](GRID_20_20_RESULTS.md).

Implementation update: daily EMA(5) -> HA -> EMA(3) is implemented as an
unoptimized starting configuration, with 50-bar signal warm-up. User target:
trends lasting roughly one week to several months. This does not imply fixed
holding periods. Indicator parity with PyneSys remains unverified.
Unit tests cover manual calculations, causality and input validation; a local
SPY preview exercises the command without performance evaluation.

The user requested a separate SHA research track in this Python repository.
This document defines the work sequence; it does not freeze unconfirmed
instrument, parameter or execution choices.

EMA(10,10), BTC daily from 2018, 10 bps commission and 5 bps slippage were
suggestions in an earlier discussion, not approved baseline settings.
No data acquisition, parameter search or backtest has been performed here.

## 1. Specify and reproduce the indicator

Obtain the intended PyneSys Pine source/version and actual indicator settings.
Record the moving-average type and length before and after HA transformation,
source OHLC, timeframe, initialization, warm-up, missing-value handling and the
rule for equal SHA open/close. Check any higher-timeframe requests and whether
the source uses unconfirmed bars or future information.

Implement only the required configuration first in Python. Confirm causality:
appending or changing future observations must not change earlier outputs.
Compare numeric values and candle direction with a TradingView reference using
matching input data and sufficient shared warm-up history. Vendor differences
must not be mistaken for calculation errors. Until checked, label parity
unverified; a generic double-smoothed HA is not a verified PyneSys replica.

## 2. Freeze one simple baseline before viewing performance

Specify the instrument, venue/data source, timeframe, sample dates, timezone,
bar boundaries, missing-bar policy and price-adjustment policy.
Record signal rules, initial position, sizing, neutral-candle behavior, costs,
cash return, terminal valuation and benchmark treatment.

Proposed starting design, pending specification: long/cash, no leverage,
confirmed SHA direction at close, execution at the next real bar open.
Decide explicitly whether initial green state permits entry or a new color
transition is required. Do not trade during warm-up.

Use synthetic SHA values only for signals. Fill orders and value holdings using
real instrument prices. Include per-side fees and adverse slippage; reconcile
cash, units and equity on a small hand-calculated example.
For crypto, define daily boundaries and calendar-day annualization explicitly.

## 3. Run and document the baseline

Save source snapshot fingerprints, configuration, code revision, date coverage,
warm-up exclusions, signals, orders, fills, holdings and equity.
Compare with buy-and-hold on the same evaluation dates and cost conventions.
Report CAGR, maximum drawdown, Sharpe with explicit annualization/risk-free
assumptions, exposure, turnover, trade count and trade-return distribution.
Distinguish open positions from completed trades.

Report historical results as exploratory. Before parameter selection, document
which history has already been inspected and reserve any feasible untouched
validation period. Do not relabel an inspected period as independent OOS.

## 4. Subsequent experiments

Only after the baseline is reproducible, predeclare a bounded sensitivity study
and retain all tested variants. Filters, ATR stops, shorts, leverage and other
instruments are separate experiments; they are outside the first milestone.

## Immediate missing inputs

- Intended indicator source/version and actual smoothing settings.
- First instrument and timeframe.

Library choice follows execution requirements. No new backtesting dependency
is required merely to create this research track.
