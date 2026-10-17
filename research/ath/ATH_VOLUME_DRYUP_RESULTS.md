# Pre-breakout volume contraction: fifteen exploratory variants

Study: `ath_19_volume_dryup_v001`  
Run: `outputs/research/ath/ath_19_volume_dryup_v001/20261016T221234158189Z`  
Protocol: [ATH_VOLUME_DRYUP_PLAN.md](ATH_VOLUME_DRYUP_PLAN.md)

## Finding

Declining pre-breakout volume does not show a reliable general improvement in the primary ATH + 6-1/top20 event sample: **13 of 15 full-period means are below the unchanged +5.58 pp annual SPY-excess reference**. The two higher means are small improvements with uncertainty including zero. Stronger volume contraction is not a consistently favorable gradient.

One nonoverlap sensitivity, 21+21 sessions with recent mean <=100% of the earlier mean, has a borderline positive pointwise improvement interval. It does not survive the simultaneous fifteen-variant sensitivity, and the primary version barely improves its reference. Preserve it as a weak secondary lead, not a confirmed filter. No primary or nonoverlap cell has a positive simultaneous lower bound at either block length.

## Frozen definition

Compare two consecutive equal H-session periods strictly before the signal: first t-2H through t-H-1, recent t-H through t-1. H = 5, 10, 21, 42, 63; total windows 10, 20, 42, 84, 126 sessions. Ratio = mean recent volume / mean earlier volume. Cutoffs <=0.50, <=0.75, <=1.00. The 1.00 cutoff is non-increase, not necessarily a decline.

Comparable volume is raw CRSP volume times share_adjustment_factor, matching the existing project adjustment direction and its split test. Require finite nonnegative volumes, positive finite factors and all scheduled observations. Keep valid daily zero volumes; reject zero earlier means rather than inventing ratios. A constant positive rescaling of the full window leaves the ratio unchanged. This is share-volume, not dollar-volume or turnover. No signal-day volume is used.

No price-range contraction, absolute width, proximity, breakout-day volume, exit or portfolio rule is added. Primary universe remains original ATH + common 6-1/top20. All **23,712 annual stock/SPY pairs** have all five observed ratios, with zero missing-volume or zero-denominator exclusions. Original and common-feature baselines coincide. The larger source contains 25,250 signals before annual exclusions; original returns and nonoverlap flags remain frozen.

Next-open entry, 252-session return, distributions and terminal cash follow existing rules. Prices end June 30, 2026; annual mature signal cohorts end in partial 2025. Event means are gross, dependent across repeated companies/dates and not portfolio CAGR, alpha or costs-adjusted performance. Historical quality and liquidity restrictions remain.

## Mean annual excess over SPY, percentage points

| Equal volume periods | Total sessions | Recent mean <=50% | <=75% | <=100% |
|---|---:|---:|---:|---:|
| 5 + 5 | 10 | +1.73 | +3.81 | +4.76 |
| 10 + 10 | 20 | +6.15 | +1.65 | +4.23 |
| 21 + 21 | 42 | -3.28 | +4.31 | +5.75 |
| 42 + 42 | 84 | +0.22 | +2.78 | +4.88 |
| 63 + 63 | 126 | -5.55 | +4.88 | +3.72 |

Reference without the new volume filter: **+5.58 pp**. Only 10+10 / 50% (+0.57 pp improvement) and 21+21 / 100% (+0.17 pp) exceed it. The surface is irregular; an isolated higher cell is not an optimal parameter. Strong <=50% contraction is usually worse here, but this is not proof that every volume-based strategy fails.

## Counts

| Equal periods | Recent mean <=50% | <=75% | <=100% |
|---|---:|---:|---:|
| 5 + 5 | 814 | 4,398 | 10,863 |
| 10 + 10 | 677 | 4,607 | 11,785 |
| 21 + 21 | 524 | 4,578 | 12,146 |
| 42 + 42 | 272 | 3,100 | 10,835 |
| 63 + 63 | 153 | 2,278 | 9,656 |

Strong long-period contraction is selective. Fixed nonoverlap samples are much smaller: for the <=50% cutoffs they contain 79, 63, 30, 22 and 15 events respectively. No cells are removed or retuned because of their result.

## Inspected primary maximum and uncertainty

The highest primary mean, 10+10 / 50%, was selected for explanation after viewing the grid. It has 677 events from 429 historical companies:

- Stock mean **+16.31%**, same-window SPY **+10.16%**, excess **+6.15 pp**.
- Improvement **+0.57 pp**, pointwise 252-block interval **-12.06 to +20.38 pp**; simultaneous15 **-26.09 to +27.24 pp**.
- At 504 sessions, pointwise interval **-12.65 to +18.53 pp**.
- Median stock +0.92%, median SPY excess -6.72 pp, annual loss frequency 44.31%. Baseline median stock is +3.66% and loss frequency 44.60%.
- Early/middle/recent excess: **+19.63 / +1.49 / -7.57 pp**, versus reference **+17.11 / +0.90 / -2.23 pp**. Recent performance is materially less favorable in this inspected cell.
- Nonoverlap: 63 events, excess **-5.48 pp**, compared with +3.64 pp reference; improvement -9.12 pp with very wide uncertainty.

There is no convincing primary evidence for adopting this maximum. Existing period data were already inspected, so they are not fresh validation.

## Secondary nonoverlap lead, fully disclosed

For 21+21 / 100%, the primary mean is **+5.75 pp** (12,146 events), just **+0.17 pp** above reference. Nonoverlap gives **+9.40 pp** (782 events) versus +3.64 pp reference, improvement **+5.76 pp**.

Approximate pointwise improvement intervals are **+0.06 to +12.17 pp** at block 252 and **+0.11 to +12.35 pp** at 504. These narrowly positive lower bounds are a secondary, selected sensitivity. The simultaneous fifteen-cell intervals are **-63.32 to +74.84 pp** and **-57.34 to +68.86 pp**: they do not confirm a family-adjusted improvement. Very broad simultaneous bands reflect uncertainty in the full family, including sparse strict filters; no favorable subfamily is substituted after seeing results.

Nonoverlap descriptive early/middle/recent improvements are +9.87/+5.15/+4.38 pp. This merits retaining the observation, not changing the primary weighting or calling it validated. The <=100% condition measures no increase in volume, not strong dry-up.

## Right-tail effect

The inspected primary maximum retains 48 of the original 1,598 >=100% winners, 22 of 523 >=200% winners and 16 of 267 >=300% winners. Its corresponding within-cell frequencies are 7.09%, 3.25%, 2.36%, versus 6.74%, 2.21%, 1.13% baseline, but it retains only 677/23,712 events and has wide mean uncertainty. Do not confuse a higher frequency in a selected subgroup with retaining all original winners or improving an investable portfolio.

At the strongest long-period cutoff (63+63 / 50%), only 153 events remain: four finish >=100%, none >=200%. Its sample loss frequency is lower (32.03%) but mean SPY excess is -5.55 pp and sample skewness only 0.28, versus 4.36 baseline. A reduction in loss frequency alone is not the desired combination of preserved right tail and limited losses. No actual loss-cutting exit was applied.

All cells' >=100/200/300% frequencies/retention, skewness, company/date weighting, medians, loss fractions, annual and historical cuts are retained. Volume does not identify buying/selling pressure or a causal mechanism; changes in share supply and reporting conventions are not separately controlled here.

## Verification and inference scope

Independent verification passed **10,368 summary/tail checks** and **4,455 raw-volume feature sample checks**. All frozen source IDs/outcomes/flags and common support reconcile. Production generation checked 825 direct two-half volume ratios. Eleven relevant tests passed, including signal/future exclusion, mean windows, zero/missing values, split adjustment, scale invariance, generic joint uncertainty and existing CRSP adjustment tests. Ruff and whitespace checks passed; full repository tests were not run.

Joint approximate event-company/circular date-block bootstrap: 2,000 draws, seed 20261016, blocks 252/504. Main complete-family support is 2,000 at both lengths; nonoverlap 1,995/1,994, above the registered 95% requirement, so all simultaneous15 bands are available. Approximate bands do not guarantee calibrated coverage or correct for the earlier research program and omitted factors. No primary pointwise improvement lower bound is positive; one secondary nonoverlap cell has positive pointwise bounds, but no simultaneous benefit is established.

Artifacts: `events.parquet`, `coverage.csv`, `feature_audit.csv`, all-cell/period/year `summary.csv`, `uncertainty.csv`, `adjacent_contrasts.csv`, code/input hashes and `independent_verification.json`.

## Decision and next-stage boundary

Do not add strict pre-breakout volume dry-up as a confirmed general entry condition. Preserve the weak 21+21 / non-increase nonoverlap lead with its multiplicity and weighting qualifications. No threshold, period or denominator was changed to improve the result.

The next separately proposed volume question is relative volume **on the breakout day**; it is a different hypothesis and was not tested here. No combination with range contraction, exit, ranking, allocation or portfolio construction was run. These later stages remain deferred under the user's requested entry-filter sequence.
