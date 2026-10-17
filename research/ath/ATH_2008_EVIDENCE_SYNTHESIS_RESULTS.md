# ATH34:2008-onward signal and filter evidence synthesis

Completed2026-10-17. All old definitions were frozen. No new thresholds, feature computation, portfolio rules or source downloads. The principal signal sample is2008 onward with original annual outcomes observable by2026-06-30; the last mature annual signal is2025-06-27, so2025 is partial. This is known-history reassessment, not independent validation.

## Populations and metric discipline

Unfiltered annual ATH:47,379 events. Common momentum:44,084. ATH plus6-1/top20:15,853. All nine principal single-feature families and the fixed combination grid support exactly those same15,853 events; no feature-driven exclusions. Industry-supported and date-balanced ranking samples remain separate and cannot be substituted for this reference. Original nonoverlap sensitivity retains its past-only pre2008-seeded flags. Annual gross event means are not costed capital-constrained CAGR. CAPM CAR is a sum of residuals, not compounded return or portfolio alpha.

## Broad signal and control evidence

| Sample | Events | Mean metric | Equal-company metric | Metric |
| --- | ---: | ---: | ---: | --- |
| unfiltered_annual_ATH | 47379 | -1.33 pp | -18.95 pp | excess_spy |
| common_momentum_annual | 44084 | -1.10 pp | -15.92 pp | excess_spy |
| ATH6_1_top20 | 15853 | -1.42 pp | -14.63 pp | excess_spy |
| momentum12_matched_controls | 33311 | +1.10 pp | -6.62 pp | new_excess |
| incremental_ATH6_1_matched | 11023 | +1.15 pp | -7.83 pp | incremental_ath |
| CAPM_CAR_all_supported | 44948 | +0.15 pp | -13.97 pp | stock_car |
| CAPM_CAR_common | 30258 | +0.71 pp | -7.73 pp | stock_car |
| CAPM_CAR_incremental_common | 30258 | +1.87 pp | -5.11 pp | incremental_car |

Unfiltered ATH mean stock return10.23% versus same-window SPY11.56%, excess-1.33 pp. Crossed-company/date-block252 confidence interval is-5.72 to+3.07 pp;504-session sensitivity-5.29 to+2.96 pp. Nonoverlap excess-1.79 pp also has intervals including zero. No standalone ATH market edge is confirmed. Matched-control and CAR figures above are descriptive2008 re-expressions; their old full-history intervals were not reused as2008 intervals. Equal-company weighting reverses some positive matched associations, a material unresolved concentration/estimand issue.

## All seven fixed horizons on identical events

| Sessions | Events | Stock mean | SPY mean | Excess |
| --- | ---: | ---: | ---: | ---: |
| 5 | 41306 | -0.14% | 0.05% | -0.20 pp |
| 21 | 41306 | 0.41% | 0.51% | -0.09 pp |
| 63 | 41306 | 2.03% | 2.18% | -0.16 pp |
| 126 | 41306 | 4.47% | 5.06% | -0.59 pp |
| 252 | 41306 | 9.65% | 10.50% | -0.85 pp |
| 504 | 41306 | 19.37% | 22.98% | -3.60 pp |
| 756 | 41306 | 33.67% | 41.48% | -7.80 pp |

The common41,306 events require every horizon, excluding newer immature dates. These are cumulative window returns, not annualized rates. Every inspected common-horizon point mean is below SPY, but no new horizon-specific uncertainty is claimed in this descriptive table. `horizon_summary.csv` retains separate available-horizon populations and fixed subperiods.

## Fixed prior examples on the same15,853 feature reference

Examples below were specified in earlier studies; they are not newly selected period maxima. Full reference: stock10.12%, SPY11.53%, excess-1.42 pp; reference-level interval-8.42 to+6.21 pp with252 blocks.

| Original filter | Events | Excess SPY | Improvement | Approximate95% improvement interval |
| --- | ---: | ---: | ---: | --- |
| contraction: window63_threshold0.75 | 4478 | +0.45 pp | +1.87 pp | -2.75 to+6.22 pp |
| breakout_volume: window63_threshold2 | 2574 | -1.56 pp | -0.14 pp | -5.33 to+6.40 pp |
| close_quality: minimum0.95 | 2764 | -1.99 pp | -0.57 pp | -3.78 to+2.67 pp |
| record_age: minimum252 | 304 | +4.03 pp | +5.45 pp | -5.02 to+17.37 pp |
| strength: minimum1 | 1953 | -0.51 pp | +0.91 pp | -4.16 to+9.40 pp |

No principal single-filter improvement has a positive pointwise lower bound on all events; no ordinary family has a positive simultaneous lower bound under either block length or nonoverlap sensitivity. A few nonoverlap-only proximity/contraction pointwise leads fail their family bands. The>=252-session record-age lead uses only304 events and remains highly uncertain. High breakout-day volume63>=2x no longer improves even the primary point mean. Price-above-SMA entry conditions remain redundant. These observations do not prove every effect is zero.

## Coverage of the synthesis

All111 original principal single-feature variants plus four proximity accounting references are retained; nine momentum cutoffs plus fifteen disjoint quintiles; three industry cutoffs; all81 off/neighbor/main combinations; three M/MV/MVC rank families. All1,808 ordinary group/weight/subperiod summary rows are saved, including negative/empty/sparse cells. All404 original combination contrasts are retained for each of four draw settings. Sparse/empty cells can make full family bands unavailable; a missing interval is not positive evidence. Industry labels remain effective-dated current-vintage classifications, not publication-time labels.

## Ranking, separate date-balanced support

Primary ranking support is8,853 annual events on854 dates, restricted to the old common quintile-support rule. Rank scores were assigned before annual availability; the synthesis only slices dates and never reranks on outcomes.

| Group | Selected events | Equal-date excess SPY |
| --- | ---: | ---: |
| reference | 8853 | -2.02 pp |
| M_Q5 | 1734 | -3.46 pp |
| MV_Q5 | 1708 | -1.29 pp |
| MVC_Q5 | 1708 | -2.18 pp |

MV top minus M top is+2.18 pp with252-block interval-1.40 to+5.63 pp; the504 sensitivity also includes zero. No ranking superiority is established. Date-balanced reference-2.02 pp differs from full-event reference-1.42 pp because weighting and support differ. Nonoverlap-top support is separately retained.

## Uncertainty and checks

Ordinary groups:2,000 draws,252/504-session circular date blocks crossed with company multinomial resampling, fixed seed20261016. Shared draws preserve the original within-family inference while allowing consistent comparisons; per-family bands do not correct the whole historical research search. Ranking faithfully retains its distinct positive exponential-company/date-block diagnostic and20261017 seed. CAR/control means are descriptive here. All six inference jobs and draw arrays are saved.

Two focused tests verify paired differences, declared family radii and unavailable bands for empty cells. Independent checks validated34 source hashes,226 original-definition membership masks,1,808 summary rows,904 pointwise/family interval rows,20 date-balanced rank group points and identical-horizon support. The source masks and returns were not recomputed from future labels. Ruff passed.

## Practical decision

Keep the clean ATH33 portfolio benchmark and the whole evidence set. There is no confirmed2008-onward standalone ATH edge, reliable mandatory filter stack, optimum or risk-adjusted portfolio alpha. No new combination or rule was installed. Future work should address the incremental signal and exposure/concentration/factor questions under frozen definitions, not pick a larger historical maximum.
Run: `outputs/research/ath/ath_34_2008_evidence_synthesis_v001/20261017T180449698337Z`. Protocol: `research/ath/ATH_2008_EVIDENCE_SYNTHESIS_PLAN.md`. Reproduce with `harmonize_ath_2008_evidence.py`, `bootstrap_ath_2008_evidence.py RUN JOB` (main/momentum/industry/unfiltered/rank_primary/rank_nonoverlap), then `verify_ath_2008_evidence.py RUN`. All prior data and results remain unchanged.
