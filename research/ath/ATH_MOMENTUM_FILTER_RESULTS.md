# ATH entry filter: momentum 12-1

Study: `ath_11_momentum_filter_v001`.
Run: `20261016T201856779702Z`.
Protocol: [ATH_MOMENTUM_FILTER_PLAN.md](ATH_MOMENTUM_FILTER_PLAN.md).

## Decision

Stricter momentum thresholds have higher full-history event-weighted mean
annual excess over SPY, but this experiment does NOT establish a reliable
improvement or an optimal threshold. Every primary filter-minus-baseline
interval includes zero, including the simultaneous three-contrast sensitivity.
Results are period-sensitive, weaker after repeat suppression, and unfavorable
for median excess/loss frequency. Relative performance against momentum-matched
stocks does not improve monotonically. Do not adopt top20 as a validated rule.

Retain momentum 12-1 as an exploratory feature candidate, all tested results,
and the unchanged baseline. No other momentum horizon or combined filter was run.

## Definition and population

Momentum compounds 231 scheduled total returns t-251 through t-21 inclusive.
Every return is required. Rank at the signal close within all contemporaneous
historical universe securities meeting the original liquidity and quality rules
and possessing momentum. Include ATH and non-ATH securities; no future return,
control availability, positive-size or complete-volatility restriction enters
the denominator. Tied values share mid-distribution percentiles.

Original signals remain 75,884. Momentum/rank is observed for 69,307, of which
65,650 have complete annual stock/SPY outcomes. This is the fair filter baseline,
not all 71,961 annual observations regardless of momentum availability.

| Availability group | Events | Annual stock mean | Same-window SPY | Excess |
| --- | ---: | ---: | ---: | ---: |
| All valid annual pairs | 71,961 | +12.64% | +10.09% | +2.55 pp |
| Momentum-observed annual baseline | 65,650 | +12.89% | +10.28% | +2.62 pp |
| Missing momentum, valid annual pairs | 6,311 | +10.04% | +8.17% | +1.87 pp |

No signals, returns, historical quality exclusions, old/new matched controls or
ath_10 non-overlap flags changed. No WRDS connection or new download. All means
are gross event returns, not portfolio returns, CAGR or alpha.

## Three fixed cumulative filters

"Top20" means above the 80th percentile of the contemporaneous eligible market
universe, not the strongest 20% of ATH events. Ties are not randomly broken.

| Variant | Annual events | Share of ATH baseline | Stock mean | SPY mean | Excess SPY | Improvement vs baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 65,650 | 100.00% | +12.89% | +10.28% | +2.62 pp | — |
| Top60 | 59,499 | 90.63% | +13.14% | +10.37% | +2.77 pp | +0.16 pp |
| Top40 | 46,615 | 71.01% | +13.76% | +10.51% | +3.25 pp | +0.64 pp |
| Top20 | 25,638 | 39.05% | +14.82% | +10.57% | +4.25 pp | +1.64 pp |

These nested means have an upward ordering; that alone does not demonstrate
a robust gradient across the full feature distribution.

| Disjoint market momentum group | ATH events | Excess over SPY |
| --- | ---: | ---: |
| Q1, lowest 20% | 688 | +2.86 pp |
| Q2 | 5,463 | +0.86 pp |
| Q3 | 12,884 | +1.05 pp |
| Q4 | 20,977 | +2.03 pp |
| Q5, highest 20% | 25,638 | +4.25 pp |

The five-group pattern is not strictly monotonic. Q1 has only 688 events across
286 securities and is highly influence-sensitive. ATH naturally concentrates
in high momentum, so groups are intentionally unequal in event counts.

## Joint uncertainty and multiple comparisons

All variants share each bootstrap draw: event PERMCO resampling crossed with
circular calendar blocks. 2,000 draws, seed 20261016, exactly the original
calendar length. These are approximate exploratory intervals, not proof of
calibrated inference or a correction for all previous/future research.

| Primary filter improvement | Point estimate | Pointwise 95% interval | Simultaneous three-filter interval |
| --- | ---: | --- | --- |
| Top60 minus baseline | +0.16 pp | -0.58 to +0.80 pp | -4.05 to +4.37 pp |
| Top40 minus baseline | +0.64 pp | -0.93 to +2.53 pp | -3.57 to +4.84 pp |
| Top20 minus baseline | +1.64 pp | -2.11 to +6.65 pp | -2.57 to +5.85 pp |

Above: 252-session calendar blocks. With 504-session blocks, all pointwise and
simultaneous primary improvement intervals also include zero. Q5-minus-Q1 is
+1.40 pp with interval -14.04 to +14.45 pp. Top20 standalone excess has interval
-3.52 to +14.20 pp. Neither the group spread nor the positive excess is established.

The simultaneous band uses the bootstrap 95th percentile of the maximum
absolute centered error across the three raw improvement contrasts. It has a
common, unstudentized radius and can be wider than pointwise intervals for mild
filters. It is a familywise sensitivity, not an optimal-threshold selection rule.

## Period stability

| Signal period | Baseline excess SPY | Top60 | Top40 | Top20 |
| --- | ---: | ---: | ---: | ---: |
| 1994-2009 | +9.46 pp | +10.03 pp | +11.60 pp | +14.77 pp |
| 2010-2017 | +1.37 pp | +1.50 pp | +1.18 pp | +0.31 pp |
| 2018 through complete 2025 signals | -3.05 pp | -3.22 pp | -2.98 pp | -2.42 pp |

The historical ordering is strongest in the earliest period. In 2010-2017 the
strictest filter underperforms the baseline. In the most recent complete period
top20 still loses to SPY on average. These are known-history stability checks,
not untouched out-of-sample validation.

## Repeats, weighting, risk and matched controls

Keep the EXISTING company-level annual non-overlap flags; do not restart the
selection clock inside filters. Momentum-observed annual baseline has 6,011
retained events; top60 4,812, top40 3,291 and top20 1,588.

| Fixed non-overlap variant | Annual excess SPY |
| --- | ---: |
| Baseline | +1.45 pp |
| Top60 | +1.92 pp |
| Top40 | +1.73 pp |
| Top20 | +2.10 pp |

The ordering is no longer monotonic. Top20 improvement is +0.65 pp with a
pointwise interval -3.48 to +5.57 pp. All non-overlap improvement intervals also
include zero. These are sampling sensitivities, not executable filtered portfolios.

In all-event annual pairs, baseline versus top20:

- Median paired excess over SPY: -3.00 versus -5.17 pp.
- Losing stock events: 40.22% versus 43.66%.
- Fifth percentile stock return: -55.12% versus -64.19%.
- Equal-PERMNO excess SPY: -15.41 versus -13.95 pp; both remain negative.
- Top five company contributions: +1.24 pp to baseline excess, +2.71 pp to top20
  excess. Positive tails and recurring-company weights remain important.

Higher mean excess does not mean a better typical event, less risk or a robust
risk-adjusted improvement. Quantiles above are event returns, not drawdowns.

Secondary comparison uses 44,397 complete frozen momentum-control pairs, not
the earlier 43,824 intersection requiring old controls too. Baseline excess over
these controls is +1.88 pp; top60 +1.96, top40 +1.97, top20 +1.54 pp. Top20's
change is -0.34 pp, interval -3.21 to +2.28 pp. No confirmed incremental benefit.

On those SAME matched events, excess over SPY is +1.09 pp at baseline and +1.40
pp for top20. The decline from the wider-sample +2.62/+4.25 is sample composition,
not an effect attributable solely to adding momentum adjustment. Only 11,451
of 25,638 top20 annual events have complete matched controls (44.66%). Do not
generalize their relative results to unmatched extreme-momentum events.

With frozen non-overlap in the matched population, control excess is +2.70 pp
at baseline versus +2.44 pp top20; all filter improvement intervals include zero.
No CAPM or other factor model was newly fitted for these filters.

## Verification and reproducibility

13 relevant tests passed: four new filter/ranking/bootstrap tests, three prior
momentum tests and six baseline-robustness tests. Ruff passed. Independent checks:
all 69,307 ranked event percentiles and group assignments checked against complete
saved daily cross-sections using separate search/sort arithmetic; 99 raw scalar
231-session momentum products (three per signal year), maximum discrepancy
7.1e-15; 1,296 summary/year rows and contributor sums reconciled. Original returns
and non-overlap flags are unchanged; saved artifact hashes verified.

This does not independently establish provider truth, listing inception, full
market representativeness, untouched validation or bootstrap coverage calibration.
Crossed event-company resampling still does not model the full reused-control
network. No new full repository suite was executed.

Code: `scripts/research/study_ath_momentum_filter.py`,
`scripts/research/verify_ath_momentum_filter.py`,
`src/ath_breakout/research/momentum_filter.py`.
Output: `outputs/research/ath/ath_11_momentum_filter_v001/20261016T201856779702Z/`.
Includes features, daily ranking pools, rank context, availability, summaries,
year results, contributor tables, intervals, config, manifest and subsequent
independent verification record. Changes remain local, without a new commit.
