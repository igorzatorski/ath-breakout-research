# Mean-reversion extension: findings

Study v003, 2026-10-22. Twelve variants per ETF, SPY and QQQ. Common signal
dates 2000-04-05 to 2026-09-21, outcomes through 2026-10-05. The later start
allows all indicators to warm up; these results are not directly identical
to earlier samples starting in 1993 or 1999. Rules in EXTENDED_PLAN.md;
complete tables in EXTENDED_RESULTS.md; machine-readable artifacts and
event/equity ledgers in outputs/zscore/v003.

## Main findings

- QQQ 30-session Z <= -2 shows the clearest continued rebound across 1/3/5/10
  sessions. On identical qualifying dates the gross mean rises from 0.317%
  to 0.546%, 0.893%, and 1.424%. Longer holds also increase adverse excursion.
- The sequential non-overlapping QQQ 10-session sample has 112 trades,
  1.261% mean net of 10bps each side, 58.9% winners before costs, and a
  -14.72% worst gross terminal return. This does not prove 10 sessions optimal.
- QQQ high-volatility oversold days have stronger mean returns than the
  low-volatility subset. This is exploratory regime evidence, not a proven
  difference or a reason to multiply position size.
- Buying after Z recovers above -2 hurts the observed results: QQQ mean net
  -0.368% and SPY +0.040% per non-overlapping trade. First down-cross entries
  also do not improve the base case.
- SPY RSI2 <= 10 is a useful alternative: 334 non-overlapping trades, mean net
  0.268%; subperiod net means 0.273%, 0.252%, 0.273%. QQQ RSI is weaker:
  mean net 0.116%, and -0.184% in the 2018-end subperiod.
- The volatility-scaled five-day shock is not consistently useful: SPY mean
  net -0.204%; QQQ +0.506%, with its excess confidence interval sensitive to
  bootstrap block length.

## Path risk and capital use

At the base five-session entry, median adverse excursion in non-overlapping
trades is -1.79% SPY / -2.22% QQQ. Across all signal days, the 5th percentile
of adverse excursion is -9.21% / -9.97%. Thus positive average final returns
coexist with substantial interim losses. Excursions use daily adjusted OHLC;
they cannot establish the intraday sequence of highs and lows or stop fills.

With 100% unlevered capital in each trade, zero cash yield and 10bps each side:

| Rule | Net CAGR | Close-to-close max drawdown | Occupied sessions |
|---|---:|---:|---:|
| SPY Z30/-2, 5 sessions | 2.11% | -25.61% | 11.86% |
| SPY RSI2/10, 5 sessions | 2.82% | -33.95% | 25.06% |
| SPY buy-and-hold, gross | 8.27% | -55.19% | 100% |
| QQQ Z30/-2, 5 sessions | 3.39% | -26.37% | 11.03% |
| QQQ Z30/-2, 10 sessions | 4.67% | -32.75% | 16.81% |
| QQQ Z30/-2 high volatility, 5 sessions | 4.35% | -23.69% | 7.05% |
| QQQ buy-and-hold, gross | 8.54% | -81.19% | 100% |

Buy-and-hold begins near the dot-com peak, so its drawdown and annual return
are particularly start-date-sensitive. Occupied-session percentage is not
precise clock-time exposure. Daily close drawdown understates possible
intraday loss. Low exposure does not by itself establish risk-adjusted alpha.

## Evidence limits

All signal-day bootstrap intervals are pointwise and unadjusted for the many
comparisons. For SPY the base five-session excess interval includes zero with
20-session blocks and excludes zero narrowly with 60-session blocks; it is
not robust statistical confirmation. QQQ base horizons and high-volatility
subset have positive excess intervals under both block lengths, but SPY and
QQQ are correlated and historical choices have already been inspected.
Subperiod performance is descriptive, not an untouched holdout.

Non-overlap selection changes which signals enter each variant. Therefore
differences between those means cannot isolate the causal effect of one
filter or holding period. Use identical-date all-signal horizon comparisons
alongside the implementable sequential trade samples.

No future observation, derivative financing/roll model, margin rule, stop-loss
execution or leveraged strategy has been validated by this study.

## Verification

Eight tests passed, including independent Wilder RSI, forward-return/path
formulas, future-data invariance and overnight-gap accounting. Ruff passed.
Both source files contain every expected NYSE session in their coverage.
One hundred sampled ledger paths were independently recalculated from source
OHLC. All 24 daily equity curves reconciled to compounded net trade returns.
No pre-existing ATH or earlier Z-score results were overwritten.

Reproduce: `.venv/Scripts/python.exe scripts/research/study_mean_reversion.py`.
