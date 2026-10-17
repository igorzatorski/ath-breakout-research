# ATR-normalized ATH breakout magnitude — results

Study: `ath_24_breakout_strength_v001`.
Run: `outputs/research/ath/ath_24_breakout_strength_v001/20261016T225642807548Z`.
Protocol: `research/ath/ATH_BREAKOUT_STRENGTH_PLAN.md`.

## Finding

Mean annual SPY excess increases across cumulative minimum overshoots from0.10 to1.00 prior ATR, then falls at2.00 ATR. The highest inspected cumulative mean is >=1.00 ATR: stock21.17%, same-window SPY10.89%, excess+10.28 pp versus unchanged+5.58 pp reference; improvement+4.70 pp. It remains a useful descriptive candidate under frozen nonoverlap, but recent improvements are much weaker and median/loss tradeoffs are unfavorable. No optimum, confirmed alpha or complete strategy is established.

## Feature and unchanged population

Strength(t) = (adjusted signal close - frozen prior ATH HIGH bound) / prior ATR20. ATR is the simple arithmetic mean of20 true ranges from t-20 through t-1, not Wilder smoothing. True range uses max(high-low, abs(high-previous close), abs(low-previous close)), with consistently split-adjusted prices. Require complete scheduled windows, valid positive OHLC and previous close, positive finite ATR. No signal-day range or future observation enters the denominator. Signal close is known before original next-open entry; the breakout-day rise is excluded from outcome returns.

Same25,250 source events and23,712 annual ATH + common6-1 momentum/top20 stock/SPY pairs. Every annual event has a valid feature; zero missing-feature exclusions, so common and original references are identical. Original event identity, ranks, prior ATH, next-open execution, annual252-session total return/distributions/terminal cash and original company nonoverlap remain unchanged. Prices endJune30,2026 and mature signal cohorts endpartial2025. This is gross event research, not portfolio returns, CAGR or an allocation-to-cash test.

Five frozen minimum overshoots only:0.10/0.25/0.50/1.00/2.00 ATR. Six descriptive bands partition the same support with consistent1e-12 numerical tolerance. No extra ATR length, optimized upper-bound rule, market regime, prior-filter combination, exit, ranking or portfolio was tested.

## Main annual results

Stock/SPY columns are percentages; excess/improvement are percentage points. Each SPY mean uses exactly the selected event windows. Improvement is selected excess minus common reference.

| Minimum ATR units | Events | Stock % | SPY % | Excess pp | Improvement pp |
| --- | --- | --- | --- | --- | --- |
| Reference | 23,712 | 15.47 | 9.89 | 5.58 | +0.00 |
| >=0.10 | 19,927 | 16.34 | 9.94 | 6.39 | +0.81 |
| >=0.25 | 14,776 | 16.85 | 9.95 | 6.90 | +1.32 |
| >=0.50 | 8,920 | 18.54 | 10.23 | 8.30 | +2.72 |
| >=1.00 | 3,391 | 21.17 | 10.89 | 10.28 | +4.70 |
| >=2.00 | 929 | 16.17 | 11.19 | 4.98 | -0.60 |

The inspected >=1.00 ATR improvement+4.70 pp has approximate pointwise interval-1.95 to+13.38 pp (block252), and simultaneous-five interval-4.83 to+14.23 pp. Block504 pointwise interval is-2.14 to+13.56 pp. None of the five primary or nonoverlap improvements has a positive pointwise or simultaneous lower bound at either block length. These are approximate crossed company/date-block diagnostics, not calibrated guarantees; family correction covers these five tests, not earlier research choices. The positive sample association merits review despite uncertainty, rather than binary dismissal.

## Descriptive disjoint bands

These are predefined descriptions, not extra optimized entry rules.

| ATR band | Events | Excess pp |
| --- | --- | --- |
| lt0.10 | 3785 | 1.30 |
| 0.10_to0.25 | 5151 | 4.94 |
| 0.25_to0.50 | 5856 | 4.76 |
| 0.50_to1.00 | 5529 | 7.09 |
| 1.00_to2.00 | 2462 | 12.27 |
| ge2.00 | 929 | 4.98 |

The1-2 ATR band has the highest inspected band mean+12.27 pp. This does not establish an optimal1-2 rule and was not adopted as a new filter. The relationship is not monotonically better for ever larger breakouts.

## Repeats and frozen periods

Excess/improvement are pp. Fixed original nonoverlap avoids reselection within filters; it is a sensitivity on the same inspected history, not independent validation.

| Weighting | Period | Condition | Events | Excess pp | Improvement pp |
| --- | --- | --- | --- | --- | --- |
| all | all | Reference | 23712 | 5.58 | +0.00 |
| all | all | >=1 ATR | 3391 | 10.28 | +4.70 |
| all | early | Reference | 8462 | 17.11 | +0.00 |
| all | early | >=1 ATR | 1504 | 23.22 | +6.11 |
| all | middle | Reference | 6892 | 0.90 | +0.00 |
| all | middle | >=1 ATR | 830 | 1.15 | +0.26 |
| all | recent | Reference | 8358 | -2.23 | +0.00 |
| all | recent | >=1 ATR | 1057 | -0.97 | +1.26 |
| nonoverlap | all | Reference | 1725 | 3.64 | +0.00 |
| nonoverlap | all | >=1 ATR | 347 | 9.10 | +5.46 |
| nonoverlap | early | Reference | 610 | 10.91 | +0.00 |
| nonoverlap | early | >=1 ATR | 123 | 20.86 | +9.96 |
| nonoverlap | middle | Reference | 494 | -0.39 | +0.00 |
| nonoverlap | middle | >=1 ATR | 108 | 5.45 | +5.84 |
| nonoverlap | recent | Reference | 621 | -0.29 | +0.00 |
| nonoverlap | recent | >=1 ATR | 116 | 0.03 | +0.32 |

At >=1 ATR, nonoverlap excess+9.10 pp versus+3.64 pp reference gives+5.46 pp improvement, interval-6.20 to+20.32 pp. The newer period2018-partial2025 improves from-2.23 to-0.97 pp on1,057 events but still underperforms SPY. Recent nonoverlap is+0.027 pp versus-0.291 pp reference, only+0.318 pp improvement on116 events. Much of the large full-history improvement comes from earlier cohorts. These observations do not establish causal decay or a stable current edge.

## Right tail and losses

>=1 ATR retains3,391 events (14.30% ofreference), including327 of1,598 final>=100% winners (20.46% winner retention). Their frequency rises from6.74% to9.64%; >=200% frequency2.21% to3.98%; >=300%1.13% to1.95%. However, stock median falls3.66% to2.82%, losses rise44.60% to45.80%, and sample skew falls4.36 to4.04. More large winners does not imply a better typical outcome, greater measured skew, or a successful loss-cutting policy. No exit rule is tested. All cohort, company/date-weighted, tail and complement statistics remain available in outputs.

## Verification

Independent scalar raw-window calculations passed101,000 checks of adjusted signal close, prior ATR, overshoot and normalized strength across every25,250 source event. Reconciled frozen identity/ranks/returns/nonoverlap. Repeated raw windows are verification checks, not independent observations. Independent summary/tail/complement checks:4,968; bands and nested counts also reconciled. Six focused ATR/shared-bootstrap tests passed, plus Ruff on the new feature, runner, verifier and test files. This is not a full repository suite claim.

Feature: `src/ath_breakout/research/breakout_strength.py`.
Runner: `scripts/research/study_ath_breakout_strength.py`.
Verifier: `scripts/research/verify_ath_breakout_strength.py`.
Tests: `tests/research/test_breakout_strength.py`.
Artifacts: events.parquet, coverage.csv, feature_audit.csv, summary.csv, uncertainty.csv, complement_summary.csv, strength_bands.csv, manifest.json, independent_verification.json.

## Decision

Retain moderate-to-strong normalized breakout magnitude as an exploratory candidate alongside prior candidates. Do not adopt1 ATR or a1-2 band as optimal, add an upper threshold after seeing outcomes, or combine filters without a separately registered test. Review overlap with momentum, breakout-day volume and prior-record age before attributing independent information. All inspected history remains known data. No allocation, exits or portfolio work was performed.
