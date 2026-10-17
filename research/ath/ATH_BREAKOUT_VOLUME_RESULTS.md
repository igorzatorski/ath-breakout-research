# Breakout-day relative volume: twenty exploratory variants

Study: `ath_20_breakout_volume_v001`  
Run: `outputs/research/ath/ath_20_breakout_volume_v001/20261016T221719577843Z`  
Protocol: [ATH_BREAKOUT_VOLUME_PLAN.md](ATH_BREAKOUT_VOLUME_PLAN.md)

## Finding

All twenty full-period event-weighted relative-volume filters have higher inspected mean annual SPY excess than the unchanged **+5.58 pp** ATH + 6-1/top20 reference. The surface generally favors 1.5-2 times prior average volume; raising the threshold to 3 times reduces the mean for every reference length relative to 2 times. This is more consistent mean-selection evidence than pre-breakout dry-up, but **no primary or nonoverlap improvement has a positive pointwise or simultaneous lower bound** at either block length.

The highest inspected cell, volume >=2 times the prior 63-session mean, has +8.94 pp excess, improvement +3.36 pp with approximate pointwise 95% interval **-3.58 to +12.92 pp**. It selects more large winners but also more annual losers and has a lower median. Its frozen nonoverlap mean does not improve the reference. Retain breakout-day relative volume as an exploratory candidate, not a validated optimum or alpha.

## Frozen definition and support

Relative volume at t = comparable share-volume[t] / mean(comparable volume over t-L through t-1). References L = 5, 10, 21, 42, 63 scheduled NYSE sessions. Minimum ratios = 1.0, 1.5, 2.0, 3.0, inclusive with 1e-12 tolerance. The denominator excludes t. Numerator is the full signal day, known after close before next-open entry. Comparable volume is raw CRSP volume times share_adjustment_factor, consistent with the existing layer and split tests. This is share-volume, not dollar-volume or turnover.

Require all reference observations and current volume finite and nonnegative, adjustment factors positive and finite and prior mean positive. All **23,712 annual stock/SPY pairs** have complete observed ratios across all five references, with no missing-volume/zero-denominator exclusions. There are zero valid zero-volume signal days in that annual sample (recorded in independent verification). Original pre-outcome source contains 25,250 events; original outcome exclusions remain.

ATH definition, original momentum ranks/top20, historical universe, next-open entry, 252-session endpoint, distributions, terminal cash and frozen nonoverlap flags are unchanged. **The breakout-day price gain is not included in the post-entry return**. No dry-up, price-range contraction, proximity, additional entry, exit, ranking or portfolio condition is added. Prices end June 30, 2026; mature annual signal cohorts end in partial 2025. Certified-history restrictions, dependence, gross returns and inspected-history limitations remain; event means are not portfolio returns.

## Mean annual excess over SPY, percentage points

| Prior volume reference | >=1.0x | >=1.5x | >=2.0x | >=3.0x |
|---|---:|---:|---:|---:|
| 5 sessions | +6.68 | +6.89 | +7.34 | +6.03 |
| 10 sessions | +6.70 | +8.06 | +7.12 | +6.48 |
| 21 sessions | +7.00 | +8.28 | +8.65 | +7.35 |
| 42 sessions | +7.22 | +8.56 | +8.88 | +6.42 |
| 63 sessions | +7.11 | +8.43 | +8.94 | +6.34 |

Reference without the new volume filter: **+5.58 pp**. These are cumulative nested selections, not independent groups. The pattern is not "the larger the spike, the better"; the most extreme threshold does not maximize any row. Similar inspected means across adjacent references are worth retaining, but not evidence of independent replication or a confirmed rule.

## Counts

| Prior reference | >=1.0x | >=1.5x | >=2.0x | >=3.0x |
|---|---:|---:|---:|---:|
| 5 sessions | 15,510 | 7,408 | 4,009 | 1,669 |
| 10 sessions | 15,535 | 7,584 | 4,122 | 1,788 |
| 21 sessions | 15,188 | 7,491 | 4,135 | 1,822 |
| 42 sessions | 14,791 | 7,505 | 4,214 | 1,815 |
| 63 sessions | 14,802 | 7,669 | 4,309 | 1,886 |

All primary cells contain at least 1,669 events. Repeated companies and overlapping return windows mean these are not independent sample sizes.

## Inspected highest-mean cell: prior 63 sessions, >=2x

This cell is selected for discussion after seeing the grid; it is not an independent confirmation. It retains **4,309 events from 1,371 historical companies** (18.17% of reference events).

| Metric | Unchanged base | Filter |
|---|---:|---:|
| Mean stock return | +15.47% | +18.62% |
| Mean same-window SPY | +9.89% | +9.69% |
| Mean SPY excess | +5.58 pp | +8.94 pp |
| Median stock return | +3.66% | +1.06% |
| Median SPY excess | -5.17 pp | -6.72 pp |
| Annual loss frequency | 44.60% | 48.09% |
| Final >=100% frequency | 6.74% | 9.21% |
| Final >=200% frequency | 2.21% | 3.71% |
| Final >=300% frequency | 1.13% | 2.04% |
| Sample stock-return skewness | 4.36 | 4.11 |

The filter retains 397/1,598 >=100% winners (24.84%), 160/523 >=200% winners (30.59%) and 88/267 >=300% winners (32.96%). This is enrichment of the large-return tail relative to event count, not retention of every original winner. A higher large-gain frequency coexists with more losses and a lower median. Standardized sample skewness is not higher; do not substitute "more very large winners" for a proven increase in portfolio skewness or expected utility.

Equal-company mean excess is -6.21 pp versus -12.35 pp reference; equal-date excess +8.70 versus +7.58 pp. These weighting sensitivities do not make the event mean an investable portfolio result.

## Non-overlapping relative-volume bands

For the 63-session reference, the descriptive bands partition all annual events:

| Relative volume | Events | Mean SPY excess |
|---|---:|---:|
| Below 1x | 8,910 | +3.03 pp |
| 1x to below 1.5x | 7,133 | +5.70 pp |
| 1.5x to below 2x | 3,360 | +7.78 pp |
| 2x to below 3x | 2,423 | +10.96 pp |
| At least 3x | 1,886 | +6.34 pp |

This illustrates the observed rise and subsequent drop without confusing overlapping threshold samples. Bands were registered as descriptive accounting and are not an additional multiplicity-controlled set of strategies. No extra threshold is selected from these means.

## Historical and repeat sensitivity

For the inspected 63-session / >=2x cell:

| Signal period | Events | Base excess | Filter excess | Improvement |
|---|---:|---:|---:|---:|
| 1994-2009 | 1,864 | +17.11 pp | +21.43 pp | +4.32 pp |
| 2010-2017 | 1,148 | +0.90 pp | -0.15 pp | -1.04 pp |
| 2018-partial 2025 | 1,297 | -2.23 pp | -0.97 pp | +1.26 pp |

The recent filter mean is still below SPY. Already inspected subperiods are not new validation, and no period-specific family inference is provided.

Frozen nonoverlap reference: 1,725 events, +3.64 pp. The same cell has 635 events, **+3.21 pp**, improvement **-0.43 pp**. Its recent nonoverlap excess is -6.71 pp versus -0.29 pp reference. Nineteen other nonoverlap cells have positive mean improvements, but none has a positive pointwise or simultaneous lower bound. The identity of the highest mean changes under repeat treatment, so the primary maximum is not robust as an optimum.

## Uncertainty

Joint approximate event-company/circular signal-date block bootstrap: 2,000 draws, seed 20261016, blocks 252 and 504. All twenty main and nonoverlap cells have 2,000 complete-family draws at both block lengths; simultaneous bands are available.

For the inspected 63 / >=2x cell:

- Level +8.94 pp: 252-block pointwise interval **-4.26 to +28.23 pp**.
- Improvement +3.36 pp: **-3.58 to +12.92 pp** pointwise, **-7.06 to +13.78 pp** simultaneous20.
- At block 504: improvement **-3.86 to +12.76 pp** pointwise, **-7.00 to +13.71 pp** simultaneous20.
- Nonoverlap improvement -0.43 pp: pointwise **-7.79 to +7.81 pp** at block 252.

No primary or nonoverlap improvement has a positive lower bound under either interval type at either block length. These approximate bands do not guarantee calibrated coverage or correct for earlier research hypotheses, omitted factors or selecting the maximum after inspection. Positive means across the grid are not a confirmation of stable alpha.

## Verification and artifacts

Independent verifier passed **13,658 summary/tail/band checks** and **4,455 direct raw feature sample checks**. It reconstructs signal-day volume separately from strictly prior means, preserves original event IDs/returns/ranks/nonoverlap flags, reconciles bands to the common baseline and checks decreasing counts as minimum thresholds rise. Production generation checked 825 direct raw ratios. Fourteen relevant tests passed, including current numerator/prior-only denominator, future exclusion, zero/invalid/missing data, split correction and scale invariance, prior volume/generic grid and CRSP adjustment checks. Ruff and whitespace checks passed. Full repository tests and a provider truth audit were not run.

Artifacts: `events.parquet`, `coverage.csv`, `feature_audit.csv`, `summary.csv` for every cell/period/year, `relative_volume_bands.csv`, `uncertainty.csv`, `adjacent_contrasts.csv`, hashes and `independent_verification.json`. Zero signal-volume count is recorded in independent verification.

## Decision and next-stage boundary

Retain moderate breakout-day relative volume as an exploratory entry-filter candidate alongside long-window price-range contraction. Do not adopt a particular reference/threshold, combine filters or change weighting to favor the result yet. More large winners are accompanied by more losing events; this filter does not itself truncate the left tail.

High volume is not proof of buying pressure, institutional confirmation or causality; news/earnings, risk exposure and other omitted conditions can differ. Within-ATH selection does not establish incremental ATH information versus non-ATH peers. Real-time volume finalization, costs and actual execution are not modeled by the historical next-open convention.

The planned remaining entry-filter questions are breakout-day price quality and time since the prior ATH, if separately authorized. No additional filter, interaction, exit, ranking, allocation or portfolio experiment was executed here. Exits and portfolio remain deferred per the user's sequence.
