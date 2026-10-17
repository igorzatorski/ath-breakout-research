# Stock SMA position and trend alignment — results

Study: `ath_23_sma_trend_v001`.
Run: `outputs/research/ath/ath_23_sma_trend_v001/20261016T224823303917Z`.
Protocol: `research/ath/ATH_SMA_PLAN.md`.

## Finding

Stock price above SMA20/50/100/200 retains every original annual ATH/momentum event, making all four conditions redundant on this population. The two trend alignments remove only 0.62% and 2.13% of events and leave annual mean excess practically unchanged. There is no useful incremental mean-return selection demonstrated here. This result concerns these definitions and this already strong ATH/momentum population, not all uses of moving averages.

## Frozen definitions and coverage

Same ATH + common 6-1 momentum/top20 source: 25,250 source signals and 23,712 complete annual stock/SPY pairs. Each SMA is an arithmetic mean of positive split-adjusted closes over exactly 20/50/100/200 scheduled NYSE sessions through the signal close, including that close. Signals are acted on at the original next open. All scheduled observations are required. No missing prices are forward filled and no calendar gaps are skipped. Close adjustment is close / price_adjustment_factor as in the existing ATH layer. Strict comparisons treat relative differences <=1e-12 as equality.

Exactly six standalone filters: price>SMA20/50/100/200; SMA100>SMA200; SMA50>SMA100>SMA200. The last is a conjunction of the two prescribed alignments, not an interaction with volume/consolidation filters. No SPY regime, slope, extra window, exit, ranking or portfolio was run.

All four SMA features and signal closes are observed for every annual event: no feature-support exclusions. Original and common references are identical. The annual next-open execution, returns including distributions, terminal cash and original company nonoverlap flags are unchanged.

## Main annual results

Stock and SPY columns are percentage returns; excess and improvement are percentage points. Each SPY mean uses precisely the selected events' return windows.

| Condition | Events | Retained % | Stock % | SPY % | Excess pp | Improvement pp |
|---|---:|---:|---:|---:|---:|---:|
| reference | 23,712 | 100.00 | 15.47 | 9.89 | 5.579 | +0.000 |
| price_gt20 | 23,712 | 100.00 | 15.47 | 9.89 | 5.579 | +0.000 |
| price_gt50 | 23,712 | 100.00 | 15.47 | 9.89 | 5.579 | +0.000 |
| price_gt100 | 23,712 | 100.00 | 15.47 | 9.89 | 5.579 | +0.000 |
| price_gt200 | 23,712 | 100.00 | 15.47 | 9.89 | 5.579 | +0.000 |
| sma100_gt200 | 23,564 | 99.38 | 15.48 | 9.88 | 5.608 | +0.029 |
| sma50_gt100_gt200 | 23,208 | 97.87 | 15.36 | 9.78 | 5.573 | -0.006 |

The four price-position filters produce identical event IDs and returns to the reference; their improvements and bootstrap contrast bounds are exactly zero. This is mechanical redundancy, not proof of a newly profitable factor. Under a comparable-price true ATH definition, the signal close is above all previous observed comparable closes, hence above their moving averages even when the current close is included.

SMA100>SMA200 retains 23,564 events, removing 148. Improvement is +0.029 pp, pointwise approximate interval -0.120 to +0.168 pp (block252). SMA50>SMA100>SMA200 retains 23,208, removing 504. Improvement is -0.006 pp, interval -0.283 to +0.288 pp. No positive main improvement lower bound occurs in either pointwise or simultaneous-six bands at either block252 or504. The intervals concern incremental improvement, not the return range of individual trades. The existing crossed company/date bootstrap remains approximate; the six-test family does not account for the entire prior research search.

## Repeat, period and tail sensitivity

Original company nonoverlap reference: 1,725 events, +3.642 pp SPY excess. SMA100>SMA200: 1,690 events, +3.650 pp (+0.008 pp improvement). Full alignment: 1,637 events, +3.553 pp (-0.089 pp). Results do not reveal a meaningful hidden benefit under this alternate repeat treatment.

Original early/middle/recent mean excess: +17.110/+0.896/-2.235 pp. SMA100>SMA200: +17.241/+0.909/-2.311 pp. Full alignment: +17.169/+0.893/-2.406 pp. The trend conditions slightly worsen recent means rather than explaining the recent weakness. These are descriptive sensitivities on already inspected history, not independent validation.

Final >=100% winner frequency: reference6.739%, SMA100>SMA2006.748%, fullalignment6.748%. Counts are1598/1590/1566, respectively. Median stock returns3.663/3.655/3.529%; losses44.598/44.640/44.812%. No substantial improvement in tail frequency or median/loss profile is apparent. All annual cohorts, company/date weighting, >=200/300% results and rejected-event complement outcomes are retained in the output files.

## Verification

Independent direct arithmetic means from exact raw scheduled windows, without using the production rolling function: 252,500 SMA/membership checks across every source event. Reconciled frozen identities, stock/SPY/excess returns, momentum ranks and original nonoverlap flags; common support, trend hierarchy and complement counts; 5,832 summary/tail/complement checks. All passed. Five focused SMA/shared-bootstrap tests passed; Ruff passed on the feature, runner, independent verifier and tests. This does not claim a full repository test-suite run.

Runner: `scripts/research/study_ath_sma.py`.
Verifier: `scripts/research/verify_ath_sma.py`.
Feature: `src/ath_breakout/research/sma_trend.py`.
Tests: `tests/research/test_sma_trend.py`.
Outputs: events.parquet, coverage.csv, feature_audit.csv, summary.csv, uncertainty.csv, complement_summary.csv, manifest.json, independent_verification.json.

## Decision

Do not add these SMA conditions as mandatory extra entry filters. Four are redundant and the remaining two change little while adding rules. Keep this negative/informative experiment in the registry. This does not answer whether past SMA slopes, distance from SMA or the market's SMA state matter; those are separate, unexecuted hypotheses and should not be silently added after these results. Exits, ranking and portfolio remain deferred.
