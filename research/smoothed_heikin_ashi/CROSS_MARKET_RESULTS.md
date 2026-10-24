# SHA cross-market comparison and drawdown diagnostic

Exploratory 400-pair daily EMA grids. SPY uses the saved grid; QQQ and BTC use separate public snapshots.
QQQ is a Nasdaq-100 ETF proxy, not Nasdaq Composite. BTC-USD is Yahoo's USD reference series, not guaranteed exchange fills.
All data end 2026-10-05. Native histories differ; comparisons below do not isolate a market effect.
Long/cash, next-open fills, fees 10 bps + slippage 5 bps per side, dividends reinvested with costs, zero cash yield.
ETF Sharpe annualization: 252; BTC: 365. CAGR uses elapsed calendar time. All strategies start after 50 warm-up bars.

## Native-history comparison

Rates below are decimal fractions (0.01 = 1%). Means exclude open trades.

| asset   | variant      |   pre_span |   post_span |      cagr |   sharpe |   max_drawdown |   win_rate |   mean_holding_calendar_days |   median_holding_calendar_days |   completed_trades |
|:--------|:-------------|-----------:|------------:|----------:|---------:|---------------:|-----------:|-----------------------------:|-------------------------------:|-------------------:|
| SPY     | 10/10        |         10 |          10 | 0.0415155 | 0.42226  |      -0.334386 |   0.39801  |                      39.3781 |                           27   |                201 |
| SPY     | best_CAGR    |         18 |          20 | 0.0598584 | 0.566244 |      -0.3471   |   0.454545 |                      74.8455 |                           55.5 |                110 |
| SPY     | best_Sharpe  |         18 |          20 | 0.0598584 | 0.566244 |      -0.3471   |   0.454545 |                      74.8455 |                           55.5 |                110 |
| SPY     | buy_and_hold |        nan |         nan | 0.108208  | 0.647227 |      -0.552097 | nan        |                     nan      |                          nan   |                  0 |
| QQQ     | 10/10        |         10 |          10 | 0.0622803 | 0.455235 |      -0.511547 |   0.432099 |                      38.5556 |                           28   |                162 |
| QQQ     | best_CAGR    |         10 |          14 | 0.076082  | 0.532242 |      -0.447872 |   0.433824 |                      46.5662 |                           34   |                136 |
| QQQ     | best_Sharpe  |         10 |          14 | 0.076082  | 0.532242 |      -0.447872 |   0.433824 |                      46.5662 |                           34   |                136 |
| QQQ     | buy_and_hold |        nan |         nan | 0.108425  | 0.518668 |      -0.829639 | nan        |                     nan      |                          nan   |                  0 |
| BTC_USD | 10/10        |         10 |          10 | 0.551352  | 1.17159  |      -0.675729 |   0.408163 |                      24.5102 |                           17   |                 98 |
| BTC_USD | best_CAGR    |         17 |          17 | 0.674285  | 1.30758  |      -0.577761 |   0.431034 |                      41.5172 |                           28.5 |                 58 |
| BTC_USD | best_Sharpe  |         17 |          17 | 0.674285  | 1.30758  |      -0.577761 |   0.431034 |                      41.5172 |                           28.5 |                 58 |
| BTC_USD | buy_and_hold |        nan |         nan | 0.58687   | 1.03159  |      -0.83399  | nan        |                     nan      |                          nan   |                  0 |

## Fixed 10/10 on common history

| asset   | variant      | start      | end        |      cagr |   sharpe |   max_drawdown |
|:--------|:-------------|:-----------|:-----------|----------:|---------:|---------------:|
| SPY     | 10/10        | 2014-11-07 | 2026-10-05 | 0.0598341 | 0.612742 |      -0.1927   |
| SPY     | buy_and_hold | 2014-11-07 | 2026-10-05 | 0.137616  | 0.828135 |      -0.337233 |
| QQQ     | 10/10        | 2014-11-07 | 2026-10-05 | 0.104273  | 0.801909 |      -0.279995 |
| QQQ     | buy_and_hold | 2014-11-07 | 2026-10-05 | 0.192043  | 0.917794 |      -0.3512   |
| BTC_USD | 10/10        | 2014-11-07 | 2026-10-05 | 0.551352  | 1.17159  |      -0.675729 |
| BTC_USD | buy_and_hold | 2014-11-07 | 2026-10-05 | 0.58687   | 1.03159  |      -0.83399  |

## Maximum drawdown episodes

| peak_date   | trough_date   | recovery_date   |      peak_equity |    trough_equity |   max_drawdown |   peak_to_trough_calendar_days |   underwater_calendar_days | asset   |   pre_span |   post_span |   overlapping_trades |
|:------------|:--------------|:----------------|-----------------:|-----------------:|---------------:|-------------------------------:|---------------------------:|:--------|-----------:|------------:|---------------------:|
| 1999-07-16  | 2009-03-20    | 2011-02-01      | 182268           | 121320           |      -0.334386 |                           3535 |                       4218 | SPY     |         10 |          10 |                   62 |
| 1999-07-16  | 2003-03-31    | 2010-01-07      | 237626           | 155146           |      -0.3471   |                           1354 |                       3828 | SPY     |         18 |          20 |                   15 |
| 1999-07-16  | 2003-03-31    | 2010-01-07      | 237626           | 155146           |      -0.3471   |                           1354 |                       3828 | SPY     |         20 |          18 |                   15 |
| 2000-03-27  | 2002-09-04    | 2017-06-08      | 169655           |  82868.5         |      -0.511547 |                            891 |                       6282 | QQQ     |         10 |          10 |                   14 |
| 2000-03-27  | 2003-03-31    | 2011-01-14      | 182362           | 100687           |      -0.447872 |                           1099 |                       3945 | QQQ     |         10 |          14 |                   16 |
| 2000-03-27  | 2003-03-31    | 2011-01-14      | 182362           | 100687           |      -0.447872 |                           1099 |                       3945 | QQQ     |         14 |          10 |                   16 |
| 2017-12-16  | 2019-02-14    | 2019-06-26      |      3.06077e+06 | 992519           |      -0.675729 |                            425 |                        557 | BTC_USD |         10 |          10 |                   11 |
| 2017-12-16  | 2019-01-14    | 2019-05-26      |      3.49816e+06 |      1.47706e+06 |      -0.577761 |                            394 |                        526 | BTC_USD |         17 |          17 |                    7 |

A portfolio drawdown is measured from its prior equity high, potentially across many trades. It is not a single-trade stop distance.
SPY 18/20: worst completed trade -8.58%; maximum losing streak 9.0 trades.
SPY 10/10: worst completed trade -9.46%; maximum losing streak 7.0 trades.
SHA color is a delayed transformation and is not a fixed stop. Red triggers only a next-open sale; gaps and repeated losing re-entries remain possible.
For SPY 10/10 the worst drawdown spans 1999-07-16 to 2009-03-20; worst completed trade is materially smaller than that drawdown.

## Complete per-pair outputs

Each asset folder under `outputs/smoothed_heikin_ashi/cross_market/` includes all 400 rows, 13 numeric matrices,
trade ledgers, daily equity/exposure and six-panel maps. Per-pair columns include mean/median duration (sessions and calendar days),
win rate, mean trade/winner/loser returns, worst/best trade, dollar profit factor, exposure and completed/open counts.
Maximum losing streak counts consecutive strictly negative completed trades; break-even trades reset the run.
Profit factor uses dollar P&L; absolute trade sizes vary with accumulated capital. No-loss cases are undefined (missing), not invented ratios.
Open trades are marked to last close and excluded from completed-trade statistics. No final forced-liquidation charge is applied.

## Data and inference limits

QQQ has one 2:1 split on 2000-03-20; Yahoo's OHLC is already split-adjusted, so no extra unit doubling is applied.
Corporate-action flags, split-day continuity, complete expected calendars, finite OHLC and source hashes are checked.
Dividend credit on ex-date approximates payable-date timing. BTC uses UTC daily bars; ETFs use exchange sessions.
Same calendar dates do not mean identical observation counts or simultaneous closing timestamps.
Costs are controlled assumptions, not verified broker-specific quotes. PyneSys parity remains unverified.
Grid maxima and neighbor patterns are selected from inspected history and do not establish independent OOS alpha.

```powershell
.venv/Scripts/python.exe run/sha_fetch_cross_market.py
.venv/Scripts/python.exe run/sha_cross_market.py
```
