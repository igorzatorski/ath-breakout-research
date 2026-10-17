# ATH35: five fixed SMA exits since 2008

Completed 2026-10-17. Same ATH33 entries and accounting; only the exit SMA changes. Ten net variants, clean USD100,000 cash start on 2008-01-02 through 2026-06-30. Prior prices warm indicators only. Fresh ATH + market 6-1/top20, MV ranking, maximum 20 companies, 5% initial target. Drift versus monthly equal weight, 10 bps per buy/sell, zero cash yield. Close strictly below the selected SMA triggers the next observed opening sale. No additional 5% price floor.

## Full-period net results

| SMA | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown | Drift exposure | Monthly exposure |
|---|---:|---:|---:|---:|---:|---:|
| 50 | 5.84% | 6.53% | -46.49% | -44.60% | 80.13% | 79.82% |
| 100 | 8.76% | 8.57% | -49.29% | -47.25% | 87.71% | 87.44% |
| 150 | 8.70% | 8.48% | -45.28% | -44.49% | 90.24% | 90.46% |
| 200 | 9.88% | 8.88% | -50.81% | -51.24% | 92.10% | 92.45% |
| 250 | 10.26% | 10.30% | -45.48% | -44.53% | 92.52% | 93.00% |
| SPY | 11.24% | 11.24% | -52.45% | -52.45% | 100% | 100% |

## Recent-period stability

| SMA | Since 2018 drift CAGR | Since 2018 monthly CAGR | Since 2023 drift CAGR | Since 2023 monthly CAGR |
|---|---:|---:|---:|---:|
| 50 | 6.03% | 7.60% | 6.67% | 7.61% |
| 100 | 4.86% | 4.28% | 10.95% | 8.42% |
| 150 | 6.89% | 6.55% | 8.53% | 5.48% |
| 200 | 8.15% | 7.15% | 20.53% | 15.37% |
| 250 | 9.01% | 8.49% | 19.20% | 15.80% |
| SPY | 14.67% | 14.67% | 22.83% | 22.83% |

These are calendar slices of the clean 2008 simulation, retaining positions at each subperiod boundary; they are not fresh 2018/2023 starts.

## Trading and concentration

| SMA | Policy | Entries | SMA exits | Total fees USD | Annual two-way traded notional / daily NAV | Maximum name weight | Closed losing episodes | Median calendar days, closed losing episodes |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sma50 | drift | 2011 | 1918 | 33024.21 | 9.94x | 16.02% | 1214 | 29 |
| sma50 | monthly_equal | 2012 | 1919 | 37994.88 | 10.80x | 10.09% | 1204 | 29 |
| sma100 | drift | 1155 | 1068 | 26314.63 | 5.45x | 18.23% | 674 | 57 |
| sma100 | monthly_equal | 1160 | 1071 | 32280.89 | 6.45x | 10.21% | 659 | 56 |
| sma150 | drift | 809 | 745 | 17144.30 | 3.68x | 35.74% | 468 | 80 |
| sma150 | monthly_equal | 806 | 742 | 23061.32 | 4.73x | 10.09% | 453 | 80 |
| sma200 | drift | 635 | 566 | 12744.86 | 2.82x | 34.16% | 352 | 105 |
| sma200 | monthly_equal | 638 | 566 | 16937.86 | 3.89x | 9.88% | 331 | 99 |
| sma250 | drift | 525 | 458 | 10858.75 | 2.23x | 35.00% | 299 | 154 |
| sma250 | monthly_equal | 521 | 454 | 17502.86 | 3.31x | 10.04% | 272 | 142 |

Turnover sums absolute executed buy/sell notional divided by contemporaneous pre-trade NAV, annualized by 252/4652. Excludes cash distributions and forced terminal settlements. Closed-episode diagnostics omit open positions and are hindsight conditional; monthly cashflow profit ratios are not fixed-unit trade returns.

## Interpretation

All ten variants lag SPY in full-period CAGR. SMA250 is highest among these inspected full-period points; SMA150 slightly trails SMA100 and SMA200 drift beats SMA250 drift since 2023, so there is no uniformly improving gradient or established optimum. Longer averages increase invested exposure and change capacity, subsequent entries, holding periods and concentration. This is a complete rule comparison, not an identical-trade pure-exit counterfactual. An SMA exit does not guarantee a small loss or fast response after entry. Drift allows substantial winner weights above the initial 5%; monthly equalization trims winners. Neither policy maintains guaranteed full investment.

No confirmed risk-adjusted alpha, confidence claim or untouched validation is implied by selecting the largest CAGR on inspected development history. SPY is a broad opportunity-cost benchmark, not equal-risk matching. No new entry filter or price floor was added.

## Verification

All 17 focused engine/adapter tests passed. All 100 SMA50/SMA200 period rows exactly reproduce ATH33 CAGR, NAV, drawdown and exposure. Independently rebuilt 46,008,280 five-window feature cells, 250 calendar summary rows and ten SPY curves. All ten independent next-open/trigger/cash/share replays passed, including required exits, original decisions, dividends, terminal settlements, monthly targets and daily ledger balances. Source raw files and source panels are SHA256 recorded; earlier runs are preserved.

Run: `outputs\backtests\ath_35_sma_exit_grid_v001\20261017T182520632223Z`. Reproduce with `scripts/research/backtest_ath_sma_exit_grid.py`; audit with `verify_ath_sma_exit_grid.py` and `verify_ath_sma_exit_features.py`.
