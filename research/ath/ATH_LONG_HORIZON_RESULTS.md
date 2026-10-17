# Two and three years after ATH

Study: `ath_07_long_horizons_v001`; run `20261015T222739157747Z`.
Protocol: [ATH_LONG_HORIZON_PLAN.md](ATH_LONG_HORIZON_PLAN.md).
Descriptive extension after shorter results were inspected. The original
21-session primary hypothesis has not been replaced by a selected optimum.

## Fair comparison: exactly the same events at each horizon

65,434 stock/SPY-valid events across 2,563 securities have every horizon from
5 to 756 sessions. Last complete 3-year signal: 2023-06-23; observations end
2026-06-30. Same frozen entries, quality rules and original control IDs.

| Holding sessions | Approximate length | Mean cumulative ATH total return | Same-window SPY | Excess |
| --- | --- | ---: | ---: | ---: |
| 252 | 1 year | +12.71% | +9.31% | +3.40 pp |
| 504 | 2 years | +19.87% | +18.65% | +1.22 pp |
| 756 | 3 years | +29.86% | +31.46% | -1.59 pp |

These are gross arithmetic cumulative EVENT returns, not yearly rates or
portfolio CAGR. The 1-year row differs from the earlier +12.64%/+10.09%
available-sample result because this table uses only signals with three full
years of data. Do not mix populations when comparing horizons.

Positive cumulative returns over longer periods do not imply increasing
predictive excess from the signal. The 3-year stock mean is below SPY in this
sample. Uncertainty includes both positive and negative excess.

## Available-sample figures and periods

| Horizon | Valid stock/SPY events | Mean ATH | Mean SPY | Excess |
| --- | ---: | ---: | ---: | ---: |
| 504 sessions | 68,692 | +20.29% | +19.64% | +0.64 pp |
| 756 sessions | 65,434 | +29.86% | +31.46% | -1.59 pp |

Latest valid 2-year signal: 2024-06-25. Later windows are censored rather than
silently shortened or filled. 2-year: 6,475 censored, 542 invalid paths, 175
missing entries. 3-year: 9,327 censored, 950 invalid paths, 173 missing entries.
Existing history-quality exclusions and future-availability attrition remain.

| Signal period | 2-year excess SPY | 3-year excess SPY |
| --- | ---: | ---: |
| 1994-2009 | +8.25 pp | +8.79 pp |
| 2010-2017 | -0.42 pp | -1.86 pp |
| 2018 through each horizon's last complete signal | -7.40 pp | -15.54 pp |

Most recent complete 3-year cohort: ATH +27.25% versus SPY +42.78%.
These are predefined stability periods of known history, not untouched OOS.

## Positive endpoint is not a smooth uptrend

Each event's closing-total-return wealth includes reinvested distributions and
terminal return once, then cash at zero interest. Drawdown is relative to that
event's previous closing wealth peak, including initial investment 1. SPY uses
the same entry and holding dates. These are event-path risk metrics, not a
portfolio drawdown or intraday stop simulation.

| Path statistic | 2-year | 3-year |
| --- | ---: | ---: |
| Median maximum stock closing drawdown | -40.64% | -48.62% |
| Median maximum SPY closing drawdown | -19.03% | -24.50% |
| Fraction of stock events with >=50% closing drawdown | 36.56% | 47.53% |
| Median worst closing loss relative to entry | -24.41% | -30.54% |
| Fraction ending below entry wealth | 41.55% | 40.20% |
| Median cumulative stock outcome | +9.48% | +13.28% |

This does not establish or reject every definition of trend persistence. It
shows that holding a positive eventual winner may involve substantial interim
risk, and that the mean stock result is influenced by a positive tail.

## Uncertainty and fixed sensitivities

2,000 circular signal-date bootstrap draws, seed 20261015. 756-session blocks:

- 2-year SPY excess: +0.64 pp; 95% interval -5.69 to +7.98 pp.
- 3-year SPY excess: -1.59 pp; interval -11.84 to +9.03 pp.

1512-session blocks also include zero. Very long overlapping windows and few
effective long blocks limit inference; firm persistence is not fully clustered.

Original fixed matched controls: 63,222 complete 2-year comparisons, mean ATH
+20.77% versus controls +17.83%, excess +2.94 pp. Three-year: 58,666 comparisons,
ATH +30.96% versus controls +29.18%, excess +1.78 pp. Both long-block intervals
include zero. These paired populations differ from the full SPY populations.
Controls do not match earlier momentum, sector or all risk factors.

Previously frozen 21-session repeat suppression, without tuning: 2-year excess
SPY +0.52 pp; 3-year -1.87 pp. Both intervals include zero. Equal-security mean
SPY excess is strongly negative in the main sample (-30.36 pp at 2 years,
-38.45 pp at 3 years); weights answer different sampling questions and are not
executable equal-weight portfolio results.

Terminal proceeds remain zero-interest cash to the horizon (6,841 stock/SPY
2-year events and 9,238 3-year events). No successor holding, settlement-timing,
new entry or freed-capital reinvestment model was introduced.

## Decision and verification

Longer holding alone does not produce a demonstrated, increasing SPY premium
in this selected population. Do not infer a reliable multi-year uptrend from
the ATH signal alone, choose an optimum from these horizons, or extrapolate to
five years. Later feature studies remain separate hypotheses.

Three new path tests and ten related path/annual/vector-engine tests passed;
Ruff passed. 299 scalar/vector return checks passed. All 134,126 valid long
closing-path endpoints agree with the event-return engine. Source/artifact
hashes, dates, horizon identity, data-cutoff and drawdown bounds checked.
No visual chart QA or new WRDS connection.

Run: `.venv/Scripts/python.exe scripts/research/extend_ath_long_horizons.py`.
Artifacts: `outputs/research/ath/ath_07_long_horizons_v001/20261015T222739157747Z/`.
Includes long returns/path summaries, common seven-horizon comparison, coverage,
periods, long-block uncertainty and SHA256 provenance. Earlier outputs preserved;
changes remain local and uncommitted.
