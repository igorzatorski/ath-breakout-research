# Why annual ATH excess differs across historical periods

Study: `ath_13_period_diagnostic_v001`. Written before this diagnostic's results.
This is a retrospective descriptive attribution, not a causal identification
design, a new entry filter, or evidence that a previously validated strategy broke.

## Population and comparison

Reuse frozen ath_12 event-level outcomes/features and original non-overlap flags.
Main focus: 6-1/top20 on the SAME common-momentum annual population used in ath_12.
This focus was chosen after its high full-history mean was observed; disclose it.
Show unfiltered common ATH plus 12-1/top20 and 3-1/top20 as contextual comparisons.
Periods remain 1994-2009, 2010-2017, 2018 through complete 2025 signal cohorts.
Main change is recent minus early. No new ATH, return, control, window or cutoff
optimization; no WRDS, download, costs, stops or portfolio.

## Frozen diagnostic questions

1. Reproduce stock mean, same-window SPY mean and paired excess by period/year.
   Reconcile change in excess exactly as change in stock minus change in SPY.
   Include medians, quantiles, loss/underperformance rates, event/company counts,
   equal-company/date/year means and the already-frozen non-overlap sensitivity.
2. Quantify signal-year and historical PERMCO contributions within each period.
   Show positive/negative leaders, event concentration and every leave-one-year-out
   mean. Show leave-top-1/5/10-company influence, not tradable deletions. Also show
   the fixed 1998-2000 exclusion as a descriptive historical-episode sensitivity,
   with remaining dates/counts, not a replacement baseline.
3. Attribute distribution/tail changes using FIXED excess buckets: <=-50 pp,
   (-50,0], (0,50], (50,100], (100,200], >200 pp. Sum shares times bucket means;
   distinguish frequency and severity. Clip positive excess at +100 pp only as
   an influence diagnostic, never as the baseline or an implementable payoff.
4. Compare observed signal-time size, vol63, ADV21, pre-signal momentum and beta.
   For composition analysis use size quartiles relative to each day's original
   6-1 eligible ranking pool: join PIT raw market cap to frozen pool identities,
   rank positive finite caps with the existing mid-distribution rule. This avoids
   treating nominal cap buckets as constant real size over three decades.
   Use fixed vol63 buckets <=20%, (20,40], (40,60], >60%, plus explicit missing.
   Use size quartile x volatility cells for exact early/recent mix-vs-within-cell
   decomposition. Apply the symmetric Kitagawa identity on shared cells;
   separately reconcile contributions of cells absent in one period, with no
   imputation. Report common-support counts and standardized means.
5. Inspect the SAME observed matched/CAPM subset across periods, retaining the
   source's frozen 12-1 momentum controls. Report matched stock, SPY, controls,
   CAR and control CAR as descriptive risk/context checks. Do not compare a
   full-sample old mean to a reduced-sample adjusted mean as a pure factor effect.
6. Coverage: yearly common-population/top20 counts, selection and matched/CAPM
   availability. All original quality exclusions remain; do not infer excluded
   ATH returns. 2025 is partial and annual 2026 cohorts are incomplete.

Sector/industry, fundamentals, institutional adoption, transaction costs and
causal market-structure changes are not observed in the saved PIT source.
Do not substitute current sector labels or invent a causal explanation. State
these gaps; existing raw schema contains no industry/SIC field.

## Uncertainty and interpretation

Joint company/date-block bootstrap, 2,000 draws, seed 20261016, calendar blocks
252 and 504 sessions, for early/intermediate/recent means and recent-minus-early
stock/SPY/excess differences on the main population. Same weights within each
draw. This tests uncertainty around historical mean differences, not the cause
of a regime shift. Known-history focus selection, few long blocks and dependence
remain; composition and influence diagnostics are not independent discoveries.

## Verification and deliverables

Verify source artifact/input hashes. Reconcile period/year means with ath_12,
all year/company/tail contributions, stock-minus-SPY identities and the complete
mix/within/nonoverlap-support identity. Unit-test decompositions including missing
cells and weighted bootstrap arithmetic. Independently aggregate saved rows and
sample raw PIT size percentiles. Preserve all code, inputs, config, diagnostics,
manifests, English report and Notion record. Clearly separate accounting
attribution, plausible mechanisms and unresolved causal questions.
