# Frozen momentum lookback comparison: 12-1, 6-1 and 3-1

Study: `ath_12_momentum_lookbacks_v001`. Written before shorter-lookback outcomes.
The user authorized exactly two additional momentum definitions, not a search
until significance appears. Preserve the prior 12-1 study and every trial.

## Definitions

At signal session t, compound scheduled CRSP total returns, including dividends:

- 12-1: t-251 through t-21 inclusive, 231 returns (existing definition).
- 6-1: t-125 through t-21 inclusive, 105 returns.
- 3-1: t-62 through t-21 inclusive, 42 returns.

All exclude the latest 21 sessions; 6-1 and 3-1 therefore cover approximately
five and two months respectively, not six/three months including the last month.
Every scheduled return must be finite and >= -1. No gap bridging or imputation.

Keep original ATH events, history-quality/PIT membership/ADV21 rules, next-open
entry, 252-session return horizon, SPY, fixed 12-1 matched-control IDs/outcomes,
and company-level ath_10 non-overlap flags. No WRDS, download, cost model,
stops, portfolio or additional lookback. Source ath_11 12-1 ranks must reconcile.

## Ranking and comparable populations

For each lookback rank within the entire same-date originally eligible universe
with that lookback observed. Include ATH and non-ATH stocks; use the same tied
mid-distribution ranks and Q1-Q5/top60/top40/top20 rules as ath_11. Shorter
lookbacks naturally admit younger/gappier histories; do not silently force a
long-history denominator or use future eligibility. Save all ranking pools.

PRIMARY comparison: identical ATH annual event IDs with all three lookbacks
observed. Recompute every filter and the unfiltered baseline on this common
population. Natural-availability samples are explicitly secondary, with counts
and observed outcomes for included/excluded events. A change from a full-sample
12-1 result to a larger short-lookback sample is not a pure lookback effect.

Cross-sectional rank denominators remain the natural contemporaneous eligible
pool for each definition. Thus the comparison includes the defined measurement
and its available reference population; no claim of isolating only time-window
length from all denominator changes is made.

## Comparisons

For each lookback and five groups/three thresholds show common-sample annual
stock/SPY excess, means, medians, loss/quantile risk, security/company counts,
equal-company/security/date weights, three existing periods and yearly results.
Repeat on frozen non-overlap flags WITHOUT restarting clocks inside filters.
Secondary comparison uses the common events with five complete ORIGINAL 12-1
momentum-matched controls. Those controls are not rematched for 6-1/3-1, so they
control the earlier 12-1 measure, not each shorter measure. Label this explicitly.

Also show available-sample point estimates, but do not use a favorable sample
to select a winner. Save top-company contributions and event-level features.

## Joint uncertainty and multiplicity

Cross event-PERMCO resampling with circular date blocks, 2,000 draws, seed
20261016; block lengths 252 and 504. Use identical weights for all lookbacks,
groups and thresholds within a sample. Estimate filter levels and improvements
over the same unfiltered common baseline, Q5-Q1, and shorter-minus-12-1 contrasts
at each corresponding threshold.

Predeclared primary family: NINE filter improvements (three thresholds times
three lookbacks) versus baseline in the common all-event annual SPY sample.
Report pointwise percentile intervals and an approximate simultaneous band
using the bootstrap 95th percentile of maximum absolute centered error across
all nine contrasts. This is not a correction for the complete past/future
research program or proof of calibrated coverage. Preserve weak/null results.

Inference remains approximate: few independent long calendar blocks, company
dependence, sparse groups, reused controls, selected history and prior inspection.
No winning parameter, persistent alpha or investable return follows merely from
the largest historical mean or one positive interval.

## Verification and reporting

Unit-test exact lag endpoints, missing/invalid/terminal-loss returns, no future
information and joint-bootstrap arithmetic. Verify saved input hashes, all
source identities/12-1 ranks, fixed returns/selection, independent cross-sectional
ranks and sampled raw products for both new lookbacks. Reconcile all summary
means and contributor sums. Record source/code/protocol hashes and test scope.

Deliver one English report, experiment registry entry and Notion research note,
with common and natural population differences explicit. No further variant is
authorized by a null result in this study.
