# Nasdaq-100 replication and next research steps

QQQ is the Nasdaq-100 ETF proxy, not Nasdaq Composite. Public Yahoo data
downloaded 2026-10-22, capped at 2026-10-05 to match the saved SPY dataset.
Identical 6,872 eligible signal dates: 1999-06-03 through 2026-09-28.
Entry next open, exit fifth close, adjusted return proxy. No stops or leverage.

## All qualifying signal days (overlapping)

| Market | Window | Threshold | N | Mean 5-session return | Win rate |
|---|---:|---:|---:|---:|---:|
| QQQ unconditional | - | - | 6872 | 0.213% | 56.8% |
| QQQ | 30 | -1 | 1360 | 0.498% | 56.6% |
| QQQ | 30 | -2 | 350 | 0.893% | 59.4% |
| QQQ | 60 | -1 | 1252 | 0.224% | 53.8% |
| QQQ | 60 | -2 | 311 | 0.644% | 60.1% |
| SPY unconditional | - | - | 6872 | 0.161% | 57.3% |
| SPY | 30 | -2 | 384 | 0.686% | 58.3% |

QQQ 30/-2 non-overlapping: 147 trades, mean 0.893%, win rate 60.5%,
worst -15.82%, 5th percentile -5.12%. Illustrative 20bps round-trip costs
reduce mean to 0.693%; funding and derivative-specific costs are excluded.
The 20-session-block bootstrap 95% interval for QQQ 30/-2 excess over the
unconditional mean is +0.143 to +1.210 percentage points. Other QQQ variants'
excess intervals include zero. No adjustment for multiple comparisons.

The result supports continued research into short-term rebounds, not a validated
strategy or superiority to SPY: larger raw returns need risk normalization.
QQQ and SPY are correlated; replication is not independent market evidence.
Non-overlapping return samples are not portfolio return series.

## Proposed sequence (not yet tested)

1. Fix entry, compare 1/3/5/10-session forward returns; measure post-entry
   maximum adverse and favorable excursions. Do rebounds arrive promptly?
2. Compare distinct signal families separately: price Z-score, short RSI,
   volatility-scaled cumulative return shock. Avoid a full parameter grid.
3. Test one predeclared regime split at a time: above/below 200-session SMA,
   then low/high lagged realized volatility. Keep all regime results.
4. Compare all oversold days, first threshold crossings, and wait-for-recovery
   entries. Account for execution delay and reduced signal counts.
5. Freeze one rule and assess chronological stability and genuinely unseen
   future observations. Already inspected historical periods are not untouched.
6. Only then assess portfolio exposure, drawdowns, costs, stops, futures/CFDs
   and position size. Daily OHLC cannot resolve intraday stop/target ordering;
   gaps may execute beyond stops.

For every test retain sample size, mean and median, win rate, average win/loss,
tails, time in market, and dependence-aware confidence intervals. Compare with
unconditional windows and, where appropriate, equal-volatility exposure.
