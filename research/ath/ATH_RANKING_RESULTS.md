# Three same-date event rankings and recent episodes

Study: `ath_27_event_ranking_v001`, completed2026-10-17.
Run: `outputs/research/ath/ath_27_event_ranking_v001/20261017T140021546620Z`.
Protocol: `research/ath/ATH_RANKING_PLAN.md`.

## Finding

On common supported dates, top-ranked momentum plus capped volume (MV) gives mean annual SPY excess+6.25 pp versus+3.14 pp for momentum alone (M), an incremental+3.11 pp with approximate pointwise interval-2.05 to+8.99 pp. Adding contraction (MVC) reduces top excess to+3.19 pp. The quintile curves are not smoothly increasing; top selection is not a general monotonic score-return relationship.

The newer episodes are unfavorable: top-ranked events of all three models underperform SPY in2021-2022 and2023-partial2025. Latest top excess is-9.63/-8.44/-14.26 pp forM/MV/MVC, versus same-date reference-5.00 pp. A positive full-history association therefore does not establish useful current selection or validate a20-company portfolio.

## Fixed definitions

Base candidates are the original qualified ATH + common6-1 market-momentum/top20 signals. Each date uses all pre-outcome candidates with observed original6-1 momentum, breakout-day volume relative to prior63 mean, and42+42-session range contraction. Component percentiles use (average ordinal rank minus0.5)/N on that date. M ranks original6-1 momentum; V ranks min(relative volume,2), so larger spikes above2 receive no extra component score; C ranks negative contraction ratio, favoring smaller recent/earlier closing ranges.

Three fixed scores: M; MV=(M+V)/2; MVC=(M+V+C)/3. No weight or model tuning was performed after results. Each score is ranked again within date to form tie-preserving quintiles. Equal scores stay together and may leave a quintile empty. Q5 is approximately the highest20% of same-date signal candidates, not20 stocks. Maximum source candidates on one date is36 and many dates have fewer than5. Security-level candidates remain as in prior studies, including multiple share classes when present; this does not implement company-level position selection.

All rank calculations precede filtering for complete annual outcomes:25,250 source signals retained. Existing annual next-open stock/SPY returns, distributions, terminal cash, source identities and original company nonoverlap flags are unchanged. No WRDS connection, new price download, new holding/exit rule or stocks/cash allocation was used. Signal-day volume is known before original next-open entry.

## Support and estimand: important change from prior event averages

Original annual sample is23,712 events across5,578 signal dates. The >=5-pre-outcome-candidate rule leaves16,068 annual events across1,911 dates. Requiring all five observed quintiles for each model leaves a common primary evaluation set of11,864 events across1,200 dates, or50.03% of original annual events. Dates with too few candidates, score ties leaving empty quintiles, and incomplete outcome support are excluded openly. Rank construction never uses future annual availability, but this evaluation restriction still creates a conditional population and does not represent every ATH date.

The primary means weight each evaluation date equally, then each selected event equally within that date. Same dates are used for every model and quintile. This prevents favorable calendar composition from being credited to a ranking, but it is not a capital-constrained portfolio return. Its reference stock mean12.60%, SPY9.16%, excess+3.44 pp cannot be substituted for the old full-sample event-weighted+5.58 pp reference.

For further reconciliation, raw event-weighted excess on the same primary support is+2.02 pp; the equal-date excess is+3.44 pp. The11,848 annual events excluded from primary evaluation have event-weighted excess+9.14 pp. Both support and weights matter; do not attribute those differences to score quality. All secondary event-weighted statistics remain saved separately.

## Top-quintile primary comparison

Stock/SPY columns are percentages; excess/improvement are pp. Each row uses the same1,200 evaluation dates, with original matched SPY windows.

| Group | Events | Dates | Stock equal-date % | SPY equal-date % | Excess pp | Versus same-date reference pp |
| --- | --- | --- | --- | --- | --- | --- |
| reference | 11864 | 1200 | 12.60 | 9.16 | 3.44 | +0.00 |
| M_Q5 | 2318 | 1200 | 12.30 | 9.16 | 3.14 | -0.30 |
| MV_Q5 | 2273 | 1200 | 15.41 | 9.16 | 6.25 | +2.81 |
| MVC_Q5 | 2285 | 1200 | 12.35 | 9.16 | 3.19 | -0.25 |


MV top minusM top:+3.11 pp, pointwise interval-2.05 to+8.99 pp at block252 and-1.72 to+9.10 pp at block504. Simultaneous-three incremental bounds also include zero. MVC minusMV top:-3.06 pp, pointwise interval-7.49 to+0.42 pp at block252. Thus volume gives an exploratory historical lead; adding contraction to this particular equal-weight score has no observed benefit. This does not establish the best weights, a universal negative contraction effect, or alpha beyond risk factors.

## All quintile means

Equal-date annual SPY excess in pp. Q1 is lowest score, Q5 highest. Model ordering is not uniformly monotonic.

| Model | Q1 | Q2 | Q3 | Q4 | Q5 |
| --- | --- | --- | --- | --- | --- |
| M | 1.09 | 2.46 | 4.42 | 5.01 | 3.14 |
| MV | 3.07 | 1.56 | 2.95 | 2.34 | 6.25 |
| MVC | 3.09 | 2.78 | 2.31 | 5.20 | 3.19 |


Momentum alone peaks inQ4, notQ5. MV's highest group is stronger but lower groups are irregular. MVC also hasQ4 aboveQ5. A rule that more points always imply greater expected return is not established.

## Historical periods and recent episodes

All are same-date primary comparisons, not untouched validation. Early1994-2009, middle2010-2017, recent2018-partial2025. Complete annual prices endJune30,2026, so mature2025 signals end only partway through2025. These are signal cohorts, not calendar-year portfolio returns.

| Period | Group | Events | Dates | Excess pp | Versus reference pp |
| --- | --- | --- | --- | --- | --- |
| early | reference | 3224 | 363 | 15.27 | +0.00 |
| early | M_Q5 | 626 | 363 | 17.51 | +2.24 |
| early | MV_Q5 | 608 | 363 | 22.65 | +7.39 |
| early | MVC_Q5 | 623 | 363 | 14.70 | -0.57 |
| middle | reference | 3446 | 378 | -0.38 | +0.00 |
| middle | M_Q5 | 677 | 378 | -2.97 | -2.60 |
| middle | MV_Q5 | 661 | 378 | -1.03 | -0.65 |
| middle | MVC_Q5 | 660 | 378 | -1.57 | -1.19 |
| recent | reference | 5194 | 459 | -2.78 | +0.00 |
| recent | M_Q5 | 1015 | 459 | -3.19 | -0.41 |
| recent | MV_Q5 | 1004 | 459 | -0.72 | +2.06 |
| recent | MVC_Q5 | 1002 | 459 | -1.99 | +0.79 |
| 2018_2020 | reference | 2919 | 247 | 5.01 | +0.00 |
| 2018_2020 | M_Q5 | 575 | 247 | 8.66 | +3.65 |
| 2018_2020 | MV_Q5 | 572 | 247 | 13.32 | +8.31 |
| 2018_2020 | MVC_Q5 | 568 | 247 | 13.02 | +8.02 |
| 2021_2022 | reference | 1123 | 99 | -19.65 | +0.00 |
| 2021_2022 | M_Q5 | 217 | 99 | -25.40 | -5.75 |
| 2021_2022 | MV_Q5 | 213 | 99 | -26.93 | -7.28 |
| 2021_2022 | MVC_Q5 | 218 | 99 | -25.44 | -5.79 |
| 2023_partial2025 | reference | 1152 | 113 | -5.00 | +0.00 |
| 2023_partial2025 | M_Q5 | 223 | 113 | -9.63 | -4.63 |
| 2023_partial2025 | MV_Q5 | 219 | 113 | -8.44 | -3.44 |
| 2023_partial2025 | MVC_Q5 | 216 | 113 | -14.26 | -9.25 |


For2018-2020 the MV top excess+13.32 pp exceeds reference+5.01 pp. In2021-2022 it falls to-26.93 pp versus reference-19.65 pp. In2023-partial2025 it is-8.44 pp versus reference-5.00 pp. This localizes weak recent outcomes and shows the full-history average is not a reliable description of every episode. It does not prove permanent edge decay or identify a causal market mechanism. Negative SPY excess is not necessarily a negative absolute stock return.

## Original nonoverlap sensitivity

Ranks are unchanged and company nonoverlap is never reselected inside models. Require common dates with an observedQ5 event for every model, rather than inventing a full nonoverlap quintile curve. Support falls to165 events on103 dates (original nonoverlap sample1,725 events on1,432 dates), a material selection limitation.

Equal-date reference excess-7.04 pp; M top-10.16 pp; MV top-4.33 pp; MVC top-8.86 pp. MV-minusM is+5.83 pp with positive pointwise intervals+1.36 to+11.33 pp and+1.73 to+12.53 pp at252/504 blocks. MVC-minusMV is negative pointwise at both blocks. Neither finding survives simultaneous-three/full-six bands. Top selections overlap strongly in this tiny sensitivity (Jaccard about81-83%); relatively few differing observations can move the contrast. Retain it as a qualified secondary lead, not proof of robust or positive net performance.

## Outcome distribution and overlap

On primary support, base event median1.84%, losses47.16%, final>=100% frequency5.68%. M top has median-5.03%, losses53.75%, >=100% frequency8.67%; MV top median-2.17%, losses51.61%, >=100% frequency8.71%; MVC top median-1.65%, losses51.47%, >=100% frequency6.74%. MV retains29.38% of the common reference's final doublers. These event-distribution statistics have different weights from the date-balanced mean; they show the high mean can coexist with a worse typical event. No stop-loss efficacy is tested.

Primary top-group Jaccard: M/MV39.21%, M/MVC33.85%, MV/MVC45.44%. Scores change selections materially, but selection differences alone do not demonstrate predictive value.

## Uncertainty method and limitations

Date-balanced comparisons recompute means inside every date/group. Traditional zero-count company resampling would erase many singleton quintile/date cells. Before outcomes, the protocol therefore specified strictly positive Exp(1) company weights crossed with circular252/504-session date-block resampling,2,000 draws, seed20261017. This differs from the prior event-average multinomial-company bootstrap and must not be presented as an identical estimator or calibrated95% frequentist coverage. It is an approximate company-weighted/block diagnostic preserving the common dates. Pointwise intervals and centered max-error simultaneous-three and full24 (primary)/six(nonoverlap) bands are stored.

No primary interval excludes zero for an incremental ranking effect. The secondary pointwise leads are disclosed above, with their simultaneous failure and thin support. These corrections do not undo the prior research search or current-vintage feature choices. Period rows are descriptive and do not have separately estimated intervals.

## Verification and files

Independent direct-count verification passed 303,000 component/score/rank/quintile checks across all25,250 pre-outcome signals; 11,040 summary/tail checks; 540 stored-draw contrast/family checks; and 120 directly reconstructed positive-company/date-block estimates. Original source fields/outcomes, candidate counts, common-date masks, contrast coefficients, equal-date means and support reconciliation passed. Eight focused ranking/combination/shared tests passed, plus Ruff for the new feature, runner, verifier and tests. This is not a full repository test-suite claim.

Feature: `src/ath_breakout/research/event_ranking.py`.
Runner: `scripts/research/study_ath_event_ranking.py`.
Verifier: `scripts/research/verify_ath_event_ranking.py`.
Tests: `tests/research/test_event_ranking.py`.
Artifacts: events.parquet, coverage.csv, support_by_year.csv, summary.csv, uncertainty.csv, top_overlap.csv, contrast definitions/coefficients, four draws_*.npz files, manifest.json, independent_verification.json.

## Decision

Keep MV as a simple exploratory ranking candidate and M as the necessary comparator. Do not assume adding C improves the ranking, tune weights to the now-inspected latest years, or claim a20-stock portfolio result. The tested rankings do not rescue2021-2022 or2023-partial2025 versus SPY on this conditional evaluation set. If moving toward a portfolio, first specify candidate validity, company deduplication, entry/replacement timing, weights, exits and realistic costs, then separate fixed-rule validation from development history. Those steps require their own scope and were not executed here.
