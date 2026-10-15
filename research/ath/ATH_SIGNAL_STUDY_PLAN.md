# ATH signal study: one hypothesis, no trading-rule tuning

Study: `ath_04_signal_matched_v002`. Defined 2026-10-15 before repaired-seed matched results.
This returns to Stage 01. Earlier 2024 exit/52W pilots remain exploratory records.
Version 001 used the legacy-seed exclusion after a failed connection; its output
is preserved. Version 002 changes only seed provenance/quality after the
user-authorized WRDS retry succeeded. No performance-based parameter changes.

## Question

Does a close above the maximum earlier comparable HIGH predict higher future
total returns than SPY and same-date non-ATH stocks of similar size/volatility?
No portfolio, stops, ranking, filter tuning, horizon selection or alpha claim.

## Data and population

- Local CRSP 1993 through 2026-06-30; signals 1994-01-03 through 2026-06-30.
- Historical monthly liquidity population effective at signal close; USD 10m
  mean nominal dollar volume across 21 complete NYSE sessions including signal.
- Identity PERMNO; require strictly earlier observed high, current finite price,
  valid comparable-price factor. The signal is close > prior high, excluding today.
- The authorized WRDS retry returned 4,508 isolated pre-1993 high/close bounds
  and missing-high counts. The legacy Data Layer seed was not overwritten.
  Primary population includes complete valid high seeds and excludes securities
  with any recorded pre-1993 missing/invalid nonterminal high or inconsistent
  bound. This is conservative: unpriced vendor rows may also cause exclusion;
  those rows were not silently assumed harmless. Exclude observations after
  any later missing/invalid nonterminal high. The local extraction is assumed
  complete for later listings; listing inception is not independently re-queried.
  Results are conditional on this auditable narrower population, not all ATHs.
- Track unknown-history potential breakouts separately as exclusions. This
  selection may favor younger listings. No replacement of ATH with a 252-day high.

## Return measurement

Entry: next NYSE session observed open. Measure through Hth holding-session close
for H=5,21,63,126; 21 is primary. Entry-day ex-date dividends excluded; subsequent
CIZ total returns compounded. Terminal Y return once then zero-interest cash.
Never substitute a missing open, stale price, zero missing return or later fill.
Horizons ending beyond observed coverage are censored, including late-2026 events.
SPY uses the same entry open and exit close, with subsequent adjusted-close
reinvestment proxy. This is gross event-return analysis, not a portfolio.

## Matched controls

- Same signal date, PIT membership, liquidity threshold and history-quality rules.
- No ATH signal at that close. Do not exclude controls that break out in FUTURE.
- Require positive market cap and 63 complete past daily total returns for
  volatility (sample standard deviation, annualized); all known by signal close.
- Select nearest FIVE distinct PERMNOs, excluding the event's PERMCO and duplicate
  control PERMCOs, using standardized log(size), log(volatility) distance.
- Calipers: market cap within a factor of 2; volatility within a factor of 1.5.
  Standardization uses that day's eligible control cross section. Deterministic PERMNO ties.
- Require all five matches; if unavailable retain event for SPY but mark unmatched.
  Do not relax calipers or change k after inspecting outcomes.
- Match IDs are frozen at signal date. If a selected control lacks an executable
  entry or valid forward return, flag the paired horizon incomplete; do not
  replace it based on future availability. Report this attrition.
- Controls are equal-weighted within each event; controls may be reused across
  events. Their future returns never enter matching or sample selection at t.

## Summaries and uncertainty

Report arithmetic mean/median/quantiles/loss fraction, event and security counts,
mean paired excess to SPY and controls. Show equal-security and equal-date
sensitivities, plus predefined periods 1994-2009 / 2010-2017 / 2018-2026-06-30.
Use circular moving blocks of 126 SIGNAL sessions, 2,000 draws, fixed seed
20261015, on daily sum/count pairs for event-weighted 21-session excess means.
Add 252-session block sensitivity. This handles overlap/calendar shocks better
than independent-event standard errors but not every persistent company effect.
No causal inference or multifactor alpha: controls omit sector, prior momentum
and other potential confounders. All history was available/previously inspected;
chronological subperiods are stability checks, not untouched holdouts.

Decision: describe whether positive primary excess is supported, stable and
robust to weights. If results differ by period/benchmark or data scope is narrow,
say so; do not force a yes/no general-market conclusion or start optimizing.
