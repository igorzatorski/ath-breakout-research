# Mean-reversion study v003

Declared 2026-10-22 before this extension's results. Existing 30/-2 evidence has
already been inspected; this study is exploratory and cannot create an untouched
historical holdout. SPY and QQQ are correlated markets. No parameter search.

Use saved SPY and QQQ Yahoo files, ending 2026-10-05. Require common eligible
dates, 200-session trend and 252-session volatility-history warmup, and complete
10-session outcomes. Preserve earlier artifacts.

One change at a time around close-price Z30 <= -2:
1. Holding periods 1, 3, 5, 10 sessions, next open through Hth close.
2. Adjusted daily low/high maximum adverse/favorable excursion during holding.
3. Above/below current close SMA200; separately high/low realized volatility
   (20-session daily return SD versus its trailing 252-session median, shifted
   one session). Compare with unconditional windows in the SAME regime.
4. All qualifying days, first down-cross below -2, and first recovery above -2
   following an oversold day. Entry always next open. Recovery may occur much later.
5. RSI2 <= 10 (Wilder recursion alpha=1/2, initial seed first 2 moves);
   five-session adjusted return <= -2 times preceding 60-session daily SD times
   sqrt(5), with volatility lagged five sessions to precede the entire shock.
6. Periods <=2009, 2010-2017, >=2018; report all, no rule selection.

All variants: full qualifying sample and sequential non-overlapping trades;
mean/median, hit rate, average gain/loss, return SD, 5th percentile/worst,
MAE/MFE, illustrative net mean at 10/20/40bps round trip. No financing model.
Dependence-aware paired moving-block bootstrap (20/60 sessions, 2000 draws,
seed 42) of conditional-minus-regime-unconditional return for all signal days.
Intervals are pointwise, unadjusted for multiple comparisons. Do not imply
statistical superiority between variants from separate intervals.

Calendar-time diagnostic for non-overlapping trades: 100% unlevered capital
per trade, 10bps each side, cash return zero, daily marked-to-market equity,
CAGR, max drawdown and occupied-session fraction versus buy-and-hold on same
dates. This is a stylized ETF backtest; no stops, leverage or derivatives.
Truly unseen future performance cannot be tested today. Save code, manifest,
event and daily-equity ledgers and English results. Check independent formulas,
timing, future invariance, gap exposure and trade/equity reconciliation.
