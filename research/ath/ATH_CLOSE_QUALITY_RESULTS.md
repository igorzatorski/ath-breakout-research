# Breakout-day closing location: four exploratory thresholds

Study: `ath_21_close_quality_v001`  
Final run: `outputs/research/ath/ath_21_close_quality_v001/20261016T222520735211Z`  
Protocol: [ATH_CLOSE_QUALITY_PLAN.md](ATH_CLOSE_QUALITY_PLAN.md)

## Finding

Closing nearer the breakout session's high does not show a clear, stable improvement over the original ATH + 6-1/top20 reference. The 50% and 70% thresholds have slightly lower mean annual SPY excess, 85% is effectively unchanged, and 95% has a modest inspected gain. No primary or nonoverlap improvement has a positive pointwise or simultaneous-four lower bound at either block length. Do not add a mandatory closing-location threshold based on these results.

## Definition and support

Q = (signal close - signal low) / (signal high - signal low). Zero denotes closing at the low, 0.5 the midpoint and 1 the high. Four frozen cumulative filters: Q >=0.50, >=0.70, >=0.85, >=0.95, with inclusive numerical tolerance 1e-12. A common positive within-session price rescaling, including a split adjustment, leaves Q unchanged. This is location within that session's range, not a cross-sectional percentile, candle body, gap or breakout strength.

Prices must be finite and positive with low <= close <= high and high > low. Flat high=low sessions are not assigned score 1. In the actual source, **all 25,250 original source events have valid features**, including all **23,712 complete annual stock/SPY pairs**. There are zero flat, missing/nonpositive or inconsistent-OHLC cases; their separate audit/coverage rows are retained. Thus feature availability does not change the reference mean.

Momentum 6-1 top20, original ATH, historical universe, next-open entry, annual 252-session endpoint, distributions, terminal cash and original nonoverlap flags remain unchanged. No volume, consolidation, proximity, exit, ranking or portfolio filter is combined. Signal closing location is known before next-open entry; the breakout-day gain is not earned by the studied position. Prices end June 30, 2026, so mature annual signal cohorts end in partial 2025. Qualified-history and liquidity restrictions remain; these are gross dependent event means on inspected history, not portfolio CAGR or alpha.

## Full-period threshold results

| Minimum closing location | Events | Stock mean | SPY mean | SPY excess | Improvement |
|---|---:|---:|---:|---:|---:|
| No new filter | 23,712 | +15.47% | +9.89% | +5.58 pp | Reference |
| 50% | 21,163 | +15.27% | +9.86% | +5.41 pp | -0.17 pp |
| 70% | 16,833 | +15.19% | +9.86% | +5.33 pp | -0.25 pp |
| 85% | 10,632 | +15.53% | +9.94% | +5.60 pp | +0.02 pp |
| 95% | 4,284 | +16.04% | +9.73% | +6.30 pp | +0.73 pp |

The highest inspected threshold mean is not an independent confirmation or an optimal parameter. Threshold samples overlap. All exact adjacent changes, annual cohorts and fixed periods are saved.

## Uncertainty and repeat sensitivity

Approximate joint event-company/circular signal-date block bootstrap: 2,000 draws, seed 20261016, blocks 252/504, same weights across base and four thresholds. All four primary and nonoverlap cells have 2,000 complete-family draws at both lengths; simultaneous-four bands are available.

For the inspected 95% cell:

- Improvement +0.73 pp: 252-block pointwise 95% interval **-2.74 to +4.77 pp**; simultaneous-four **-2.97 to +4.42 pp**.
- At block 504: pointwise **-2.78 to +4.62 pp**, simultaneous-four **-2.91 to +4.36 pp**.
- Level +6.30 pp: 252-block interval **-2.88 to +20.17 pp**.

No primary or nonoverlap improvement lower bound is positive under either interval type at either block length. These approximate bands are sensitivities, not calibrated coverage guarantees; they do not correct earlier inspected trials or omitted risk exposures. Pointwise percentile and centered simultaneous bands are different constructions and need not contain one another asymmetrically.

Frozen nonoverlap reference is 1,725 events and +3.64 pp. Threshold results are +3.92 pp (50%, 1,546 events), +4.27 pp (70%, 1,273), +4.40 pp (85%, 814) and **+3.67 pp (95%, 321)**. The inspected primary maximum's improvement nearly disappears: **+0.03 pp**, pointwise interval **-9.94 to +9.85 pp** at block 252. Do not switch to the more favorable nonoverlap threshold after inspection.

## Historical stability of the inspected 95% cell

| Signal period | Events | Base excess | Filter excess | Improvement |
|---|---:|---:|---:|---:|
| 1994-2009 | 1,640 | +17.11 pp | +18.58 pp | +1.47 pp |
| 2010-2017 | 1,239 | +0.90 pp | -0.45 pp | -1.34 pp |
| 2018-partial 2025 | 1,405 | -2.23 pp | -2.07 pp | +0.16 pp |

The recent change is small and the filter still underperforms SPY. These periods are already inspected, not fresh validation; no period-specific inferential family is supplied.

## Distribution and right tail

For 95% versus the unchanged base:

| Metric | Base | 95% filter |
|---|---:|---:|
| Median stock return | +3.66% | +3.58% |
| Median SPY excess | -5.17 pp | -4.94 pp |
| Annual loss fraction | 44.60% | 44.21% |
| Final >=100% frequency | 6.74% | 6.42% |
| Final >=200% frequency | 2.21% | 2.38% |
| Final >=300% frequency | 1.13% | 1.10% |
| Sample stock-return skewness | 4.36 | 4.67 |

It retains 275/1,598 >=100% winners (17.21%), 102/523 >=200% winners (19.50%) and 47/267 >=300% winners (17.60%), while retaining 18.07% of all reference events. This is not clear general enrichment of the positive tail. Sample skewness is outlier-sensitive and not validated portfolio skewness.

Nonoverlapping descriptive bands, using the same registered tolerance as filters:

| Closing-location band | Events | Mean SPY excess |
|---|---:|---:|
| Below 50% | 2,549 | +7.02 pp |
| 50% to below 70% | 4,330 | +5.71 pp |
| 70% to below 85% | 6,201 | +4.86 pp |
| 85% to below 95% | 6,348 | +5.12 pp |
| At least 95% | 4,284 | +6.30 pp |

This is not a monotonic band pattern favoring the highest closing location. It also does not prove low-location closes are preferable: the bands are descriptive and no opposite-direction strategy was tested or selected.

## Verification and retained repair

Independent verification passed **3,240 summary/tail checks** and **50,500 raw-feature score/status checks** covering all 25,250 source events, plus outcome/flag preservation, coverage partitions and exact band-to-threshold count reconciliation. Thirteen relevant tests passed, including range/price validity, flat sessions, within-row scale invariance, inclusive boundary tolerance, generic uncertainty and original robustness tests. Ruff and whitespace checks passed; full repository tests and a raw-provider truth audit were not run.

The first completed run `20261016T222350111239Z` is retained with `superseded.json`. Its descriptive bands used exact floating-point boundaries while cumulative filters used the registered tolerance, creating a small boundary-count discrepancy. The final run applies identical tolerance to both. **`events.parquet`, `summary.csv` and `uncertainty.csv` are byte-identical between the two runs**; no features, primary outcomes, filter definitions or intervals changed. Only descriptive band allocation was corrected, with an added regression test and verifier reconciliation.

Saved: `events.parquet`, `coverage.csv`, `quality_audit.csv`, `summary.csv`, `uncertainty.csv`, `quality_bands.csv`, `adjacent_contrasts.csv`, input/code hashes and `independent_verification.json`.

## Decision and next-stage boundary

Do not promote signal-day closing location to a mandatory entry filter. Its observed changes are small, uncertain and unstable across periods/repeat treatment; it does not add convincing evidence to the entry model by itself. No higher/lower unregistered threshold or combination was searched.

The remaining proposed standalone entry-filter question is time since the previous ATH, subject to a separately fixed definition. No such experiment, filter interaction, exit, ranking, allocation or portfolio was run here; these later stages remain deferred under the user's sequence.
