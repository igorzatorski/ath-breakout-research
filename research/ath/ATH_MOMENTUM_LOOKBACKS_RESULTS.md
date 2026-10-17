# ATH momentum lookbacks: 12-1, 6-1 and 3-1

Study: `ath_12_momentum_lookbacks_v001`.
Run: `20261016T203150435062Z`.
Protocol: [ATH_MOMENTUM_LOOKBACKS_PLAN.md](ATH_MOMENTUM_LOOKBACKS_PLAN.md).

## Finding and decision

On identical annual ATH event IDs, 6-1/top20 has the largest tested mean excess
over SPY (+5.58 pp), versus +4.25 pp for 12-1/top20 and +3.88 pp for 3-1/top20.
The unfiltered common baseline is +2.62 pp. However, NONE of the nine primary
filter improvements has a 95% interval excluding zero at either block length,
even before applying the simultaneous nine-contrast sensitivity.

Do not declare 6-1 the optimal lookback or top20 a validated entry rule. Its
improvement over 12-1 at the same threshold is also uncertain; period, median,
risk and company-weighting diagnostics remain unfavorable. All tested variants
and the earlier 12-1 study are retained. No 1-month variant, additional threshold,
new matched-control model, portfolio or further search was run.

## Definitions and populations

Compound scheduled daily CRSP total returns from t-251, t-125 or t-62 through
t-21 inclusive: 231 returns for 12-1, 105 for 6-1, 42 for 3-1. All omit the latest
21 sessions. Thus 6-1 and 3-1 measure approximately five and two earlier months,
not six/three months including the latest month. Require complete valid returns.

Each ranks within its own same-date originally eligible universe with observed
momentum, including ATH and non-ATH securities. Same mid-distribution tie policy,
Q1-Q5 groups and top60/top40/top20 percentile thresholds as before. Denominators
use natural historical availability and can differ across definitions; this is
not claimed to isolate time-window length from reference-population changes.

Original 75,884 signal identities, annual next-open entries/returns, SPY, quality
rules and ath_10 company non-overlap flags remain unchanged. Source 12-1 features
and ranks reconcile. No WRDS connection, new download or return recalculation.

| Lookback | Ranked source signals | Naturally available annual pairs | Common annual pairs |
| --- | ---: | ---: | ---: |
| 12-1 | 69,307 | 65,650 | 65,650 |
| 6-1 | 73,296 | 69,474 | 65,650 |
| 3-1 | 75,354 | 71,456 | 65,650 |

The main comparison below uses the SAME 65,650 annual event IDs, with observed
momentum under every definition. The unfiltered baseline is identical across
lookbacks. These are gross event averages, not portfolio returns, CAGR or alpha.

## Main same-event comparison

Each cell is mean annual stock return minus same-window SPY, in percentage points.
Top percentages refer to the eligible market universe, not percentages of ATHs.

| Lookback | No momentum threshold | Top60 | Top40 | Top20 |
| --- | ---: | ---: | ---: | ---: |
| 12-1 | +2.62 | +2.77 | +3.25 | +4.25 |
| 6-1 | +2.62 | +2.87 | +3.69 | +5.58 |
| 3-1 | +2.62 | +2.94 | +3.26 | +3.88 |

Top20 event counts: 25,638 / 23,712 / 20,205 respectively. For 6-1/top20 the mean
stock return is +15.47% versus SPY +9.89%, giving +5.58 pp excess. The larger
excess is partly associated with different signal dates and stock selection;
SPY is aligned separately for each selected event.

| Disjoint group | 12-1 excess SPY | 6-1 excess SPY | 3-1 excess SPY |
| --- | ---: | ---: | ---: |
| Q1 | +2.86 pp | +2.65 pp | -0.20 pp |
| Q2 | +0.86 pp | +0.17 pp | +1.24 pp |
| Q3 | +1.05 pp | +0.23 pp | +2.07 pp |
| Q4 | +2.03 pp | +1.54 pp | +2.63 pp |
| Q5 | +4.25 pp | +5.58 pp | +3.88 pp |

3-1 has the cleanest descriptive ordering across the five groups, but this is
not established statistical evidence: its Q5-Q1 spread +4.08 pp has interval
-4.50 to +12.61 pp. Q1 counts differ substantially: 688 / 1,142 / 2,285. Ordered
means and the highest mean are separate observations, neither a validated rule.

## Joint uncertainty and all nine comparisons

All lookbacks, groups and filters share each company/calendar bootstrap draw.
2,000 draws, seed 20261016. Crossed event-PERMCO and circular calendar blocks
of 252 sessions; 504-session sensitivity. Approximate percentile intervals.

| Top20 improvement over common baseline | Estimate | Pointwise interval | Simultaneous nine-filter interval |
| --- | ---: | --- | --- |
| 12-1 | +1.64 pp | -2.11 to +6.65 pp | -3.40 to +6.68 pp |
| 6-1 | +2.96 pp | -1.00 to +8.56 pp | -2.08 to +8.00 pp |
| 3-1 | +1.27 pp | -1.89 to +5.39 pp | -3.78 to +6.31 pp |

All top60/top40 improvement intervals also include zero. With 504-session
blocks, all nine pointwise and simultaneous improvement intervals include zero.
The wider nine-filter band is an approximate familywise sensitivity over this
predeclared family, not a correction for all previous and future research.

At a fixed top20 threshold, 6-1 minus 12-1 excess is +1.33 pp with interval
-0.90 to +4.14 pp; 3-1 minus 12-1 is -0.37 pp with interval -3.52 to +3.00 pp.
Neither establishes superiority. Standalone 6-1/top20 excess has interval
-2.50 to +16.57 pp, also including zero.

## Fixed non-overlap and period stability

Use the unchanged ath_10 past-only company selection flags. Do not restart
the clock for each filter or lookback. The common unfiltered retained sample
is 6,011 events; its mean excess SPY is +1.45 pp.

| Retained sample | 12-1 | 6-1 | 3-1 |
| --- | ---: | ---: | ---: |
| Top60 excess SPY | +1.92 pp | +1.78 pp | +1.98 pp |
| Top40 excess SPY | +1.73 pp | +2.84 pp | +2.09 pp |
| Top20 excess SPY | +2.10 pp | +3.64 pp | +2.36 pp |
| Top20 events | 1,588 | 1,725 | 1,647 |

6-1/top20 improvement is +2.20 pp, interval -2.16 to +7.95 pp. Its difference
versus retained 12-1/top20 is +1.54 pp, interval -2.61 to +6.53 pp. Repeat
suppression does not establish the apparent ranking as a reliable advantage.

| Signal period | Common baseline | 12-1 top20 | 6-1 top20 | 3-1 top20 |
| --- | ---: | ---: | ---: | ---: |
| 1994-2009 | +9.46 pp | +14.77 pp | +17.11 pp | +13.04 pp |
| 2010-2017 | +1.37 pp | +0.31 pp | +0.90 pp | +0.06 pp |
| 2018 through complete 2025 signals | -3.05 pp | -2.42 pp | -2.23 pp | -2.47 pp |

The strongest mean improvements occur in early history. All three top20
variants lag the unfiltered mean in 2010-2017, and all have negative mean
excess over SPY in the latest complete period. Previously inspected periods
are stability diagnostics, not untouched validation.

## Risk, weights and secondary controls

| Common annual sample | Baseline | 12-1 top20 | 6-1 top20 | 3-1 top20 |
| --- | ---: | ---: | ---: | ---: |
| Median paired SPY excess | -3.00 pp | -5.17 pp | -5.17 pp | -5.65 pp |
| Losing stock events | 40.22% | 43.66% | 44.60% | 45.39% |
| Fifth percentile stock return | -55.12% | -64.19% | -63.79% | -64.22% |
| Equal-PERMNO excess SPY | -15.41 pp | -13.95 pp | -12.37 pp | -12.14 pp |

These are event-return quantiles, not drawdowns. Larger positive means do not
imply better typical outcomes or lower risk. Top five company contributions
to each top20 mean are +2.71 / +2.90 / +2.38 pp; concentration remains material.

The secondary common population has 44,397 events with five COMPLETE FROZEN
12-1-momentum-matched control outcomes. Controls were not rematched for 6-1 or
3-1, so they do not directly control either shorter measure. Baseline excess
over these controls is +1.88 pp. Top20 excess is +1.54 / +3.04 / +2.49 pp.
6-1/top20 improvement +1.16 pp has interval -1.27 to +3.82 pp; 3-1/top20
improvement +0.61 pp has interval -1.87 to +3.37 pp. No confirmed improvement.

## Natural availability is a separate comparison

| Natural annual population | Baseline excess SPY | Top20 excess SPY |
| --- | ---: | ---: |
| 12-1, 65,650 events | +2.62 pp | +4.25 pp |
| 6-1, 69,474 events | +2.82 pp | +5.84 pp |
| 3-1, 71,456 events | +2.59 pp | +3.94 pp |

These rows use different event IDs. Missing-momentum annual counts are 6,311,
2,487 and 505, with observed excess SPY +1.87, -4.98 and -2.69 pp respectively.
Do not attribute an available-sample improvement solely to lookback length.

## Verification and artifacts

12 relevant tests passed: five new lookback cases, four prior ranking/filter
tests and three prior momentum tests. Ruff passed. Independent verification
covers all saved ranks/groups, sampled raw products, summary arithmetic,
contributions and hashes; the verification JSON records final counts and scope.
The independent verifier passed 217,957 event-rank checks, 297 raw scalar
momentum products (maximum absolute discrepancy 8.9e-15), and 4,104 summary/year
rows. Common annual population reconciled to 65,650 events.
Source 12-1 ranks/returns and non-overlap flags are preserved. No new full
repository suite, provider-truth audit or bootstrap calibration was performed.

Code: `scripts/research/compare_ath_momentum_lookbacks.py`,
`scripts/research/verify_ath_momentum_lookbacks.py`,
`src/ath_breakout/research/momentum_lookbacks.py`.
Outputs: `outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z/`.
Contains common/available summaries, yearly results, all three ranking pools,
features, contributor tables, joint uncertainty, configuration and hash manifest.
The independent verification record is generated after the production manifest.
All documentation is English; changes remain local, without a new commit.

We have completed the predefined 12-1/6-1/3-1 comparison. Do not extend windows
or thresholds merely to obtain a positive lower confidence bound. Any next
research hypothesis needs its own explicit scope and justification.
