# Futures trend v001: first research prototype

Exploratory market-level futures simulation, not a validated executable futures track record. No optimization or independent OOS.

Common equity anchor 2016-03-31, first execution 2016-04-01, last mark 2024-03-28. 17 eligible market families of 20 candidates; initial capital USD 10 million.
EUR, JPY and CORN were excluded before portfolio performance calculation because priced-mark gaps exceeded the frozen three-session limit.
Monthly own-market 12-calendar-month direction, long/short; 60-session volatility/covariance, 10% target, sector allocation and caps.
Signal at close D executes close D+1 and first earns D+1 to D+2 changes. Negative adjusted levels are permitted; only price differences drive P&L and trend.

## Comparison

Rates are decimal fractions (0.01 = 1%). SPY includes dividends; all cash yields are zero.

|                     |      cagr |   annualized_volatility |   sharpe |   max_drawdown |   final_equity |   correlation_to_spy |
|:--------------------|----------:|------------------------:|---------:|---------------:|---------------:|---------------------:|
| futures_trend       | 0.0324478 |                0.109537 | 0.346591 |      -0.233951 |    1.29072e+07 |           0.00651045 |
| futures_always_long | 0.0251787 |                0.125654 | 0.261062 |      -0.35096  |    1.21985e+07 |           0.444774   |
| spy_buy_hold        | 0.142726  |                0.182182 | 0.824725 |      -0.337172 |    2.90444e+07 |           1          |
| spy_target_10       | 0.0897203 |                0.114736 | 0.807307 |      -0.23881  |    1.98707e+07 |           0.933175   |

## Annual returns

|   date |   futures_trend |   futures_always_long |   spy_buy_hold |   spy_target_10 |
|-------:|----------------:|----------------------:|---------------:|----------------:|
|   2016 |     -0.0567749  |           -0.00431355 |      0.0976984 |       0.0797725 |
|   2017 |      0.139286   |            0.269507   |      0.217054  |       0.216145  |
|   2018 |     -0.0932689  |           -0.132058   |     -0.04569   |      -0.0259055 |
|   2019 |      0.0307577  |            0.202149   |      0.312239  |       0.165613  |
|   2020 |      0.136397   |           -0.00382419 |      0.183316  |      -0.040282  |
|   2021 |     -0.00451564 |            0.0934671  |      0.287287  |       0.21019   |
|   2022 |      0.13545    |           -0.190169   |     -0.181754  |      -0.0926369 |
|   2023 |     -0.0951707  |            0.0524001  |      0.261758  |       0.153664  |
|   2024 |      0.105729   |           -0.00371324 |      0.103901  |       0.0961819 |

## Interpretation boundaries

The always-long futures control uses the same sizing model, helping distinguish direction from diversified risk allocation.
SPY buy-and-hold is full equity exposure. SPY target_10 uses lagged monthly 60-session volatility scaling, capped at 100% investment; no borrowing.
Realized volatility need not equal 10% or match across portfolios. Treat the full-risk SPY comparison as context, not an alpha test.
Trend gross notional averaged 2.99 NAV and peaked at 4.38 NAV. The 4x sizing cap applies at decision time, not continuously between monthly trades.

## Source and data audit

[pysystemtrade pinned source](https://github.com/pst-group/pysystemtrade/tree/164328bd76d2937d3dd61491377704c488283bc2/data/futures) supplies adjusted/multiple-price files and roll information.
Comparable adjusted intraday changes were reconciled against same-contract changes or the previous forward on a roll; coverage audit records zero mismatches.
Intraday source dates were collapsed to last valid daily rows. Missing NYSE-session marks were carried only within a three-session threshold; counts are in staleness.csv.
Source history ends March 2024 and common history is constrained by RUSSELL_mini starting March 2015. No claim about performance after March 2024.
Provider rolls are inherited (some commodity histories use seasonal/deferred contracts), not an assumed front-month strategy.

## Material implementation limitations

Fractional source units are not integer standard-contract holdings. SILVER source point value is 1,000 oz; standard SI uses another unit size.
Historical product/venue continuity, executable delivery/first-notice compliance, volume and historical spread/margin schedules remain unverified.
One optional RUSSELL_mini roll-calendar CSV is absent; source series transitions are observed from multiple-price IDs.
Fees/spreads are static source estimates per research unit, applied to quantity changes and both roll legs. No fund fees or taxes.
The margin proxy is illustrative, not a broker margin-call/liquidation model. Decisions are delayed one full session; fills at source marks remain an approximation.
Raw data and upstream license remain local and ignored by Git. Source code is independently authored; upstream code is read as documentation, never imported or executed.

## Reproduce

```powershell
.venv/Scripts/python.exe run/futures_fetch.py
.venv/Scripts/python.exe -m run.futures_audit
.venv/Scripts/python.exe -m run.futures_backtest
```

Artifacts: `outputs/trend_following_futures/baseline_v001/`. Frozen methodology: BASELINE_V001_PLAN.md.
