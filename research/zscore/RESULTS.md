# SPY Z-score research v001

See PLAN.md for frozen methodology.

The 30-session signal has a modest positive historical mean-return association, not a material win-rate improvement. Its 95% block-bootstrap excess interval is above zero in this sample (uncorrected for testing two windows); the 60-session interval includes zero. These are exploratory findings, not independently validated alpha. The 30-session non-overlapping sample averages 0.393% gross and 0.193% after an illustrative 20bps round trip, with a 57.7% win rate and a -19.6% worst holding window. The adverse tail is worse than the unconditional sample. No live trading or leverage conclusion follows. A 60-session bootstrap block was added after the first result as an explicitly post-result dependence sensitivity; it leaves the qualitative conclusion unchanged.

Source: local Yahoo SPY, 1993-01-29 to 2026-10-05; 8414 complete common signal dates.

|   window | period    | sample        |    n |    mean |   median |   win_rate |      p05 |     p95 |    worst |   mean_less_20bps |   mean_price_return |
|---------:|:----------|:--------------|-----:|--------:|---------:|-----------:|---------:|--------:|---------:|------------------:|--------------------:|
|       30 | full      | unconditional | 8414 | 0.00194 |  0.00341 |    0.57975 | -0.03525 | 0.03496 | -0.19635 |          -0.00006 |             0.00166 |
|       30 | full      | all_signals   | 1524 | 0.00449 |  0.00574 |    0.58530 | -0.04660 | 0.05219 | -0.19635 |           0.00249 |             0.00421 |
|       30 | full      | nonoverlap    |  440 | 0.00393 |  0.00557 |    0.57727 | -0.04232 | 0.05115 | -0.19635 |           0.00193 |             0.00368 |
|       30 | 1993-2009 | unconditional | 4205 | 0.00138 |  0.00233 |    0.55386 | -0.03772 | 0.03646 | -0.19635 |          -0.00062 |             0.00109 |
|       30 | 1993-2009 | all_signals   |  826 | 0.00331 |  0.00351 |    0.54843 | -0.05074 | 0.05590 | -0.19635 |           0.00131 |             0.00309 |
|       30 | 1993-2009 | nonoverlap    |  240 | 0.00376 |  0.00384 |    0.54583 | -0.04133 | 0.06039 | -0.19635 |           0.00176 |             0.00353 |
|       30 | 2010-2017 | unconditional | 2013 | 0.00247 |  0.00357 |    0.60954 | -0.02945 | 0.02935 | -0.12166 |           0.00047 |             0.00215 |
|       30 | 2010-2017 | all_signals   |  328 | 0.00682 |  0.00820 |    0.65549 | -0.03382 | 0.04782 | -0.12166 |           0.00482 |             0.00652 |
|       30 | 2010-2017 | nonoverlap    |   93 | 0.00514 |  0.00902 |    0.66667 | -0.03455 | 0.03953 | -0.12166 |           0.00314 |             0.00492 |
|       30 | 2018-end  | unconditional | 2196 | 0.00254 |  0.00488 |    0.60200 | -0.03402 | 0.03624 | -0.15736 |           0.00054 |             0.00230 |
|       30 | 2018-end  | all_signals   |  370 | 0.00503 |  0.00818 |    0.60541 | -0.04773 | 0.05007 | -0.15736 |           0.00303 |             0.00469 |
|       30 | 2018-end  | nonoverlap    |  107 | 0.00325 |  0.00695 |    0.57009 | -0.04990 | 0.04574 | -0.15736 |           0.00125 |             0.00295 |
|       60 | full      | unconditional | 8414 | 0.00194 |  0.00341 |    0.57975 | -0.03525 | 0.03496 | -0.19635 |          -0.00006 |             0.00166 |
|       60 | full      | all_signals   | 1308 | 0.00344 |  0.00481 |    0.55428 | -0.05636 | 0.05871 | -0.19635 |           0.00144 |             0.00318 |
|       60 | full      | nonoverlap    |  342 | 0.00294 |  0.00445 |    0.54971 | -0.05641 | 0.05258 | -0.13427 |           0.00094 |             0.00264 |
|       60 | 1993-2009 | unconditional | 4205 | 0.00138 |  0.00233 |    0.55386 | -0.03772 | 0.03646 | -0.19635 |          -0.00062 |             0.00109 |
|       60 | 1993-2009 | all_signals   |  760 | 0.00177 |  0.00300 |    0.52632 | -0.05932 | 0.06135 | -0.19635 |          -0.00023 |             0.00154 |
|       60 | 1993-2009 | nonoverlap    |  199 | 0.00149 |  0.00207 |    0.51759 | -0.05788 | 0.05271 | -0.13427 |          -0.00051 |             0.00118 |
|       60 | 2010-2017 | unconditional | 2013 | 0.00247 |  0.00357 |    0.60954 | -0.02945 | 0.02935 | -0.12166 |           0.00047 |             0.00215 |
|       60 | 2010-2017 | all_signals   |  240 | 0.00740 |  0.01033 |    0.63333 | -0.03818 | 0.05265 | -0.12166 |           0.00540 |             0.00713 |
|       60 | 2010-2017 | nonoverlap    |   66 | 0.00409 |  0.01302 |    0.60606 | -0.04499 | 0.04071 | -0.12166 |           0.00209 |             0.00379 |
|       60 | 2018-end  | unconditional | 2196 | 0.00254 |  0.00488 |    0.60200 | -0.03402 | 0.03624 | -0.15736 |           0.00054 |             0.00230 |
|       60 | 2018-end  | all_signals   |  308 | 0.00448 |  0.00671 |    0.56169 | -0.05850 | 0.05994 | -0.15736 |           0.00248 |             0.00415 |
|       60 | 2018-end  | nonoverlap    |   77 | 0.00569 |  0.01013 |    0.58442 | -0.05803 | 0.05667 | -0.09939 |           0.00369 |             0.00541 |

## Block bootstrap (all signal days)

{
  "30": {
    "mean_ci": [
      0.0015258821139314202,
      0.007021219377067713
    ],
    "excess_ci": [
      0.00016502867554255615,
      0.0047115811089833756
    ],
    "block60_sensitivity": {
      "mean_ci": [
        0.0019712615516912294,
        0.007026699144879438
      ],
      "excess_ci": [
        0.00038876058226929093,
        0.004647081270232434
      ]
    }
  },
  "60": {
    "mean_ci": [
      1.8336684424372248e-05,
      0.0066492955437435775
    ],
    "excess_ci": [
      -0.0014610612213146734,
      0.00424666900810837
    ],
    "block60_sensitivity": {
      "mean_ci": [
        0.00019015689134558323,
        0.006611561328400624
      ],
      "excess_ci": [
        -0.001272310236828009,
        0.004233001641010904
      ]
    }
  }
}

All returns are decimal, unlevered, before financing and execution costs except the explicitly labeled 20bps sensitivity. Non-overlap is a separate event sample, not a full portfolio backtest. Dividend-adjusted open is a proxy. No inference about stops, futures rolls, CFD financing, margin liquidation or leverage is supported. Historical splits are inspected diagnostics, not independent out-of-sample validation. Neither window was selected as a winner.
