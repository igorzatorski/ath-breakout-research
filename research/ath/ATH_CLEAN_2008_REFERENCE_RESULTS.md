# ATH33: clean cash-start2008 portfolio reference

Completed2026-10-17. This replaces the inherited-position slice as the principal2008 portfolio reference. All eight fixed net variants still underperform SPY in CAGR. No new entry, ranking, filter, stop threshold or SMA length was introduced.

## Initialization and execution

USD100,000 cash, zero positions, zero old entry anchors and zero pending2007 sell orders before2008-01-02. End2026-06-30;4,652 NYSE sessions. First actual entry is2008-01-03 from a2008-01-02 signal. Older prices warm indicators only. No inherited2007 PnL. Same fresh ATH plus6-1/top20 candidates, MV ranking, maximum20 distinct companies,5% entry target, drift/monthly-equal policies, zero cash yield and10bps per buy/sell. Both price-floor and trend exits use closing signals and next observed opening fills. No loss guarantee. SPY starts at the first2008 opening, with the same entry cost.

## Full-window net results

| Exit | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |
| --- | ---: | ---: | ---: | ---: |
| SMA50 | 5.84% | 6.53% | -46.49% | -44.60% |
| 5% entry floor + SMA50 | 4.51% | 3.88% | -51.77% | -49.30% |
| SMA200 | 9.88% | 8.88% | -50.81% | -51.24% |
| 5% entry floor + SMA200 | 8.59% | 7.26% | -45.42% | -50.16% |
| SPY | 11.24% | 11.24% | -52.45% | -52.45% |

SMA200 drift ends at USD569,705 versus SPY USD714,793. Its CAGR9.88% differs from the old cropped9.38% because clean initialization changes executed positions and capital paths. Candidate floor+SMA200 gives8.59% drift /7.26% monthly; gross references9.22%/7.99% also trail corresponding gross SPY11.25%. The original floor remains anchored at the first purchase, never reset by rebalancing.

## Frozen calendar subperiods

| Period | Exit | Weight policy | CAGR | SPY CAGR | Mean invested |
| --- | --- | --- | ---: | ---: | ---: |
| 2008_2017 | SMA50 | drift | 5.68% | 8.42% | 75.64% |
| 2018_2022 | SMA50 | drift | 5.59% | 9.32% | 84.58% |
| 2023_end | SMA50 | drift | 6.67% | 22.83% | 86.63% |
| 2008_2017 | SMA50 | monthly_equal | 5.63% | 8.42% | 75.27% |
| 2018_2022 | SMA50 | monthly_equal | 7.59% | 9.32% | 84.34% |
| 2023_end | SMA50 | monthly_equal | 7.61% | 22.83% | 86.40% |
| 2008_2017 | SMA200 | drift | 11.37% | 8.42% | 89.15% |
| 2018_2022 | SMA200 | drift | 0.31% | 9.32% | 95.18% |
| 2023_end | SMA200 | drift | 20.53% | 22.83% | 96.15% |
| 2008_2017 | SMA200 | monthly_equal | 10.37% | 8.42% | 89.09% |
| 2018_2022 | SMA200 | monthly_equal | 1.78% | 9.32% | 95.80% |
| 2023_end | SMA200 | monthly_equal | 15.37% | 22.83% | 97.31% |
| 2008_2017 | 5% entry floor + SMA200 | drift | 8.75% | 8.42% | 82.09% |
| 2018_2022 | 5% entry floor + SMA200 | drift | 0.89% | 9.32% | 89.36% |
| 2023_end | 5% entry floor + SMA200 | drift | 20.22% | 22.83% | 93.69% |
| 2008_2017 | 5% entry floor + SMA200 | monthly_equal | 8.22% | 8.42% | 80.66% |
| 2018_2022 | 5% entry floor + SMA200 | monthly_equal | -0.29% | 9.32% | 89.39% |
| 2023_end | 5% entry floor + SMA200 | monthly_equal | 16.12% | 22.83% | 92.87% |

These are continuing calendar portfolios from the new clean start, not independent restarts at each subperiod. All250 variant/period summaries, including individual years, are retained.2026 annual-row CAGR is annualized from its partial window, not a realized full-year forecast.

## Exposure and limitations

SMA200 drift is about92.10% invested on average and can reach34.16% in one company. Floor+SMA200 drift is86.24% invested and reaches36.19% in one company. Monthly maximum weights are about10%. A5% entry target is not a permanent position cap. These unequal exposures/concentrations and different executed entries prevent a pure exit-treatment or equal-risk alpha conclusion. Cash-market allocation, interest on cash, impact, taxes and untouched validation remain untested. Dividend cash is available on ex-date, as in earlier models.

## Verification

Thirteen focused engine/boundary tests passed. Independent replay verified all ten variants: every first qualifying exit close, earliest executable opening, original entry anchor, cash/share/fee/distribution accounting, terminal-once settlement, fresh entry timing, capacity/unique company, daily marks and monthly targets. Raw source reconstruction verified9,201,656 SMA200 cells,250 calendar summaries and ten SPY curves. Boundary checks confirm no inherited holdings/anchors/orders. Cashflow PnL reconciles to final wealth. Ruff passed.

## Decision and files

Keep the whole fixed strategy set as the benchmark bundle; do not promote the highest observed rule as optimal. ATH34 separately re-expresses the earlier signal/filter evidence on2008 signal dates. Signals/events are gross fixed-horizon means and are not portfolio CAGR.
Run: `outputs/backtests/ath_33_clean_2008_reference_v001/20261017T175657998145Z`. Protocol: `research/ath/ATH_CLEAN_2008_REFERENCE_PLAN.md`. Engine code unchanged. Reproduce with `scripts/research/backtest_ath_clean_2008.py`, then `verify_ath_clean_2008.py RUN [RULE]` and `verify_ath_clean_2008_features.py RUN`. `inherited_comparison.csv` records every net boundary difference.
