# Pre-ATH range contraction: fifteen exploratory variants

Study: `ath_18_range_contraction_v001`  
Run: `outputs/research/ath/ath_18_range_contraction_v001/20261016T220702501000Z`  
Protocol: [ATH_RANGE_CONTRACTION_PLAN.md](ATH_RANGE_CONTRACTION_PLAN.md)

## Finding

Several longer-window contraction filters have higher full-period event-weighted mean excess than the unchanged ATH + 6-1/top20 reference. The highest inspected mean is **+8.18 pp over SPY** for two 63-session halves with second/first range <=0.75, versus baseline **+5.58 pp**. Improvement **+2.61 pp** has approximate pointwise 95% interval **-2.09 to +8.25 pp**, and simultaneous fifteen-comparison interval **-6.92 to +12.13 pp** at block 252. No variant establishes a positive improvement at either block length. This is an exploratory candidate, not an optimal rule or confirmed alpha.

## Frozen definition and population

Half-window H = 5, 10, 21, 42, 63 sessions; total pre-signal windows are 10, 20, 42, 84, 126 sessions. First half is t-2H through t-H-1; second is t-H through t-1. Each range is max/min split-adjusted close - 1. Ratio = second range / first range. Exactly three cumulative cutoffs <=0.50, <=0.75 and <=1.00 per half length. The 1.00 cutoff means non-expansion, not necessarily strict contraction. The signal day is excluded.

Example: an earlier 20% closing range and recent 10% range give ratio 0.50. No absolute-width, fixed-ATH proximity or volume condition is added. Range contraction is not identical to declining daily-return volatility, a sideways consolidation or proximity to ATH.

Every half requires all scheduled positive finite prices; flat first ranges <=1e-12 would make the ratio unavailable. In the annual sample, **all five ratios are observed for all 23,712 events**: zero missing-price or zero-denominator exclusions, so original and common-feature baselines are identical. The larger pre-outcome source contains 25,250 signals and retains original outcome exclusions. Source uses a historical liquidity universe and certified history, not all US equities without qualification.

Momentum 6-1 top20, original ATH signal, next-open entry, 252-session outcome, distributions, terminal cash and original nonoverlap flags remain fixed. Baseline stock **15.47%**, SPY **9.89%**, excess **+5.58 pp**. These are gross event returns, not portfolio CAGR or costs-adjusted performance. Prices end June 30, 2026; mature signal cohorts end in partial 2025.

## Mean annual excess over SPY, percentage points

| Equal halves | Total sessions | Ratio <=50% | <=75% | <=100% |
|---|---:|---:|---:|---:|
| 5 + 5 | 10 | +5.00 | +4.96 | +5.36 |
| 10 + 10 | 20 | +5.21 | +5.90 | +5.32 |
| 21 + 21 | 42 | +3.99 | +5.04 | +5.07 |
| 42 + 42 | 84 | +5.08 | +7.58 | +6.45 |
| 63 + 63 | 126 | +8.14 | +8.18 | +7.57 |

The pattern is not universally monotonic. Short windows have little consistent gain; 42-session halves are stronger at 0.75 than 0.50; 63-session halves show a similar mean at 0.50 and 0.75, both above 1.00. This is a descriptive surface from nested selections, not a causal gradient or proof of an optimal parameter. All exact adjacent contrasts are saved.

## Event counts

| Equal halves | Ratio <=50% | <=75% | <=100% |
|---|---:|---:|---:|
| 5 + 5 | 3,653 | 6,849 | 9,915 |
| 10 + 10 | 2,833 | 6,357 | 9,909 |
| 21 + 21 | 3,422 | 7,504 | 11,463 |
| 42 + 42 | 3,006 | 7,298 | 11,509 |
| 63 + 63 | 2,458 | 6,537 | 10,699 |

All main cells contain thousands of events. Repeated events and nested membership remain dependent; event count is not a count of independent companies.

## Inspected highest-mean cell: 63 + 63 sessions, ratio <=0.75

This cell is discussed because it has the highest observed mean, not because it was independently validated. 6,537 events from 1,275 historical companies:

| Metric | Original baseline | Filter |
|---|---:|---:|
| Mean stock return | +15.47% | +18.49% |
| Mean same-window SPY | +9.89% | +10.30% |
| Mean SPY excess | +5.58 pp | +8.18 pp |
| Median stock return | +3.66% | +5.70% |
| Median SPY excess | -5.17 pp | -2.99 pp |
| Annual negative-return fraction | 44.60% | 41.15% |
| Final >=100% frequency | 6.74% | 6.41% |
| Final >=200% frequency | 2.21% | 2.00% |
| Final >=300% frequency | 1.13% | 1.30% |
| Sample stock-return skewness | 4.36 | 5.16 |

The selected group is 27.57% of all reference events. It retains 419/1,598 final >=100% winners (26.22%), 131/523 >=200% winners (25.05%) and 85/267 >=300% winners (31.84%). Thus the higher mean is not a general increase in >=100/200% winner frequency; it depends on the full distribution and weighting. Sample skewness is outlier-sensitive, not proof of desirable or stable portfolio skewness. No claim that losses can be cut while retaining these same winners follows from this entry-filter experiment.

Equal-company mean excess remains negative: -4.68 pp for the filter versus -12.35 pp baseline. Equal-date mean excess is +9.07 versus +7.58 pp. These answer different weighting questions and caution against treating the event mean as an investable portfolio result.

## Historical and repeated-event sensitivity

For the same inspected 63/0.75 cell:

| Signal period | Events | Baseline excess | Filter excess | Improvement |
|---|---:|---:|---:|---:|
| 1994-2009 | 2,168 | +17.11 pp | +23.41 pp | +6.30 pp |
| 2010-2017 | 2,060 | +0.90 pp | +2.21 pp | +1.31 pp |
| 2018-partial 2025 | 2,309 | -2.23 pp | -0.78 pp | +1.45 pp |

The event-weighted mean improvement is positive in all three descriptive periods, but largest early. The recent filter still underperforms SPY on average. These periods were already inspected and are not fresh validation; this study does not supply multiplicity-controlled period inference.

Frozen nonoverlap: reference 1,725 events, +3.64 pp excess; filtered 526 events, **+4.78 pp**, improvement **+1.14 pp**. Pointwise interval for that improvement is **-6.49 to +8.65 pp** at block 252. In the recent nonoverlap cut, filter excess is -1.62 pp versus -0.29 pp reference, a **-1.33 pp** deterioration. The favorable all-event period pattern is therefore not stable across these weighting/repeat treatments.

## Uncertainty

Joint approximate event-company/circular signal-date block bootstrap: 2,000 draws, seed 20261016, 252/504-session blocks. All fifteen cells have full 2,000 complete-family draws at both block lengths, in main and nonoverlap samples. The simultaneous bands are available, unlike the earlier sparse proximity experiment.

For the inspected 63/0.75 cell:

- Mean level +8.18 pp: 252-block 95% interval **-1.76 to +23.05 pp**.
- Improvement +2.61 pp: **-2.09 to +8.25 pp** pointwise; **-6.92 to +12.13 pp** simultaneous15.
- At 504 sessions: pointwise improvement **-1.49 to +8.41 pp**, simultaneous15 **-6.90 to +12.11 pp**.

No main or nonoverlap improvement has a positive pointwise lower bound at either block length; none has a positive simultaneous lower bound. Approximate bands do not correct for previous research choices, omitted exposures or guarantee calibrated coverage. The selected maximum is not an independent test. No stable alpha or optimal contraction strength is established.

## Verification and artifacts

Independent verifier passed **10,368 summary/tail checks** and **4,455 direct raw feature sample checks**. All 25,250 source events, frozen returns, momentum and nonoverlap flags reconcile; all fifteen main counts and the per-window availability partition reconcile. Production generation separately checked 825 direct window-ratio slices. Twelve relevant tests passed, covering equal disjoint halves, signal/future exclusion, missing prices, flat denominators, zero recent range, empty bootstrap family members and an 8,000-session calendar, plus prior consolidation/robustness tests. Ruff and whitespace checks passed; full repository tests were not run.

Saved: `events.parquet`, `coverage.csv`, `feature_audit.csv`, all-period and annual `summary.csv`, `uncertainty.csv`, `adjacent_contrasts.csv`, input/code hashes and `independent_verification.json`. No raw-provider audit, exit simulation or portfolio backtest is implied.

## Decision and next-stage boundary

Retain long-window contraction as an exploratory candidate, alongside the full negative and positive grid results. Do not promote 63/0.75 as a winner or combine it with other filters yet. The planned remaining entry-filter topic is volume, with pre-breakout and breakout-day volume tested separately under registered definitions. No volume experiment was executed here. Exit, ranking and portfolio experiments remain deferred as the user requested; only entry-filter research was performed.
