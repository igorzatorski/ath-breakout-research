# Within-industry momentum on ATH events — results

Study: `ath_25_industry_momentum_v001`. Completed 2026-10-17.
Run: `outputs/research/ath/ath_25_industry_momentum_v001/20261017T123133361483Z`.
Protocol: `research/ath/ATH_INDUSTRY_MOMENTUM_PLAN.md`.

## Finding and decision

Within-industry 6-1 leadership adds little to the existing ATH + market-wide 6-1/top20 selection in this study. On the common supported sample, top50/top30 improve annual mean SPY excess by only +0.055/+0.022 pp, while top20 reduces it by -0.289 pp. All uncertainty intervals span zero and the strictest filter slightly worsens median/loss outcomes. Do not add a mandatory industry-momentum filter from these results. This is informative near-redundancy in an already strong market-momentum population, not proof that industry information never matters.

## Acquired classification data and limitations

A read-only WRDS export of `crsp_q_stock.stksecurityinfohist` produced 79,850 distinct effective-dated SIC records for 14,388 securities. Raw query, retrieval timestamp and mapping URL/hash are saved in `outputs/research/ath/shared_inputs/industry_history_v001`. No raw daily histories or prior outcomes were overwritten. There are zero overlapping, reversed or missing-date intervals in this export. Match PERMNO and inclusive effective start/end dates; do not fill history gaps or use current header codes. SIC0/9999/missing/noninteger/out-of-range codes are unclassified.

Valid codes map to the official frozen French12 SIC-industry grouping, with valid residual codes assigned Other. This is not GICS and does not replicate French's industry portfolio formation/returns. It is a broad twelve-group classification; more granular variants were not tested. Mapping source: [official SIC12 definitions](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Siccodes12.zip).

Important limitation: CRSP history has historical effective intervals but this export is the current database vintage. Original publication and revision timestamps are not supplied. Thus this is an effective-dated exploratory study, not guaranteed publication-time point-in-time data or independent validation. Do not claim that every backdated label was observable by investors at the time.

## Momentum rank and support

Use hash-verified original 6-1 eligible ranking pools, including both ATH/non-ATH securities and all market-momentum ranks. Do not restrict peers to market-top20 or ATH. Original momentum omits the latest21 sessions. Within each date x industry, percentile = (average ordinal rank -0.5)/N, preserving original security-level rather than unique-company ranking. Require at least20 classified securities. Top50/top30/top20 require percentile strictly greater than0.50/0.70/0.80, respectively. Ties stay together. No other momentum window, peer minimum or taxonomy was tried after results.

Original annual reference: 23,712 events, stock15.47%, SPY9.89%, excess+5.58 pp. Supported common reference: 21,809 events (91.97%), stock14.10%, SPY9.86%, excess+4.24 pp. Excluded1,903 events comprise1,902 with fewer than20 peers and one invalid SIC; zero annual events lack an effective history interval. Excluded events have excess+20.92 pp, making this a material support difference, not a filter effect. Early/middle/recent excluded counts are1,321/322/260. Do not directly compare the filtered means with the original+5.58 pp as if only rank thresholds changed.

Preserve all25,250 source signal identities and original23,712 annual outcomes, existing market6-1/top20, next-open entries, annual252-session stock/SPY total returns/distributions/terminal cash and original company nonoverlap flags. This is gross event analysis, not portfolio CAGR or allocation between stocks and cash.

## Main annual comparison on identical supported events

Stock/SPY columns are percentage returns; excess and improvement are percentage points. Every SPY observation uses the same dates as its stock event.

| Condition | Events | Stock % | SPY % | Excess pp | Improvement pp |
| --- | --- | --- | --- | --- | --- |
| Common reference | 21,809 | 14.10 | 9.86 | 4.24 | +0.000 |
| Top 50% | 21,648 | 14.32 | 10.02 | 4.29 | +0.055 |
| Top 30% | 20,716 | 14.45 | 10.19 | 4.26 | +0.022 |
| Top 20% | 17,708 | 14.34 | 10.39 | 3.95 | -0.289 |


Approximate pointwise improvement intervals (block252): top50 -0.084 to+0.265 pp; top30 -0.512 to+0.725 pp; top20 -1.964 to+1.219 pp. None of the three main/nonoverlap improvements has a positive pointwise or simultaneous-three lower bound at either252/504-session blocks. The existing crossed company/time bootstrap is approximate and family correction does not cover the entire research search. Here the main issue is also small or negative observed incremental effects, not merely a significance threshold.

Top50 retains99.26% of supported ATH/market-momentum events; top30 retains94.99%; top20 retains81.20%. Being a market-wide momentum leader already frequently implies high broad-industry momentum rank. This observed overlap explains why loose extra thresholds change so little; it does not identify a causal mechanism.

## Frozen repeat and period sensitivity

Excess and improvement are pp. These are diagnostics on already inspected history, not untouched validation.

| Weighting | Period | Condition | Events | Excess pp | Improvement pp |
| --- | --- | --- | --- | --- | --- |
| all | all | Reference | 21809 | 4.24 | +0.00 |
| all | all | Top20 | 17708 | 3.95 | -0.29 |
| all | early | Reference | 7141 | 16.76 | +0.00 |
| all | early | Top20 | 5402 | 16.98 | +0.22 |
| all | middle | Reference | 6570 | 1.20 | +0.00 |
| all | middle | Top20 | 5379 | 1.07 | -0.13 |
| all | recent | Reference | 8098 | -4.34 | +0.00 |
| all | recent | Top20 | 6927 | -3.97 | +0.37 |
| nonoverlap | all | Reference | 1587 | 3.16 | +0.00 |
| nonoverlap | all | Top20 | 1243 | 3.33 | +0.18 |
| nonoverlap | early | Reference | 513 | 12.03 | +0.00 |
| nonoverlap | early | Top20 | 371 | 12.20 | +0.17 |
| nonoverlap | middle | Reference | 466 | -0.61 | +0.00 |
| nonoverlap | middle | Top20 | 376 | -0.21 | +0.40 |
| nonoverlap | recent | Reference | 608 | -1.44 | +0.00 |
| nonoverlap | recent | Top20 | 496 | -0.61 | +0.84 |


Nonoverlap common reference+3.16 pp; top20+3.33 pp, improvement+0.18 pp, with interval-2.67 to+2.88 pp. Recent all-event common reference-4.34 pp; top20-3.97 pp, improvement+0.37 pp, still below SPY. Sensitivity estimates do not establish a stable useful benefit.

## Distribution and industry breakdown

Common reference versus top20: stock median3.10% versus2.84%; loss frequency45.23% versus45.46%; final>=100% winner frequency6.41% versus6.60%, retaining1,169 of1,398 such supported winners (83.62%). Large-winner frequency changes slightly but neither typical outcome nor mean excess improves. All >=200/300% tails, per-company/date weighting, annual cohorts and rejected complements are saved.

Saved per-industry mean excess varies materially and some industry/event cells are sparse (consumer durables has only16 reference events). These are descriptive breakdowns, not a search for favored sectors or an adopted sector allocation. Do not select industries retrospectively from these means.

## Verification and reproducibility

Independent verification passed 8,312,216 raw effective-interval/SIC classification checks and 12,467,541 direct peer-count/rank/support checks across all saved original ranking pools. Classification lookup uses interval membership rather than the production as-of join; direct ranks use counts below/equal via sorted values rather than pandas rank. Reconciled every source event's classification/rank, original IDs/momentum/ranks/returns/nonoverlap and 3,240 summary/tail/complement checks; supported counts, nested filters and industry-weighted reconciliation passed.

Six focused industry/shared-bootstrap tests passed. Ruff passed on new acquisition, feature, runner, verifier and tests. This is not a full repository test-suite claim.

Acquisition: `scripts/research/fetch_ath_industry_history.py`.
Feature: `src/ath_breakout/research/industry_momentum.py`.
Runner: `scripts/research/study_ath_industry_momentum.py`.
Verifier: `scripts/research/verify_ath_industry_momentum.py`.
Tests: `tests/research/test_industry_momentum.py`.
Outputs: events.parquet, coverage.csv, pool_coverage.csv, feature_audit.csv, summary.csv, uncertainty.csv, complement_summary.csv, by_industry.csv, by_year/ranking_YYYY.parquet, manifest.json, independent_verification.json.

The initial dry run failed before outcomes because WRDS nullable PERMNO needed normalization to the original pools' integer dtype. It is retained with a failure note; no parameter or methodological change followed results. Input hashes and the protocol identify the completed run.

## Next decision

Do not expand sector/momentum parameter searches merely to seek a positive result. The proposed standalone entry-filter pass is now complete enough to review candidate overlap before a small registered combination test. Keep momentum, range contraction, breakout-day relative volume, prior-record age and normalized breakout magnitude as previously qualified candidates. Their independence and combined value remain untested. No combined strategy, exit, ranking-based portfolio or market/cash allocation was executed here.
