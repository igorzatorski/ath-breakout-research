# Consolidation length x width: all 25 exploratory variants

Study: `ath_15_consolidation_grid_v001`  
Run: `outputs/research/ath/ath_15_consolidation_grid_v001/20261016T213245003386Z`  
Protocol: [ATH_CONSOLIDATION_GRID_PLAN.md](ATH_CONSOLIDATION_GRID_PLAN.md)

## Finding

In the full historical event-weighted sample, longer/tighter pre-ATH closing ranges generally have lower annual SPY excess. None of the 23 populated cells exceeds the unchanged +5.58 pp baseline mean; two cells have no observations. This does not prove that all consolidation filters fail: recent-period and nonoverlap sensitivities differ, the definition measures a price range rather than a complete chart pattern, and uncertainty is substantial.

## Frozen definition and reference

Population: ATH + original common-momentum 6-1 top20, 25,250 source signals and **23,712 complete annual stock/SPY pairs**, prices through June 30, 2026. All five prior-window features are observed for every annual pair; no feature-support change alters the reference sample. Original base: stock **15.47%**, same-window SPY **9.89%**, excess **+5.58 pp**. This is the complete original population, not the smaller sample retained by the previous non-ATH matching study.

Width = highest split-adjusted closing price / lowest split-adjusted closing price - 1 over the prior L scheduled NYSE sessions, excluding the signal day. Every scheduled price is required. Thresholds are cumulative and nested, not separate independent groups. No proximity-to-ATH, volume or contraction-shape condition was added. Momentum, signal definition, next-open execution, 252-session endpoint, distributions and terminal cash treatment remain frozen. This is gross event research, not a portfolio backtest or CAGR.

## Mean annual SPY excess, percentage points

| Prior sessions | Width <=5% | <=10% | <=15% | <=20% | <=30% |
|---|---:|---:|---:|---:|---:|
| 10 | +2.36 | +3.96 | +4.43 | +5.13 | +5.45 |
| 21 | -1.55 | +3.01 | +3.06 | +3.33 | +4.48 |
| 42 | -5.80 | +0.95 | +2.53 | +3.22 | +3.76 |
| 63 | -6.05 | -3.31 | +0.74 | +2.95 | +2.91 |
| 126 | No events | No events | -6.34 | -2.45 | -0.48 |

Every populated cell is below +5.58 pp, so its full-period improvement over the original baseline is negative. For example, 21/10 gives +3.01 pp over SPY but **-2.57 pp versus the ATH/momentum baseline**. The 10/30 cell is closest at +5.45 pp; it retains most signals and should not be called an optimum.

## Event counts

| Prior sessions | Width <=5% | <=10% | <=15% | <=20% | <=30% |
|---|---:|---:|---:|---:|---:|
| 10 | 5,179 | 13,799 | 18,324 | 20,572 | 22,422 |
| 21 | 1,149 | 6,697 | 12,112 | 15,768 | 19,828 |
| 42 | 156 | 1,248 | 4,424 | 8,113 | 13,942 |
| 63 | 62 | 255 | 1,299 | 3,433 | 8,763 |
| 126 | 0 | 0 | 35 | 143 | 1,081 |

Sparse populated cells below 100 events: 63/5 and 126/15. Repeated-company counts are smaller still. No-events is not a measured zero return. A tight 126-session range overlaps the earlier period used to measure 6-1 momentum; the joint requirements can exclude essentially all strong-momentum names. The study cannot generalize to consolidation among stocks outside this momentum population.

## Gradient and historical sensitivity

At fixed width, increasing length lowers the full-sample mean in every adjacent comparison with two populated cells. At fixed length, widening the threshold raises the full-sample mean except 63 sessions / 20% to 30% (2.95 to 2.91 pp). These are nested-selection associations, not causal parameter derivatives or evidence for monotonic population effects. Exact adjacent contrasts for every period and weighting are saved.

The full-history pattern does not hold uniformly through time. Illustrative **21 sessions / 10%**, selected for explanation rather than as a winning rule:

| Signal period | Events | Filter excess | Baseline excess | Improvement |
|---|---:|---:|---:|---:|
| 1994-2009 | 1,605 | +4.33 pp | +17.11 pp | -12.78 pp |
| 2010-2017 | 2,926 | +3.10 pp | +0.90 pp | +2.20 pp |
| 2018-partial 2025 | 2,166 | +1.91 pp | -2.23 pp | +4.14 pp |

These periods were already inspected; the recent period is not an untouched validation set. Period tables are descriptive and do not establish a recent predictive improvement. Filtering may alter exposure to extreme winners and historical cohorts; this run does not identify the mechanism.

Fixed original nonoverlap reference: 1,725 events, **+3.64 pp**. The 21/10 cell has 461 events, **+5.35 pp**, improvement **+1.71 pp**. Thus the result depends on how repeated breakouts are weighted. This is a sensitivity, not permission to switch the primary weighting after seeing the result. All 25 nonoverlap outcomes, annual cohorts, company/date-weighted means, medians and loss statistics are retained.

Tighter ranges can also improve a different metric while reducing mean excess. The 10/5 cell has negative-stock-return frequency 35.74%, versus 44.60% at baseline, and median SPY excess -2.03 versus -5.17 pp. This is not a risk-adjusted strategy evaluation and does not make it an optimal filter.

## Uncertainty and multiple comparisons

Joint approximate company/date-block bootstrap: 2,000 draws, seed 20261016, 252 and 504 sessions. No main-cell pointwise interval for improvement has a positive lower bound. For 21/10, pointwise 252-block level interval is **-0.77 to +7.09 pp**; improvement interval **-13.93 to +4.69 pp**. Do not infer a reliable improvement from a positive mean or a favorable period.

**The registered full 25-comparison simultaneous band is unavailable**, because the 126/5 and 126/10 cells are empty in the source population. No cell was removed from that family to manufacture a joint result. The saved simultaneous rows explicitly have missing bounds and zero complete-family replicates. Sparse nonoverlap cells can also lack sufficient pointwise bootstrap support; unavailable bounds remain missing. No multiplicity-adjusted benefit is established. These approximate intervals do not correct for earlier research choices or guarantee calibrated coverage.

## Verification and evidence

- Independent verifier passed **5,616 summary mean checks** and **1,485 direct raw-window sample checks**; frozen returns, momentum and original nonoverlap flags reconcile.
- Production feature generation also checked 825 direct window slices against rolling results.
- Nine relevant tests passed, including exclusion of the signal day, missing/zero prices, empty cells and an 8,000-date bootstrap calendar. Ruff and whitespace checks passed. Full repository tests were not run.
- An initial unit-test assertion required exact floating-point equality and was changed to numerical tolerance; no research definition or outcome was changed.
- Saved: `events.parquet`, `coverage.csv`, all-period/all-cell `summary.csv`, `uncertainty.csv`, `adjacent_contrasts.csv`, source/code hashes and `independent_verification.json`.

## Next step

Retain this negative full-period mean result and the differing period/weighting sensitivities. Do not crown 10/30 as optimal, drop early years, or present 21/10 as validated. The current experiment completed the authorized length/width map; no additional filter was run.

The next separately registered question can be **proximity to prior ATH**, which is part of the original chart hypothesis but was intentionally absent here. Keep a reference definition fixed, compare a small predefined proximity grid and preserve the unfiltered reference. A tight range alone cannot distinguish sideways consolidation from a steady slow rise or other price patterns. Later validation must use genuinely uninspected data; costs, fuller factor exposure and portfolio construction remain separate work.
