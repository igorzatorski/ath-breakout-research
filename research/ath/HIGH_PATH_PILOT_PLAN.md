# Breakout path diagnostic protocol

Study: `high_02_paths_pilot_v001`. Defined 2026-10-15 before path results.
Use the exact frozen 2024 event sample from `high_01_52w_vs_ath_pilot_v001`,
run `20261015T205046302698Z`. No signal reselection or parameter optimization.

Questions:

1. How much do eventual winners retreat before appreciating?
2. Does a closing return below the frozen breakout level identify losers?
3. Does the early warning predict returns occurring AFTER it is observable?

Definitions:

- Follow from observed next-session open through the 126th holding-session close.
- Primary focus: `ath_local_history`; show `52w_only`, `ath_uncertain`, all 52W
  separately. Maintain the historical ATH qualifications from the source study.
- Big winner: total return at session 126 >=20%; loser: total return <0%;
  other: 0% through <20%. Labels are retrospective descriptions, never signals.
  Threshold is a round descriptive convention, not an optimized trading rule.
- Return wealth uses first-session close/open, then CRSP CIZ total returns;
  terminal Y once then zero-interest cash. Missing observations are flagged.
- Report maximum favorable/adverse closing wealth excursions and separately
  intraday high/low price excursions on a common CRSP adjustment basis.
- Record first closing wealth >=+20%, first closing losses <=-5% and <=-10%,
  first close below the frozen breakout level, and close-below within 5 sessions.
  These are descriptive milestones, not a parameter sweep or stop simulation.
- Frozen level is prior 252-session high for `52w_only`, prior local ATH for
  either ATH group. For pooled all-52W also report the common 252-session level.
  Ordinary dividends can cause price-level breaches; levels are split-comparable,
  not total-return-adjusted. No claim of tradeability at a closing trigger price.
- For big winners, report adverse close/low excursion before first +20% close,
  and fraction returning below breakout level before that close.
- Landmark: at session-5 close, for stocks still quoted and not terminal, group
  by whether any entry-through-day-5 close was below the relevant level. Compare
  returns from day-5 close to day-126 close against same-date SPY. This avoids
  mechanically counting the loss that defined the warning as a future outcome.
- No stop orders, intraday high/low ordering assumptions, portfolio simulation,
  alpha or optimal-exit claims. An actionable close trigger would execute at a
  subsequent observed open, with gaps and costs, in a separate experiment.
- Events overlap and repeat; show equal-security sensitivity. One previously
  inspected year is exploratory, not independent validation. No significance
  claim from event counts. Check numerical consistency with source returns.
