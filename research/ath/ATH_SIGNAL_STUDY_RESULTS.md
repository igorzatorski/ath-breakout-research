# ATH signal versus market and matched stocks

Date: 2026-10-15. Study: `ath_04_signal_matched_v002`.
Run: `20261015T214148297829Z`.
Protocol: [ATH_SIGNAL_STUDY_PLAN.md](ATH_SIGNAL_STUDY_PLAN.md).

## One hypothesis

Does an ATH breakout predict higher future total returns than the market and
same-date non-ATH stocks with similar size and volatility? No portfolio, exits,
technical filters, parameter search or risk-adjusted alpha estimation.

## Data repair and scope

The user-authorized WRDS connection succeeded. An isolated pre-1993 high-history
export contains 4,508 PERMNOs. Its 4,472 overlapping historical maximum CLOSES
agree with the old seed within numerical tolerance; this checks the adjustment
basis, not every vendor observation. The original Data Layer seed was retained.

3,871 pre-period seeds have missing/invalid/inconsistent high history and remain
excluded from the primary sample. The missing-high count is deliberately
conservative and includes unpriced vendor rows; not all such rows imply a real
missed traded high. Later observations after any recorded nonterminal missing
high are also excluded. Listing inception after 1993 was not independently
reconciled, nor were absent vendor rows exhaustively audited.

Signals: 1994-01-03 through 2026-06-30, historical monthly liquidity population,
21-session average nominal dollar volume >= USD 10m. 75,884 qualified events;
76,943 additional potential signals with uncertain high histories are explicitly
outside the primary population. These are not all confirmed missed ATHs. This
large quality selection means the results are CONDITIONAL, not full-market proof.

## Measurement and controls

Next NYSE-session observed opening to the Hth holding-session close. H=5,21,63,126;
21 was designated primary before results. Entry ex-date dividend is excluded;
later CIZ total returns are compounded. Terminal return once then zero-interest
cash. Missing entries/paths are not filled; late horizons are censored.

SPY total-return proxy uses the same dates and entry/exit basis. Five controls
are fixed at signal close: non-ATH that day, same eligible/quality population,
distinct companies excluding the event company, nearest standardized log market
cap/63-session volatility, cap within factor 2 and vol within factor 1.5.
No future data in matching; no replacement based on later execution availability.

73,121 events have five matches at signal time. Primary 21-session comparison:
75,249 valid event/SPY windows; 72,023 complete matched windows across 2,729
securities. Selected controls are equal weighted within each event.

## Primary result: 21 sessions, identical matched sample

| Measurement | Mean |
| --- | ---: |
| Stock after ATH | +0.8423% |
| SPY over identical dates | +0.5700% |
| Five similar non-ATH stocks | +0.5775% |
| Paired excess versus SPY | +0.2723 percentage points |
| Paired excess versus controls | +0.2649 percentage points |

All are GROSS arithmetic event returns, not a portfolio or annualized rates.
The full event/SPY sample gives excess +0.2789 pp, similar to the matched sample.

## Uncertainty and stability

Circular moving blocks of signal dates preserve clusters of neighboring events:
126-session blocks, 2,000 draws, seed 20261015. Descriptive 95% bootstrap intervals:

- SPY excess: -0.2572 to +0.9378 pp.
- Control excess: -0.0784 to +0.5944 pp.

Both include zero. A 252-session block sensitivity also includes zero. This
does not prove zero effect; it does not establish a positive effect either.
The method does not fully capture persistent within-company dependence.

| Predefined signal period | Matched events | Mean excess SPY | Mean excess controls |
| --- | ---: | ---: | ---: |
| 1994-2009 | 24,492 | +1.0544 pp | +0.5385 pp |
| 2010-2017 | 21,530 | -0.1729 pp | -0.0804 pp |
| 2018-2026-06-30 | 26,001 | -0.0956 pp | +0.2930 pp |

This is stability analysis on previously available history, not untouched OOS.

Weighting matters. At 21 sessions, matched control excess is +0.2649 pp with
equal weight per EVENT, -0.0385 pp with equal weight per SIGNAL DATE, and
-2.4549 pp after first averaging events per SECURITY then equal weighting
securities. Equal-security excess to SPY is -2.9024 pp. These answer different
sampling questions; none is an executable portfolio. The differences show
concentration in recurring events rather than a broad, stable stock-level edge.
Median paired control excess is -0.0423 pp.

## Other horizons: descriptive, not winner selection

| Sessions | Complete matched windows | Mean stock | Mean SPY | Mean controls | Excess controls |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5 | 72,380 | -0.2167% | +0.0211% | +0.0457% | -0.2623 pp |
| 21 primary | 72,023 | +0.8423% | +0.5700% | +0.5775% | +0.2649 pp |
| 63 | 71,000 | +3.0201% | +2.1856% | +1.9587% | +1.0614 pp |
| 126 | 69,968 | +6.2512% | +4.9612% | +4.4332% | +1.8180 pp |

Longer-horizon positive means are leads for a separately registered hypothesis,
not a reason to replace the predesignated primary horizon after seeing results.
Horizon populations differ because of censoring and future missing observations.
No significance result was calculated for these exploratory horizons.

## Coverage and limitations

For 21 sessions: 442 event horizons censored, 177 missing entries and 16 invalid
paths; 75,249 valid event returns. Compared with these, 3,226 windows lack the
complete matched comparison. Reported controls are conditional on complete
fixed matches; attrition is not demonstrated random. 438 terminal-event windows
remain in the paired primary result.

Controls do not match sector, earlier momentum or all risk exposures. A positive
paired mean is association, not causal effect or multifactor alpha. Results are
before costs. Events and reused controls overlap and repeat. Conservative
high-history screening can favor younger or cleaner-history securities.

## Decision

There is a small positive event-weighted 21-session association in this selected
sample, but it is not statistically established by these intervals, consistent
across periods, or stable across weighting conventions. Do not claim a
repeatable general ATH premium or optimize filters from this result.

The next issue to resolve within this signal question is the large historical
quality selection and concentration, not portfolio construction or stop tuning.
Preserve this baseline for any explicitly registered follow-up.

## Verification and reproducibility

306 tests passed with actual WRDS construction blocked during the test process.
Four matching/return-engine tests include 84 synthetic scalar/vector comparisons.
649 additional production scalar/vector return checks passed. A separate
read-only verifier passed source/artifact fingerprints, event/PIT/quality
invariants, five distinct companies, fixed calipers, coverage and excess-return
arithmetic. No visual chart QA. Pandas emitted a non-fatal future dtype warning.

Reproduce using LOCAL files:
`.venv/Scripts/python.exe scripts/research/study_ath_signal.py`

Verify:
`.venv/Scripts/python.exe scripts/research/verify_ath_signal_study.py`

Outputs: `outputs/research/ath/ath_04_signal_matched_v002/20261015T214148297829Z/`.
Contains frozen config, per-year event/control/forward tables, aggregate returns,
sample audit, summary, annual/coverage tables, uncertainty and SHA256 manifest.
Live WRDS acquisition is a separate explicit action. Code remains uncommitted.
Version 001 output is retained and superseded for seed provenance; it was not
used to choose the parameters or to select this version's return result.
