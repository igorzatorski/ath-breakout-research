# ATH record age — exploratory results

## Question and fixed comparison

Does a longer interval since creation of the previous all-time HIGH level improve annual outcomes? This is an additional standalone entry feature on the existing ATH + 6-1 momentum/top20 population, not an unfiltered ATH study or CAPM alpha estimate. The annual next-open execution, stock/SPY return pairs, terminal-cash treatment and original company nonoverlap flags are unchanged. No combinations, exits or portfolio rules were tested.

Record age is the number of NYSE sessions from the date that first established the immediately preceding all-time high level to the signal date. The signal observation is excluded when determining the previous record. Equal touches do not reset its creation date. This is not time since the last qualified close-breakout signal, nor the last touch of an old high. It uses the original adjusted high/close fallback convention and all raw history for each PERMNO.

The seed contains pre-1993 record levels but not their creation dates. Exact dates are available for 23,707 of 23,712 annual events. Five unknown earlier dates retain a conservative age lower bound measured from 1992-12-31, sufficient to classify them as at least 252 sessions. No exact date is fabricated and no event is excluded. Frozen cutoffs: 5, 21, 63, 126 and 252 sessions.

## Main annual results

Each SPY mean uses the identical dates as its selected stock events. Improvements compare mean stock-minus-SPY with the unchanged reference. Percentages are cumulative annual event returns; pp means percentage points.

| Minimum sessions | Events | Stock % | SPY % | Excess pp | Improvement pp | Improvement interval pp |
| --- | --- | --- | --- | --- | --- | --- |
| Reference | 23712 | 15.47 | 9.89 | 5.58 | +0.00 | 0.00 to 0.00 |
| 5 | 6628 | 15.25 | 10.03 | 5.22 | -0.36 | -2.83 to 2.07 |
| 21 | 2154 | 16.85 | 10.82 | 6.03 | +0.45 | -4.86 to 4.75 |
| 63 | 692 | 17.01 | 10.93 | 6.08 | +0.51 | -9.02 to 8.95 |
| 126 | 487 | 18.09 | 10.95 | 7.14 | +1.56 | -10.29 to 12.12 |
| 252 | 405 | 19.05 | 11.32 | 7.72 | +2.14 | -10.85 to 14.56 |

The inspected largest main mean is at >=252 sessions: +7.72 pp SPY excess versus +5.58 pp reference, an incremental +2.14 pp. Its pointwise approximate improvement interval is -10.85 to +14.56 pp. None of the five primary improvement intervals or simultaneous-five bands has a positive lower bound, at either 252- or 504-session time blocks. These diagnostic bootstrap bands are approximate and do not provide calibrated guarantees under all dependence structures; simultaneous-five bands address this family, not the entire prior research search.

Only 405 events (363 companies, 1.71% of the reference) satisfy >=252 sessions. The filter retains 27 of the reference's 1,598 final >=100% winners: 1.69% retention. Winner frequency is 6.67% versus 6.74%; this does not demonstrate stronger capture of the extreme right tail. Median stock return improves from 3.66% to 7.08%, and loss frequency falls from 44.60% to 41.23%. These are descriptive outcomes, not future guarantees.

## Frozen company nonoverlap sensitivity

The original rule was assigned before inspecting these filter outcomes. Do not select a fresh sequence inside each filter. Excess and improvement below are pp.

| minimum | events | excess | improvement |
| --- | --- | --- | --- |
| -1 | 1725 | 3.64 | 0.00 |
| 5 | 1088 | 2.60 | -1.04 |
| 21 | 716 | 5.86 | 2.22 |
| 63 | 503 | 7.38 | 3.74 |
| 126 | 456 | 7.43 | 3.79 |
| 252 | 404 | 7.78 | 4.14 |

Unlike the selected breakout-volume result, the longest-age mean survives the original repeat restriction: 404 events, +7.78 pp excess versus +3.64 pp nonoverlap reference. Improvement +4.14 pp has interval -6.28 to +15.35 pp at block252. This is a useful descriptive lead, not independent confirmation; the annual-age sample changes by only one event under the restriction.

## Historical periods

All-event excess below is pp. Periods are the previously frozen early/middle/recent groups; later history has already been inspected and is not a fresh holdout.

| period | minimum | events | excess |
| --- | --- | --- | --- |
| early | -1 | 8462 | 17.11 |
| early | 252 | 113 | 14.76 |
| middle | -1 | 6892 | 0.90 |
| middle | 252 | 121 | 4.09 |
| recent | -1 | 8358 | -2.23 |
| recent | 252 | 171 | 5.64 |

Long age has a higher mean than the reference in middle and recent history, but a lower mean in early history. Recent >=252 excess is +5.64 pp on 171 events, versus reference -2.23 pp. This warrants keeping the candidate for review; no causal explanation or optimal threshold is established. Exclusive bands are not smoothly monotonic: +5.72/+4.83/+6.00/+3.57/+4.27/+7.72 pp for 1-4/5-20/21-62/63-125/126-251/>=252 sessions. Nested cumulative cutoffs must not be mistaken for independent confirmations.

## Verification and reproducibility

Independent verifier passed 1,345 raw prefix/date checks using first dates of prefix maxima rather than the production recurrence, including unknown seed dates; 3,888 summary/tail checks; frozen source identity and returns; nested counts; band partition and weighted means. Five focused record-age/shared tests passed and Ruff passed on the four new code/test files. This is not a full repository test-suite claim.

Protocol: `research/ath/ATH_RECORD_AGE_PLAN.md`.
Runner: `scripts/research/study_ath_record_age.py`.
Independent verifier: `scripts/research/verify_ath_record_age.py`.
Feature: `src/ath_breakout/research/record_age.py`.
Tests: `tests/research/test_record_age.py`.
Run: `outputs/research/ath/ath_22_record_age_v001/20261016T223810045721Z`.
Artifacts: events.parquet, coverage.csv, age_audit.csv, summary.csv, uncertainty.csv, age_bands.csv, manifest.json, independent_verification.json.

## Decision

Retain long time since prior record as an exploratory candidate, without adding a mandatory cutoff or combining filters. The historical association is positive at longer cumulative cutoffs, with encouraging nonoverlap and recent descriptions, but sparse data and substantial uncertainty. Review the entry-filter evidence together before registering the next experiment. Exits, ranking and portfolio remain deferred per user sequence.

## Interpreting positive means and wide intervals

A positive historical mean is an observed fact for this sample. An interval including zero means the method does not distinguish that mean from no average effect at the chosen evidence threshold; it is not proof that the true effect is zero. Conversely, excluding zero is evidence under the method's assumptions, not proof of a durable economic mechanism, positive profit every year, or a 95% winning-trade rate. The nominal 95% repeated-sampling interpretation requires adequate assumptions; our dependent-event crossed bootstrap remains approximate.

Two questions must remain separate: excess over SPY and improvement over an existing ATH/momentum reference. A filter with +8.94 pp SPY excess on a +5.58 pp reference adds +3.36 pp historically, not +8.94 pp. Shared positive means across nested filters reuse events, companies and market episodes; they are not independent evidence and cannot be added together.

Do not demand significance in every year or reject every uncertain candidate. Judge effect size, uncertainty, robustness, concentration, practical costs and independent validation together. Equally, do not label a true future edge as established merely because many retrospectively selected means are positive. Preserve negative trials and do not change interval methods merely to obtain a positive lower bound.

Primary statistical references: [NIST confidence intervals](https://itl.nist.gov/div898/handbook/prc/section1/prc14.htm) and [ASA statement on statistical significance](https://www.amstat.org/asa/files/pdfs/P-ValueStatement.pdf). These explain statistical interpretation; they do not validate our data or trading hypothesis.
