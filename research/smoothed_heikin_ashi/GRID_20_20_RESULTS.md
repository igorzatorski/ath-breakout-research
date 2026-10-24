# SPY SHA EMA: 20 x 20 grid

Exploratory full-history sensitivity; not independent out-of-sample validation.

400 pairs: EMA before HA 1..20 x EMA after HA 1..20. Evaluation: 1993-04-14 to 2026-10-05.
Signal initialization and 50-bar warm-up unchanged. Real next-open fills; fractional shares; long/cash; neutral retains target.
USD 100,000; commission 10 bps + slippage 5 bps per side including reinvestment; cash yield 0%.
Dividend entitlement, ex-date credit approximation and final-close valuation follow the baseline plan.

## Grid summary

Positive CAGR: 333/400. Higher CAGR than buy-and-hold: 0/400.
Higher Sharpe than buy-and-hold: 0/400.
CAGR range -7.63% to 5.99%; median 3.38%.
Sharpe range -0.621 to 0.566; median 0.354.
Buy-and-hold: CAGR 10.82%, Sharpe 0.647, max drawdown -55.21%.

## Top 10 by full-sample CAGR

CAGR and drawdown are decimal fractions; e.g. 0.05 = 5%.

|   pre_span |   post_span |      cagr |   sharpe_252 |   max_drawdown |   completed_trades |   median_holding_calendar_days |   neighbor_mean_sharpe |   neighbor_worst_sharpe |
|-----------:|------------:|----------:|-------------:|---------------:|-------------------:|-------------------------------:|-----------------------:|------------------------:|
|         18 |          20 | 0.0598584 |     0.566244 |      -0.3471   |                110 |                           55.5 |               0.541144 |                0.512787 |
|         20 |          18 | 0.0598584 |     0.566244 |      -0.3471   |                110 |                           55.5 |               0.541144 |                0.512787 |
|         19 |          19 | 0.0589688 |     0.558839 |      -0.3471   |                110 |                           55.5 |               0.549762 |                0.516996 |
|         19 |          20 | 0.0584971 |     0.554651 |      -0.360435 |                109 |                           55   |               0.555397 |                0.542056 |
|         20 |          19 | 0.0584971 |     0.554651 |      -0.360435 |                109 |                           55   |               0.555397 |                0.542056 |
|         20 |          20 | 0.058482  |     0.555196 |      -0.335308 |                108 |                           55   |               0.556047 |                0.554651 |
|         18 |          19 | 0.0569601 |     0.542056 |      -0.361823 |                111 |                           55   |               0.53784  |                0.512787 |
|         19 |          18 | 0.0569601 |     0.542056 |      -0.361823 |                111 |                           55   |               0.53784  |                0.512787 |
|         17 |          20 | 0.0564061 |     0.537386 |      -0.365696 |                111 |                           55   |               0.529704 |                0.511719 |
|         20 |          17 | 0.0564061 |     0.537386 |      -0.365696 |                111 |                           55   |               0.529704 |                0.511719 |

## Top 10 by full-sample Sharpe

|   pre_span |   post_span |      cagr |   sharpe_252 |   max_drawdown |   completed_trades |   median_holding_calendar_days |   neighbor_mean_sharpe |   neighbor_worst_sharpe |
|-----------:|------------:|----------:|-------------:|---------------:|-------------------:|-------------------------------:|-----------------------:|------------------------:|
|         18 |          20 | 0.0598584 |     0.566244 |      -0.3471   |                110 |                           55.5 |               0.541144 |                0.512787 |
|         20 |          18 | 0.0598584 |     0.566244 |      -0.3471   |                110 |                           55.5 |               0.541144 |                0.512787 |
|         19 |          19 | 0.0589688 |     0.558839 |      -0.3471   |                110 |                           55.5 |               0.549762 |                0.516996 |
|         20 |          20 | 0.058482  |     0.555196 |      -0.335308 |                108 |                           55   |               0.556047 |                0.554651 |
|         19 |          20 | 0.0584971 |     0.554651 |      -0.360435 |                109 |                           55   |               0.555397 |                0.542056 |
|         20 |          19 | 0.0584971 |     0.554651 |      -0.360435 |                109 |                           55   |               0.555397 |                0.542056 |
|         18 |          19 | 0.0569601 |     0.542056 |      -0.361823 |                111 |                           55   |               0.53784  |                0.512787 |
|         19 |          18 | 0.0569601 |     0.542056 |      -0.361823 |                111 |                           55   |               0.53784  |                0.512787 |
|         15 |          18 | 0.0562239 |     0.541483 |      -0.314067 |                128 |                           44.5 |               0.505324 |                0.473241 |
|         18 |          15 | 0.0562239 |     0.541483 |      -0.314067 |                128 |                           44.5 |               0.505324 |                0.473241 |

## Reference 10/10

|   pre_span |   post_span |   initial_equity |   final_equity |   total_return |      cagr |   sharpe_252 |   max_drawdown |   exposure_fraction |   fills |   commissions |   slippage_cost |   dividend_cash |   completed_trades |   open_trades |   win_rate |   median_holding_sessions |   median_holding_calendar_days |   holding_sessions_p10 |   holding_sessions_p90 |   neighbor_count |   neighbor_mean_sharpe |   neighbor_worst_sharpe |   cagr_rank |   sharpe_rank |
|-----------:|------------:|-----------------:|---------------:|---------------:|----------:|-------------:|---------------:|--------------------:|--------:|--------------:|----------------:|----------------:|-------------------:|--------------:|-----------:|--------------------------:|-------------------------------:|-----------------------:|-----------------------:|-----------------:|-----------------------:|------------------------:|------------:|--------------:|
|         10 |          10 |           100000 |         390321 |        2.90321 | 0.0415155 |      0.42226 |      -0.334386 |            0.648629 |     485 |       74541.7 |         37270.9 |         69395.9 |                201 |             1 |    0.39801 |                        19 |                             27 |                      4 |                     65 |                8 |               0.406712 |                0.353391 |         144 |           130 |

## Parameter neighborhoods and limits

All 400 parameter pairs generated 213 distinct signal histories on this sample; trials are not independent.
Tied maximum CAGR pairs (absolute tolerance 1e-12): [[18, 20], [20, 18]].
The displayed CAGR leader's immediate neighbors have mean Sharpe 0.541 and minimum Sharpe 0.513.
Neighbor statistics use adjacent pairs in a clipped 3x3 window excluding the center (3 to 8 neighbors).
They describe sensitivity on the same history, not statistical independence or out-of-sample stability.
At a boundary, settings beyond the tested range are unknown. All 400 trials are retained, including losses.
Maxima were selected after seeing all 400 results and are subject to selection bias. No parameter is declared best for future trading.
SPY is an ETF proxy for S&P 500. Source is an existing unrefreshed snapshot; PyneSys numerical parity remains unverified.

## Verification and reproduce

All 400 configurations matched the ledger simulator on synthetic input with costs, dividends and gaps.
Full-history equity/metric reference checks: [(10, 10), (18, 20), (20, 18)]. Existing 10/10 and buy-and-hold results reproduced.
Daily equity, signals, exposure, trades, all metrics, heatmaps and fingerprints:
`outputs/smoothed_heikin_ashi/grid_20_20/` (Git ignored).

```powershell
.venv/Scripts/python.exe run/sha_grid.py
```

Source SHA256: `d53d88560bb710b5a27dc0052a401166132682148ee78550ec3262018fb5872f`.
