# ATH36: gain-triggered stepped SMA exits

Same clean cash-start 2008-01-02 to 2026-06-30, entries, MV ranking, 20-company capacity, 5% entry target, costs of 10bps per buy/sell and zero cash yield as ATH35. No initial 5% price floor. Start on SMA150, permanently switch to SMA100 and then SMA50 after the two fixed closing-price gain thresholds from original executed opening. Monthly trades preserve anchors and stages; reentry resets them. Threshold equality activates, including an entry-day jump across both thresholds. Exit after a strictly below-SMA close at the next observed opening. Current SMA includes the signal close. 

## Net CAGR and drawdown

| Schedule | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |
|---|---:|---:|---:|---:|
| sma150 | 8.70% | 8.48% | -45.28% | -44.49% |
| step25_50 | 11.22% | 9.96% | -39.44% | -40.02% |
| step50_100 | 9.29% | 9.07% | -44.51% | -43.15% |
| step100_200 | 9.30% | 9.13% | -44.92% | -44.08% |
| SPY | 11.24% | 11.24% | -52.45% | -52.45% |

## Recent calendar slices

| Schedule | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |
|---|---:|---:|---:|---:|
| sma150 | 6.89% | 6.55% | 8.53% | 5.48% |
| step25_50 | 10.09% | 7.21% | 16.39% | 9.62% |
| step50_100 | 8.20% | 6.58% | 13.03% | 8.46% |
| step100_200 | 6.35% | 6.35% | 8.34% | 5.77% |
| SPY | 14.67% | 14.67% | 22.83% | 22.83% |

Recent slices retain positions from the 2008 simulation; no fresh 2018/2023 starts. Every year and fixed period is retained in summary.csv.

## Stage and trading diagnostics

| Run | Switches | To numerically lower SMA | Entries | Fees USD | Annual two-way turnover | Median losing hold, calendar days |
|---|---:|---:|---:|---:|---:|---:|
| sma150__drift_10bps | 0 | 0 | 809 | 17144.30 | 3.68x | 80 |
| sma150__monthly_equal_10bps | 0 | 0 | 806 | 23061.32 | 4.73x | 80 |
| step25_50__drift_10bps | 549 | 0 | 958 | 26513.71 | 4.65x | 79 |
| step25_50__monthly_equal_10bps | 544 | 0 | 959 | 30623.47 | 5.47x | 79 |
| step50_100__drift_10bps | 229 | 0 | 878 | 19589.30 | 4.21x | 83 |
| step50_100__monthly_equal_10bps | 228 | 0 | 875 | 25830.93 | 5.05x | 82 |
| step100_200__drift_10bps | 67 | 0 | 825 | 20230.18 | 3.89x | 82 |
| step100_200__monthly_equal_10bps | 70 | 0 | 823 | 26194.40 | 4.81x | 80 |

Turnover sums absolute buy/sell notional divided by transaction pre-trade NAV, annualized by 252/4652; excludes dividends and terminal settlements. Losing holds are hindsight-conditional closed episodes, omitting open positions. Monthly cashflow episode ratios are not fixed-unit security returns. Full concentration/exposure metrics remain in summary.csv.

## Interpretation and limits

The primary +50/+100% schedule improves full-history net CAGR over SMA150 in both policies, but remains below SPY. The faster +25/+50% schedule is the strongest of these inspected points and drift nearly matches SPY with a smaller drawdown. All schedules still lag SPY in CAGR, and recent gaps are material. The late +100/+200% schedule does not improve since2018 or since2023 drift CAGR over constant SMA150. No uniformly optimal schedule or confirmed alpha is established.

This rule tightens exits after appreciation; initial losing entries still use SMA150. It therefore does not directly solve fast initial loss cutting. Shorter SMA windows are not a numerical price ratchet and do not guarantee a protected profit or maximum loss. All observed stage changes in these runs selected a higher or equal numerical SMA, but that is an empirical result, not a rule guarantee.

Earlier exits change capacity, later entries, costs and concentration, so portfolio differences are not identical-trade causal exit effects. Drift winner weights can exceed 5%; monthly equalization trims them. Missing opportunities and cash balances mean neither policy guarantees full investment. Comparisons with SPY do not isolate entry selection, risk exposures, timing, cash drag or diversification. No causal single reason for benchmark underperformance is established by this study. Different risk/drawdown is relevant even when CAGR is lower. All history is inspected development data; the best schedule has selection bias and no newly estimated uncertainty or unseen-data confirmation.

## Verification

All 50 SMA150 control period rows exactly match ATH35 CAGR/NAV/drawdown/exposure. 22 focused adapter/ledger tests passed. All eight independent daily cash/share/trigger/next-opening replays passed, including all 1,687 stage transitions. Independently rebuilt 46,008,280 raw SMA cells, 200 calendar summaries and eight SPY curves. Source hashes and final status are recorded in manifest.json.

Run: `outputs\backtests\ath_36_stepped_sma_v001\20261017T184040153319Z`. Protocol: `ATH_STEPPED_SMA_PLAN.md`.
