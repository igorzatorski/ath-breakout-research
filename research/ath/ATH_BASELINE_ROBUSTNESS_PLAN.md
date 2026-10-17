# Annual ATH baseline: concentration, repeats and coverage

Study: `ath_10_baseline_robustness_v001`. Written before this study's results.
This is a diagnostic extension on already inspected history, not a filter search.

## Frozen inputs and estimands

Reuse ath_04 v002 event identities/features, ath_06 annual outcomes, ath_08
momentum-control outcomes and ath_09 CAPM outcomes. Verify saved SHA256 values.
Do not alter signals, returns, controls, exclusions or original artifacts.
No WRDS connection or download. No portfolio, costs, stop or factor-model search.

Primary population: all valid annual stock/SPY event pairs (71,961 previously).
Secondary: the frozen common momentum sample (43,824), and common CAPM sample
(39,561). Each comparison uses its own explicitly complete population.

Report event-weighted mean, median, equal-PERMNO, equal-PERMCO and equal-date
means; counts and three existing signal periods. The estimands are different;
none is an investable portfolio. PERMCO is the company identifier at signal time.

## Concentration

Aggregate counts and paired excess sums by PERMNO and historical PERMCO.
Each contribution to the overall event mean is group excess sum / all events.
Reconcile contributions exactly. Report positive and negative contributors,
event-count/mean-excess relationship, and top 1/5/10/20 company diagnostics.
Show shares of positive and negative excess separately, avoiding a small net
denominator. Leave-top/bottom-out figures are descriptive influence checks,
not permissible trading exclusions. Do not remove extremes from the baseline.

## One past-only non-overlap rule

Within each historical PERMCO, accept the earliest qualified signal and then
require a signal-date separation of at least 252 NYSE sessions. At a same-date
tie use the lowest PERMNO, then event ID. Select from ALL 75,884 source signals
before checking future execution, annual completeness or control availability.
Skipped signals do not extend the clock; state persists across years. This
ensures no overlap of scheduled next-open/252nd-close windows within a PERMCO.
It is not an optimized cooldown and does not make different companies independent.

## Uncertainty

2,000 draws, seed 20261016; circular calendar blocks of 252 sessions, plus a
504-session sensitivity. Jointly resample baseline and retained events.
Report date-only block bootstrap and a crossed company/date-block bootstrap:
resample event PERMCOs with replacement, independently resample calendar blocks,
and multiply company and calendar multiplicities for event sums/counts.
Use shared weights for baseline, retained and their difference.

These are approximate diagnostic percentile intervals, not guaranteed calibrated
tests: sparse crossed cells, limited long time blocks, reused control companies,
beta-estimation error and research selection remain limitations. Resampling
event companies does not independently model the full reused-control network.

## Coverage and exclusions

Reconstruct only the original signal-date candidate/quality gate from local raw
history, seed and PIT membership; reconcile every qualified event identity and
every year's uncertain-history potential-candidate count with ath_04 v002.
Save qualified and uncertain candidate features (size, ADV21, volatility and year).
Uncertain candidates are NOT certified ATHs and receive no claimed ATH returns.
Compare distributions and annual shares, and separately quantify annual censoring,
invalid paths, missing entry, original/momentum matching and CAPM attrition.
Compare observed outcomes only where genuinely available, and separate recent
right-censoring from historical missingness. Do not fill or rematch exclusions.

## Verification and decision

Test selection ties, cross-year state and future-outcome independence; exact
contribution arithmetic and bootstrap reproducibility/known-weight arithmetic.
Independently loop over all production selection decisions and aggregate saved
event rows to reconcile published numbers. Preserve manifests, inputs, code,
configuration, event flags and every diagnostic table.

Decide whether the baseline is suitable for a small registered filter hypothesis,
and identify which conclusions remain unsupported. Do not require a positive
unconditional ATH mean to permit a separately motivated conditional hypothesis.
