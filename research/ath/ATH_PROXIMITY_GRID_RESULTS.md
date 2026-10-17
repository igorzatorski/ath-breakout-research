# Fixed prior ATH proximity: sixteen exploratory variants

Study: `ath_16_proximity_grid_v001`  
Run: `outputs/research/ath/ath_16_proximity_grid_v001/20261016T214222219772Z`  
Protocol: [ATH_PROXIMITY_GRID_PLAN.md](ATH_PROXIMITY_GRID_PLAN.md)

## Finding

None of the 16 full-period event-weighted variants beats the original ATH + 6-1/top20 reference mean of **+5.58 pp annual excess over SPY**. Strict closeness for a long time is rare. Some period and nonoverlap means differ, but no full-period improvement is supported by a positive pointwise lower interval bound at either block length. There is no validated optimum, causal filter effect or portfolio alpha.

## Definition and population

For signal session t and length L, anchor A is the highest comparable historical HIGH bound known **strictly before t-L**, using the original high/close bound conventions and pre-1993 seed. During t-L through t-1, every split-adjusted close must be between A*(1-d) and A. The signal day is excluded. The anchor never moves inside the window. A prior close above the fixed anchor disqualifies the window; intraday highs above it do not by themselves fail this closing-price test. The eventual signal must still exceed the original true prior ATH, including all intraday highs through t-1.

This is explicitly the strict **below a fixed earlier ATH** interpretation announced before running. It differs from merely being within d of a moving ATH or allowing intermediate closes above the reference peak. No range-width filter was added. This definition can still admit a slow upward path below the anchor; it does not certify a complete sideways chart pattern.

Original common-momentum 6-1/top20 population: 25,250 signals; **23,712 complete annual stock/SPY pairs**. All four feature windows are observed for those annual pairs, so no availability change alters the baseline. Original stock mean **15.47%**, SPY **9.89%**, excess **+5.58 pp**. Next-open entry, 252-session holding window, distributions, terminal cash and frozen nonoverlap flags remain unchanged. Prices end June 30, 2026, so mature signal cohorts end in partial 2025. These are gross event returns, not calendar portfolio returns or CAGR.

## Annual SPY excess, percentage points

| Prior sessions | Within 5% below anchor | Within 10% | Within 15% | Within 20% |
|---|---:|---:|---:|---:|
| 10 | +0.74 | +3.39 | +4.23 | +4.51 |
| 21 | -0.13 | +3.44 | +4.41 | +4.50 |
| 42 | -7.57 | -0.03 | +3.67 | +3.80 |
| 63 | -8.20 | -8.76 | +1.01 | +3.02 |

Every cell is below the unchanged +5.58 pp reference mean. Looser depths generally increase the full-period mean; the 63/5 versus 63/10 reversal is based on tiny samples. Length gradients are not uniformly monotonic, particularly between 10 and 21 sessions. Exact adjacent contrasts for all periods and both weightings are saved. No winning cell is selected after seeing this table.

## Counts and selection

| Prior sessions | Within 5% | Within 10% | Within 15% | Within 20% |
|---|---:|---:|---:|---:|
| 10 | 1,257 | 3,663 | 4,917 | 5,451 |
| 21 | 204 | 1,104 | 1,955 | 2,502 |
| 42 | 23 | 138 | 432 | 761 |
| 63 | 5 | 27 | 120 | 265 |

Sparse cells below 100 events: 42/5, 63/5 and 63/10. Companies number 23, 5 and 25 respectively. These are descriptive estimates, not strong evidence that rare setups systematically fail.

The upper-anchor condition itself removes many repeated-breakout events. Accounting references below apply only that upper condition, without a depth floor. They are not extra optimized strategies:

| Prior sessions | Upper-only events | Upper-only excess |
|---|---:|---:|
| 10 | 5,890 | +3.74 pp |
| 21 | 3,157 | +4.76 pp |
| 42 | 1,519 | +6.09 pp |
| 63 | 1,043 | +4.76 pp |

For 21/10, the exact annual selection is **23,712 = 20,555 with a prior close above the fixed anchor + 2,053 too deep below the anchor + 1,104 passing**, with zero missing-feature exclusions. Thus one must not attribute the entire change relative to the original base solely to depth. The 21/10 excess is +3.44 pp, versus +4.76 pp for the same-length upper-only reference: a depth-specific difference of **-1.32 pp**. Its uncertainty also includes zero. A close above the fixed anchor is not necessarily a new true all-history ATH at that moment; labels in the exclusion audit mean crossing this fixed reference.

## Periods and repeated signals

Illustrative 21 sessions / 10% (for explanation, not chosen as an optimal rule):

| Signal period | Events | Filter excess | Original baseline | Improvement |
|---|---:|---:|---:|---:|
| 1994-2009 | 270 | +3.16 pp | +17.11 pp | -13.95 pp |
| 2010-2017 | 456 | +5.24 pp | +0.90 pp | +4.35 pp |
| 2018-partial 2025 | 378 | +1.46 pp | -2.23 pp | +3.70 pp |

These already inspected period means do not confirm a recent tradable edge or an out-of-sample improvement. No period-specific inferential family was tested here.

Frozen original nonoverlap reference: **1,725 events, +3.64 pp**. Nonoverlap 21/10: 257 events, **+3.19 pp**; 21/15: 538 events, **+5.96 pp**. Some sensitivity means exceed their reference, but none has a positive pointwise lower bound for improvement at either block length. Do not switch the primary weighting or pick 21/15 after inspection. All annual cohorts, medians, loss fractions and equal-company/equal-date results are retained.

## Uncertainty and full-family limitations

Approximate crossed event-company/date circular-block bootstrap: 2,000 draws, seed 20261016, blocks 252 and 504 sessions, with common weights for all cells and accounting references. For 21/10:

- Mean level +3.44 pp; 252-block 95% interval **-1.57 to +8.72 pp**.
- Improvement over original baseline -2.14 pp; interval **-13.51 to +5.81 pp**.
- Difference versus upper-only reference -1.32 pp; interval **-10.72 to +5.16 pp**.

The registered simultaneous 16-improvement band is **unavailable**: only 1,829/2,000 complete-family draws at block 252 and 1,805/2,000 at 504, below the predeclared 95% support requirement. Nonoverlap support is only 829 and 802 complete-family draws. Sparse cells sometimes vanish in resampling; no cell was dropped or threshold widened to manufacture a joint band. Missing bounds remain explicit. Consequently no multiplicity-adjusted benefit is established. Approximate bands do not correct for previous hypotheses or guarantee calibrated coverage.

## Verification and artifacts

- Independent verifier passed **4,536 summary mean checks** and **5,280 raw feature sample checks**. Samples independently reconstruct pre-window anchors from historical high/close bounds and seed, check prior closing minima/maxima, depth and upper status, including cross-year windows.
- Frozen 25,250 source event IDs, original returns, momentum and nonoverlap flags reconcile; all exclusion counts sum exactly to the annual population.
- Production generation additionally checked 660 direct window slices and reconciled signal-day prior ATH against the frozen source every year.
- Twelve relevant tests passed (proximity, prior consolidation and robustness); Ruff and whitespace checks passed. Full repository tests were not run. No raw-provider truth audit or calibrated inference claim is implied.
- Artifacts: `events.parquet`, `coverage.csv`, `summary.csv`, `uncertainty.csv`, `exclusion_audit.csv`, `adjacent_contrasts.csv`, source/code hashes and `independent_verification.json`.

## Interpretation and next-stage boundary

This experiment does not support adding strict pre-ATH proximity as a broadly beneficial annual-return filter to the frozen momentum setup. It also does not prove that every consolidation strategy fails: the definition, momentum conditioning, fixed annual exit and event weighting bound the conclusion.

The two exploratory grids have now tested width/length and fixed-anchor proximity separately. Do not continue widening the search merely to obtain a positive result. Before any combined width/proximity experiment, register a small interaction hypothesis and its reference; do not optimize all parameters simultaneously or treat known recent history as untouched validation. A complete strategy still requires frozen rules, genuinely uninspected validation and later costs/portfolio testing. No combined filter, new horizon or portfolio was run in this task.
