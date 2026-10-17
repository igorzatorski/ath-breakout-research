# Does ATH add information beyond 6-1 momentum?

Study: `ath_14_incremental_6_1_v001`  
Run: `outputs/research/ath/ath_14_incremental_6_1_v001/20261016T212108778138Z`  
Protocol: [ATH_INCREMENTAL_6_1_PLAN.md](ATH_INCREMENTAL_6_1_PLAN.md)

## Finding

The matched top20 sample has a positive annual ATH-minus-non-ATH mean of **1.30 percentage points**, but approximate uncertainty includes zero. This does not establish incremental ATH alpha, and does not prove the effect is absent. In this matched population the mean gap is not weaker recently; the earlier SPY-relative deterioration is a different comparison.

These are gross event means, not portfolio returns or a causal experiment. All historical data have already been inspected. The 6-1/top20 focus was chosen after earlier results.

## Identical-sample comparison

Five same-date non-ATH controls, matched on continuous 6-1 momentum, historical size and vol63. Next-open entry; 252 holding sessions; original distributions, terminal-cash and censoring rules unchanged. No controls are selected using future returns or whether they later break ATH.

| Population | Events | ATH stock | Non-ATH controls | SPY | ATH minus controls |
|---|---:|---:|---:|---:|---:|
| Top20, main | 14,559 | 11.21% | 9.91% | 9.36% | +1.30 pp |
| Top20, frozen nonoverlap | 1,082 | 11.12% | 9.60% | 9.83% | +1.52 pp |
| All common momentum, secondary | 52,157 | 11.15% | 9.59% | 10.15% | +1.56 pp |
| All common, frozen nonoverlap | 4,863 | 11.85% | 10.50% | 10.67% | +1.35 pp |

Main top20 median paired difference is **-2.49 pp**; 47.11% of events beat their controls. Equal weight per historical company gives **-6.76 pp**, versus +2.05 pp with equal weight per signal date. The frozen nonoverlap mean remains positive; equal-company within that restricted population is -0.50 pp. These weights answer different questions; no weighting is selected to maximize the result.

## Uncertainty

Approximate crossed event-company/date-block bootstrap, 2,000 draws, seed 20261016:

| Population | 252-session block 95% interval | 504-session block 95% interval |
|---|---:|---:|
| Top20 main | -2.34 to +5.21 pp | -2.37 to +5.07 pp |
| Top20 nonoverlap | -3.05 to +6.51 pp | -3.32 to +6.51 pp |
| All common | -0.81 to +4.09 pp | -0.64 to +4.19 pp |

These intervals are approximate sensitivity diagnostics, not calibrated causal or portfolio-alpha inference. They cluster event companies, not the full network of reused control companies; annual forward windows overlap and controls can recur. Main complete top20 controls are reused at most six times on one date. Selection of this research focus and earlier trials is not corrected by these intervals.

## Periods on the rematched support

| Signal period | Events | ATH stock | Controls | SPY | ATH minus controls |
|---|---:|---:|---:|---:|---:|
| 1994-2009 | 3,879 | 8.22% | 7.70% | 1.52% | +0.52 pp |
| 2010-2017 | 5,098 | 13.49% | 12.12% | 12.12% | +1.37 pp |
| 2018-partial 2025 | 5,582 | 11.20% | 9.42% | 12.29% | +1.78 pp |

Each period's approximate interval includes zero. The recent stock mean is below SPY while above the matched controls. That is compatible: the benchmarks represent different exposures. Period composition and matching support also differ. This is not evidence of a monotonic structural ATH effect. Last complete signal is June 27, 2025 because prices end June 30, 2026 and the horizon needs 252 sessions. Signal-year cohorts are not portfolio calendar-year returns.

## Matching support and balance

Original top20 source contains 25,250 signals, including incomplete annual windows. 15,593 receive five controls at signal time. Of the **23,712 original complete annual ATH/SPY pairs**, **14,559 (61.40%)** also have all five valid control returns. The remaining 9,153 are not silently imputed or replaced with future-valid controls.

The retained sample has SPY excess **+1.84 pp**, compared with **+5.58 pp** in all 23,712 original pairs. Excluded annual events average **+11.52 pp** over SPY. Thus comparing the old +5.58 directly with the new +1.30 would conflate both benchmark and population changes. Extreme/high-momentum breakouts often lack close non-ATH analogues; this study cannot identify their incremental ATH effect.

Period retention is 3,879/8,462 early, 5,098/6,892 middle and 5,582/8,358 recent. Secondary all-common support is 52,157/65,650 annual events.

Fixed calipers: size ratio [0.5,2], volatility ratio [1/1.5,1.5], absolute momentum gap <=0.10. Five distinct control companies, excluding the event company. Distance/ties reuse the original matcher. Full certified same-date ranking pools were reused; every certified ATH that day was excluded, including signals outside the common-momentum sample.

Main matched-event momentum averages 37.78%, controls 36.08%; signed gap -1.70 pp and mean absolute gap 4.49 pp. Median control/event size ratio is 0.978, volatility ratio 1.006. Controls' mean momentum percentile is 0.859; **18.90%** fall below the top20 boundary. This is intentional continuous matching, not a separate top20-versus-top20 strategy. Residual imbalance and omitted exposures remain; no calipers were changed after results.

## Verification and saved evidence

- Frozen 69,307 common-momentum source events and original returns, ranks and nonoverlap flags reconciled.
- 278,375 saved control rows checked for eligible frozen pool membership, non-ATH status, distinct company rules, momentum and calipers.
- Independent verifier passed 1,251,584 numerical comparisons plus 396 raw size/volatility sample checks. This count reflects vectorized comparisons, not independent experiments or a full raw-provider audit.
- Main script independently checked 330 sampled control-return paths against the scalar holding-return implementation, including unavailable windows.
- Twelve relevant existing tests passed (momentum matching, annual returns, robustness); Ruff and diff whitespace checks passed. Full repository tests were not run.
- Artifacts: `events.parquet`, `controls.parquet`, year-level controls, `summary.csv`, `uncertainty.csv`, `availability.csv`, `balance.csv`, `coverage.csv`, `control_reuse.csv`, manifest and `independent_verification.json`.

## Recommended next stage

This comparison completes the immediate question. It gives a tentative positive conditional mean, not a validated edge. Further parameter searches should not be used to turn that uncertainty into a success claim.

A reasonable next exploratory step is **one consolidation-depth hypothesis**, keeping momentum definition, annual endpoint, universe, execution and benchmark fixed. Register its past-only definition and a small set of broad values before running it; compare both with the unchanged ATH baseline and with non-ATH controls. Keep all outcomes, including negative ones. Do not test duration, volume, exits and sizing at the same time.

Before calling any resulting strategy validated: freeze its rules, obtain genuinely uninspected validation data, consider fuller factor adjustment, and then evaluate costs, execution and a realistic portfolio. Known-history walk-forward diagnostics can help but cannot recreate an untouched holdout. No new consolidation filter or portfolio has been executed in this task.
