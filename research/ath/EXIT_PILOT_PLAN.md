# Fixed exit-family pilot

Study: `high_03_exit_families_pilot_v001`. Defined 2026-10-15 before exit results.

## One research question

With the same qualified local-history ATH entries, does a simple asymmetric
exit improve net event outcomes versus a fixed holding period?

We are comparing exit families, not optimizing parameters. No new entry filters,
ranking, signal definition, sizing, shorting or portfolio construction. The
previous 52W and path studies are exploratory context, not additional knobs.

## Frozen sample and three rules

Source: `high_01_52w_vs_ath_pilot_v001/20261015T205046302698Z`,
group `ath_local_history` only. Signals in 2024. Same next-session observed open.
126-session maximum holding period. No re-entry within an event; repeated source
events remain independent hypothetical positions, not executable portfolio slots.

1. `hold_126`: exit at close of holding session 126, or CIZ terminal event earlier.
2. `failed_breakout`: closing price below frozen prior local ATH creates an exit
   order for the immediately following exchange-session opening. Otherwise hold
   through session 126. Do not sell at the trigger's close.
3. `atr_trend`: compute a 20-session SIMPLE mean true range at signal close,
   including signal day, on CRSP comparable high/low/previous-close prices.
   Freeze this ATR throughout the event. Initial level = entry comparable open
   minus 2 ATR. Trailing level = highest comparable CLOSE observed since entry
   (including entry open as initial anchor) minus 3 ATR. Effective level is the
   maximum of these two levels and zero. A close STRICTLY below it creates a
   next-session opening exit. No intraday stop assumption or parameter search.
   These values are starting conventions, not optimized or established optima.

Ordinary closing triggers preserve ex-date distribution entitlement at a later
opening exit. Opening proceeds use previous closing wealth times current
comparable opening plus comparable ordinary/nonordinary distributions divided
by previous comparable close. No exit-day closing return is used. CRSP CIZ
terminal Y returns are compounded once, then proceeds are held as zero-interest
cash to session 126. Missing scheduled exit opening without terminal settlement
is an explicit unresolved case, not a stale/later fill.

## Comparisons and limits

- Use the common executable sample across all variants. Report exclusions.
- Stock costs: 10 bps at entry and exit, applied to wealth multiplicatively.
- Show gross/net mean, median, loss frequency, loss-tail quantile, large gains,
  holding time and paired differences versus `hold_126`.
- Benchmark both full 126-session SPY and SPY held over each variant's exact
  entry/exit window with matching opening/closing exit and ex-date entitlement.
  Both cash balances earn zero interest. SPY is gross; this is conservative
  stock-cost sensitivity, not risk-adjusted alpha.
- Show equal-security weighting as sensitivity, not a portfolio backtest.
- Compare which fixed-hold big winners survive; retrospective labels remain
  explanatory only. No exits are designed using the identity of those winners.
- No CAGR/Sharpe, significance or best-strategy claim from this single previously
  viewed year. The next step is assessment on other predefined periods using
  frozen rules, before any parameter tuning with separate validation.
