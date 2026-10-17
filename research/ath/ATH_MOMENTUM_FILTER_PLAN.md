# ATH entry selection by momentum 12-1

Study: `ath_11_momentum_filter_v001`. Protocol recorded before filter outcomes.
One feature, one annual horizon, five ordered groups and three fixed thresholds.
This is retrospective exploratory research, not untouched validation.

## Hypothesis and frozen baseline

Does stronger pre-signal momentum distinguish subsequent annual excess returns
among qualified ATH signals? Do not assume monotonic improvement or select a
winning lookback from the results. Reuse ath_04 v002 signal/quality/PIT/ADV21 rules,
ath_06 252-session next-open returns, ath_08 frozen momentum-control returns,
and ath_10 past-only company non-overlap flags. No returns or controls are rebuilt
or rematched. No stops, portfolio, costs, downloads or WRDS access.

Momentum 12-1 compounds all 231 scheduled daily CRSP total returns t-251 through
t-21 inclusive. Require every return observed and >= -1. Reuse the tested lagged
momentum function and reconcile event values against ath_08. Do not change to
3-1/6-1, include the latest month, bridge missing sessions or fit the lookback.

## Signal-date cross-sectional ranking

Rank within the full contemporaneous historical universe meeting the ORIGINAL
membership, liquidity and history-quality/current-price rules, with observed
momentum. Include ATH and non-ATH stocks. Do not restrict the rank denominator
to ATH events, future annual completeness, five-control availability, positive
market cap or complete volatility (the latter are matching requirements only).
Rank securities (PERMNO), as in the original universe; flag company share classes.

Use the tied mid-distribution percentile (count strictly below + half count
equal) / number of observed eligible securities. Ties share ranks; thresholds
need not retain exactly the nominal percentage. Save denominator counts and
ranking pools on signal dates. All information is available at signal close.

Five disjoint groups: Q1 <=20th percentile, Q2 (20,40], Q3 (40,60], Q4 (60,80],
Q5 >80th. Fixed cumulative filters: top60 >40th, top40 >60th, top20 >80th.
Baseline = ATH with observed momentum/rank, not all ATH regardless of availability.
Record excluded events and compare their observable annual results separately.

## Evaluation

Primary display: annual stock/SPY valid pairs within the momentum-observed
baseline. For each group/filter show event/security/company counts, retained
fraction, stock/SPY/excess means, medians, quantiles, loss rates, terminal events,
equal-security/equal-company/equal-date excess, and 1994-2009 / 2010-2017 /
2018 through complete 2025 signals. Same-window SPY must be recomputed for every
subset. Show signal-year results and top-company contribution concentration.

Repeat with the EXISTING ath_10 annual PERMCO non-overlap flags. Do not restart
the selection clock separately inside each momentum filter: that would create
a different entry policy and a second experimental change.

Secondary: only events with five frozen valid momentum controls, and a rank.
Compare baseline and filters within this explicit common eligibility; do not
compare a filtered matched mean to an unmatched full baseline. This conditional
matching analysis does not replace risk-factor regression or establish causality.

## Uncertainty and multiplicity

2,000 draws, seed 20261016; circular calendar blocks 252 sessions and 504 sensitivity,
crossed independently with event-PERMCO resampling. Resample all groups jointly,
using identical company/date weights. Estimate each selected mean and its
difference from the corresponding momentum-observed unfiltered baseline;
also Q5 minus Q1. Report pointwise percentile intervals as EXPLORATORY: five
groups, three thresholds, periods, weighting and overlap diagnostics are related
multiple comparisons, not independently confirmed discoveries. Retain all tests.

The primary contrast family is top60/top40/top20 minus baseline (all events,
annual SPY excess). Add a bootstrap max-absolute-centered-error simultaneous
interval across these three contrasts at each block length; label it an
approximate familywise sensitivity, not a guarantee of calibrated coverage or
a correction for all past/future research. No optimal threshold is established.

Retain the earlier crossed-bootstrap limitations: event-company resampling does
not model the full reused-control network; few long calendar blocks, sparse
crossed cells, data quality and previous inspection limit inference.

## Verification and deliverables

Verify SHA256 inputs and reproduce all source identities, event momentum and
non-overlap flags. Unit tests: exact ties/group boundaries, missing momentum,
ranking against the full eligible pool, no future-outcome dependence, joint
bootstrap arithmetic and reproducibility. Independently check sampled raw
momentum products including both endpoints, complete cross-sectional ranks,
all summary arithmetic and contribution sums. Keep script, config, features,
ranking pools, coverage, summaries, intervals and hash manifest.

Report positive, null, negative and non-monotonic patterns honestly. Decide
whether any single fixed threshold merits later validation; do not execute
another lookback, combined filter or portfolio in this study.
