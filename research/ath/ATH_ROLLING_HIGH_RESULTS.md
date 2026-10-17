# ATH38: ATH versus one- to five-year maxima

Same US equity strategy and original gain stages SMA150 ->100 at+50% ->50 at+100%. Only the signal high lookback changes. Clean USD100,000 cash start2008-01-02 through2026-06-30, maximum20 companies,5% entry target, MV priority and same historical liquidity/momentum support. Two weighting policies,10bps per buy/sell, zero cash yield. Next-opening entries and exits. No consolidation cutoff, opening-gap cap or initial price floor. This is a US implementation, not an audited GPW replication of the supplied screenshots.

## Full-period net CAGR and drawdown

| Maximum | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |
|---|---:|---:|---:|---:|
| ath | 9.29% | 9.07% | -44.51% | -43.15% |
| high1y | 4.61% | 4.81% | -54.06% | -52.47% |
| high2y | 6.48% | 6.20% | -42.29% | -42.03% |
| high3y | 7.36% | 7.43% | -38.42% | -37.65% |
| high4y | 8.90% | 8.95% | -35.28% | -36.27% |
| high5y | 6.72% | 6.31% | -34.59% | -36.12% |
| SPY | 11.24% | 11.24% | -52.45% | -52.45% |

## Contemporary calendar slices

| Maximum | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |
|---|---:|---:|---:|---:|
| ath | 8.20% | 6.58% | 13.03% | 8.46% |
| high1y | 4.24% | 3.83% | 9.50% | 7.39% |
| high2y | 7.21% | 6.87% | 21.33% | 15.69% |
| high3y | 7.42% | 8.05% | 21.50% | 20.18% |
| high4y | 11.96% | 12.35% | 28.57% | 24.94% |
| high5y | 8.40% | 7.50% | 23.36% | 20.17% |
| SPY | 14.67% | 14.67% | 22.83% | 22.83% |

These are calendar slices with inherited positions from the clean2008 simulation, not fresh2018/2023 starts. All years remain in summary.csv.

## Signal overlap and history requirements

| Definition | Signals | Non-ATH additions | Retained ATH signals | ATH excluded for incomplete rolling history |
|---|---:|---:|---:|---:|
| ath | 17285 | 0 | 17285 | 0 |
| high1y | 30507 | 13222 | 17285 | 0 |
| high2y | 23418 | 8268 | 15150 | 2135 |
| high3y | 18910 | 5470 | 13440 | 3845 |
| high4y | 15873 | 3992 | 11881 | 5404 |
| high5y | 13795 | 3075 | 10720 | 6565 |

Counts include2007-12-31 signals eligible for the first2008 opening and final 2026-06-30 signals with no subsequent executable session in this run. Full252/504/756/1008/1260 scheduled high histories are required. All definitions retain the original conservative pre1993/missing-high quality exclusions. Consequently longer rolling maxima can drop young ATH stocks as well as add recovery breakouts. This is not an isolated threshold-only comparison on identical listing-age support. No common-five-year-history portfolio was tested.

## Right-tail and actual portfolio attribution

| Run | Entries | Non-ATH entries | Cashflow >=100% episodes | Top5 episodes / net PnL | Non-ATH PnL USD |
|---|---:|---:|---:|---:|---:|
| ath__drift_10bps | 878 | 0 | 24 | 46.9% | 0.00 |
| ath__monthly_equal_10bps | 875 | 0 | 10 | 35.7% | 0.00 |
| high1y__drift_10bps | 1027 | 525 | 26 | 60.7% | 37444.24 |
| high1y__monthly_equal_10bps | 1027 | 529 | 10 | 53.3% | 50622.25 |
| high2y__drift_10bps | 945 | 396 | 22 | 48.3% | 75171.01 |
| high2y__monthly_equal_10bps | 942 | 395 | 7 | 40.0% | 69022.42 |
| high3y__drift_10bps | 925 | 324 | 23 | 43.4% | 87659.57 |
| high3y__monthly_equal_10bps | 929 | 327 | 7 | 32.8% | 109526.80 |
| high4y__drift_10bps | 887 | 276 | 20 | 39.4% | 139938.75 |
| high4y__monthly_equal_10bps | 886 | 277 | 12 | 36.5% | 156978.51 |
| high5y__drift_10bps | 869 | 243 | 15 | 49.4% | 50455.34 |
| high5y__monthly_equal_10bps | 868 | 245 | 7 | 40.6% | 55224.41 |

Episodes include both closed positions and open marked positions; their net cashflow PnL reconciles exactly to final portfolio NAV minus initial cash. >=100% means episode profit relative to accumulated purchases including fees; monthly buys/sells make this different from a fixed-unit stock price gain. Top5 contributions may exceed100% because other trades lose money. Non-ATH PnL is attribution of this realized path, not the causal value of adding those signals; ranks, capacity and subsequent entries also change. Detailed episodes, top20 contributors, company PnL, fees and turnover are retained.

## Findings and limits

ATH has the highest full-period CAGR among the six definitions under both policies. The two-year maximum underperforms ATH over the full period; it does not explain the supplied account results by itself. More candidates or higher exposure do not guarantee better selection. All full-period and since2018 CAGRs remain below SPY.

Contemporary ordering differs: the four-year maximum improves since2018 CAGR relative to ATH, and since2023 it exceeds SPY in both policies (28.57/24.94% versus22.83%). The five-year drift variant also slightly exceeds SPY since2023. These short inspected slices and selected maxima do not establish stable alpha or an optimal lookback. Do not delete weak earlier years or treat2023 as untouched validation.

A complete author strategy replication remains unavailable: different market, unspecified consolidation and position sizing, and unverified reported account methodology. The US liquidity threshold and momentum/ranking rules remain our research choices. No new confidence interval, equal-risk alpha inference, causal decay explanation, GPW result or live-ready strategy is claimed.

## Verification

All 50 ATH control period rows exactly reproduce ATH36 primary stepped exits. Signal keys, momentum, volume, contraction and MV scores reproduce the earlier ATH control for every modern signal. Independently audited all119,788 raw signal windows and3,607,887 market-pool rank rows. All12 daily cash/share/required-exit/stage replays passed. Independently rebuilt27,730,572 SMA cells,300 calendar summaries and12 SPY curves. The auditor price-product rounding discrepancy at64.20 ->96.30 was resolved by reconstructing the declared percentage gain; portfolio engine and trades were unchanged. Receipts and final status are in manifest.json. Twelve focused window/rank/stage tests passed, including a decimal50% boundary regression. Source files and code are hash recorded.

Run: `outputs\backtests\ath_38_rolling_highs_v001\20261017T191148442382Z`. Protocol: `ATH_ROLLING_HIGH_PLAN.md`.
