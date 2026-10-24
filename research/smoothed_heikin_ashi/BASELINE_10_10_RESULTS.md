# SPY SHA EMA(10,10): first historical backtest

Exploratory single configuration. No optimization, grid or independent out-of-sample validation.

Source: 1993-01-29 through 2026-10-05 (8,478 sessions).
Initial cash anchor: 1993-04-13; first execution session: 1993-04-14.
USD 100,000; 10 bps commission + 5 bps adverse slippage per side; zero cash interest.

## Results

Returns, CAGR, drawdown, exposure and win rate below are decimal fractions (0.01 = 1%).
Fees and slippage costs are cumulative USD cash amounts, not percentage-point performance attribution.
|                              |      sha_10_10 |    buy_and_hold |
|:-----------------------------|---------------:|----------------:|
| initial_equity               | 100000         | 100000          |
| final_equity                 | 390321         |      3.1178e+06 |
| total_return                 |      2.90321   |     30.178      |
| cagr                         |      0.0415155 |      0.108208   |
| sharpe_252                   |      0.42226   |      0.647227   |
| max_drawdown                 |     -0.334386  |     -0.552097   |
| exposure_fraction            |      0.648629  |      1          |
| fills                        |    485         |    136          |
| completed_trades             |    201         |      0          |
| open_trades                  |      1         |      1          |
| win_rate                     |      0.39801   |    nan          |
| median_holding_sessions      |     19         |    nan          |
| median_holding_calendar_days |     27         |    nan          |
| holding_sessions_p10         |      4         |    nan          |
| holding_sessions_p90         |     65         |    nan          |
| commissions                  |  74541.7       |    480.729      |
| slippage_cost                |  37270.9       |    240.244      |
| dividend_cash                |  69395.9       | 381210          |

## Interpretation and accounting

SHA CAGR is 4.15%, versus 10.82% for buy-and-hold.
Maximum drawdowns are -33.44% and -55.21%, respectively.
Median completed holding period is 19 sessions / 27 calendar days.
The baseline sacrifices substantial return for lower drawdown; its historical Sharpe is also lower.

Signals use completed daily SHA on real split-adjusted OHLC. Green means fully invested, red cash;
neutral retains target. Orders execute on the next real open. No shorts, stops or leverage.
Dividend cash is credited on ex-date to previous-close holders and reinvested at that open
if remaining long. This approximates actual payable-date timing. Reinvestment incurs costs.
Both strategies use the same dates, capital and dividend/cost assumptions.
CAGR uses elapsed calendar years (365.25 days); Sharpe uses 252 sessions, sample standard deviation
and zero risk-free rate. Drawdown is measured at closes, not intraday. Exposure is the fraction
of evaluation closes invested; it does not measure overnight holdings precisely on exit days.
Completed-trade durations exclude the separately marked open trade. Terminal holdings are
valued at the final close, without a hypothetical liquidation charge.

## Limits

SPY is an ETF proxy for S&P 500. Results use an existing vendor snapshot ending 2026-10-05;
the source was not refreshed. No independent OOS, statistical alpha test or parameter selection
has been conducted. EMA(10,10) numerical parity against the original PyneSys script is unverified.
A single market and full-period statistics do not demonstrate robustness or a live-ready strategy.

## Reproduce

```powershell
.venv/Scripts/python.exe run/sha_backtest.py
```

Generated ledgers, fills, trades, metrics and manifest:
`outputs/smoothed_heikin_ashi/baseline_ema10_10/` (ignored by Git).
Source SHA256: `d53d88560bb710b5a27dc0052a401166132682148ee78550ec3262018fb5872f`.
