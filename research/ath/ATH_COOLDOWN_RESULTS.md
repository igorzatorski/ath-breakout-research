# Repeated-event sensitivity: 21-session exclusion

Study: `ath_05_cooldown21_v001`; run `20261015T220442543623Z`.
Protocol: [ATH_COOLDOWN_PLAN.md](ATH_COOLDOWN_PLAN.md).

## Question and method

Does the positive mean depend mainly on repeatedly counting the same security's
nearby breakouts? Reuse the entire frozen 1994-2026 sample from the corrected-seed
ATH study. For each PERMNO, keep the first qualified signal, skip the next 21
exchange sessions, and allow another from session 22. Skipped events do not reset
the clock. State persists across year ends. Apply BEFORE future execution/match
validity; a missing future opening does not retroactively change the clock.
No change in ATH definition, history-quality rules, liquidity, returns, 21-session
horizon, SPY or original matched control IDs. No new WRDS connection or downloads.

## Counts

- Source qualified events: 75,884.
- Retained by past-only exclusion: 23,158; skipped: 52,726.
- Baseline complete stock/SPY/control windows: 72,023 across 2,729 securities.
- Retained complete matched windows: 21,921 across 2,698 securities.
- All valid SPY windows: baseline 75,249; retained 22,976.

## Primary 21-session comparison, common benchmarks within each event

| Measurement | All signals | 21-session exclusion |
| --- | ---: | ---: |
| Complete matched events | 72,023 | 21,921 |
| Mean stock return | +0.8423% | +0.9711% |
| Mean same-window SPY | +0.5700% | +0.6087% |
| Mean five matched controls | +0.5775% | +0.7169% |
| Mean excess SPY | +0.2723 pp | +0.3623 pp |
| Mean excess controls | +0.2649 pp | +0.2542 pp |
| Median excess controls | -0.0423 pp | -0.0851 pp |
| Loss frequency stock | 45.97% | 45.65% |

Gross arithmetic event returns, not annualized or portfolio results. Samples
are deliberately different; higher raw stock return does not by itself show a
better filter. Retained control stocks also earn higher returns in their windows.

## Uncertainty

126-session circular signal-date blocks, 2,000 replicates, seed 20261015.
Baseline and retained means are resampled jointly using the same date blocks.

- Retained excess versus controls: +0.2542 pp; 95% interval -0.0916 to +0.6031 pp.
- Change in control excess versus baseline: -0.0107 pp; interval -0.1189 to +0.1053 pp.
- Retained excess versus SPY: +0.3623 pp; interval -0.1897 to +1.0829 pp.

All include zero. 252-session blocks give the same qualitative finding. We have
not established a positive premium, nor a material change caused by suppressing
repeated events. These are dependent-sampling sensitivity intervals, not causal
effects of a trading filter. Removing same-security overlap does not make the
remaining events/controls independent.

## Stability

| Signal period | Baseline excess controls | Retained excess controls | Retained excess SPY |
| --- | ---: | ---: | ---: |
| 1994-2009 | +0.5385 pp | +0.5143 pp | +1.1821 pp |
| 2010-2017 | -0.0804 pp | -0.0076 pp | -0.0694 pp |
| 2018-2026 | +0.2930 pp | +0.2220 pp | -0.0755 pp |

Retained equal-security mean excess controls is -0.5223 pp, versus -2.4549 pp
in the baseline. Retained equal-signal-date mean excess is +0.0874 pp, versus
-0.0385 pp. Different weighting questions still yield different results.

## Decision

The small positive event-weighted mean does NOT disappear under this specific
repeated-event restriction. It cannot be attributed solely to including every
nearby breakout in the same trend. This is not proof of a repeatable ATH edge:
intervals include zero, post-2010 SPY excess remains negative, and weighting
and historical-quality selection remain important. Do not select or optimize
cooldown based on this result. Keep the signal study as the current scope.

## Verification and reproducibility

All 75,884 greedy selection decisions independently checked. Source event and
return hashes verified; retained events/returns use original IDs and controls.
Baseline mean/count reconciled with the previous study, artifact hashes checked.
Six new tests cover exact boundaries, cross-year state, non-resetting skipped
events, future-data independence, duplicate/date rejection, and identical-sample
joint-bootstrap differences. No chart review or new WRDS calls.

Run: `.venv/Scripts/python.exe scripts/research/compare_ath_cooldown.py`.
Artifacts: `outputs/research/ath/ath_05_cooldown21_v001/20261015T220442543623Z/`.
Includes selection, primary event outcomes, summary, coverage, annual results,
joint uncertainty, config and SHA256 provenance. Existing history-quality and
matching limitations are unchanged. Known history is not untouched validation.
