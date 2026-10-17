# ATH40: early SMA stages x opening cap and crash cash behavior

Four fixed configurations on identical ATH + market6-1/top20 candidates and MV priority: constantSMA150 baseline, early+25/+50% stages, opening-only0.5 priorATR cap and both. CleanUSD100,000 cash start2008-01-02 to2026-06-30, next-opening fills,20 companies,5% entry target,10bps per side and zero cash yield. Drift and monthly equal policies. No explicit market/cash regime overlay, consolidation cutoff or initial percentage floor.

## Full-period net CAGR and drawdown

| Configuration | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |
|---|---:|---:|---:|---:|
| base | 8.70% | 8.48% | -45.28% | -44.49% |
| steps | 11.22% | 9.96% | -39.44% | -40.02% |
| gap | 10.37% | 9.97% | -42.72% | -42.75% |
| combined | 10.53% | 10.71% | -42.23% | -45.23% |
| SPY | 11.24% | 11.24% | -52.45% | -52.45% |

The combination does not dominate: drift10.53% trails stages-only11.22%; monthly10.71% exceeds either component but still trailsSPY. Full drawdowns worsen versus stages-only. All fixed contrasts are retained; arithmetic differences of CAGRs are descriptive portfolio-path interactions, not causal additive effects or significance tests.

## Contemporary calendar slices

| Configuration | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |
|---|---:|---:|---:|---:|
| base | 6.89% | 6.55% | 8.53% | 5.48% |
| steps | 10.09% | 7.21% | 16.39% | 9.62% |
| gap | 9.76% | 9.77% | 13.21% | 10.67% |
| combined | 6.82% | 6.23% | 9.41% | 6.62% |
| SPY | 14.67% | 14.67% | 22.83% | 22.83% |

Contemporary slices retain positions from2008; no fresh-start or untouched validation claim. The combination is weaker than either component in both contemporary slices and both policies.

## What happens during declines?

Principal diagnostic below uses the previously strongest full-period candidate: early +25/+50% stages with drift weights. The fixed crash windows are2008-01-02..2009-06-30, 2020-01-02..2020-12-31 and2022-01-03..2022-12-30. These choices were declared before the new results. All four configurations and both policies have chart/data exports.

| Window | Strategy local max drawdown | SPY local max drawdown | Cash at SPY trough | SPY trough date |
|---|---:|---:|---:|---|
| 2008_2009 | -34.61% | -52.45% | 94.62% | 2009-03-09 |
| 2020 | -20.62% | -33.72% | 78.92% | 2020-03-23 |
| 2022 | -27.92% | -24.50% | 23.16% | 2022-10-12 |

Local drawdown uses each series' own running peak inside the fixed window, seeded by prior-close capital (initial cash at the2008 boundary). It is not necessarily the return between the same peak/trough dates. The CSV separately retains matched SPY peak-to-trough strategy returns and full since2008 drawdown. Cash is measured at the same mechanically selected SPY trough date for every strategy.

The system partly creates the desired cash-allocation effect. In2020 the principal candidate moves from almost fully invested near the benchmark peak to78.92% cash at the benchmark trough, then reinvests during the rebound. Protection is reactive: from the SPY peak to its trough it still loses18.74%, versusSPY33.72%.

In2022 that mechanism is not reliable crash avoidance: local strategy drawdown27.92% exceedsSPY24.50%; only23.16% cash remains at the benchmark trough, after earlier cash spikes and renewed investment. Individual security exits do not prohibit fresh entries elsewhere. A stock's SMA and a market-wide allocation rule are different decisions.

The2008 result starts from cash after the2007 market peak. It must not be presented as evidence of having exited a fully invested2007 portfolio before the crash. No counterfactual all-invested or SPY-SMA overlay was simulated.

## Reading and reproducing the charts

PNG/PDF overview: `crash_charts/crash_overview_steps_drift`. Six detailed PNG/PDF and offline interactive Plotly HTML figures retain all four configurations plusSPY. The first panel rebases each series to100 at the first window close; it does not show the first-day opening-to-close loss. Drawdown panels retain running high-water marks since2008; cash panels show daily cash/NAV. Thus the detailed drawdown panel can differ from local-window drawdown in the table. All reviewed chart rows and sources are saved. Interactive figures allow export toPNG.

Run `chart_ath_crashes.py RUN` and `render_ath_crash_png.py RUN`. Static exports use the optional `research-plots` dependency; Plotly is already a project dependency. Overview and detailed PNG layouts were visually checked, including a contact sheet covering all six detailed figures.

## Verification and scope

All150 control summary rows and27912 daily equity rows reproduce ATH35/36/37 exactly for NAV, cash and exposure. All eight independent ledger/eligibility/stage replays passed;23 focused tests passed. All24,668 plotted points and24 crash metric rows independently reconcile to equity.csv. Frozen source panel, SMA and priorATR inputs retain their source hashes and prior raw audits. Final code/artifact hashes and receipt paths are in manifest.json.

Inspected history remains development evidence. No optimum, new confidence interval, risk-adjusted alpha, live execution guarantee or market-timing overlay is established. Opening-only fills, zero cash yield, stock selection and delayed SMA execution remain material assumptions.

Run: `outputs\backtests\ath_40_steps_gap_factorial_v001\20261017T200912951276Z`. Protocol: `ATH_STEPS_GAP_FACTORIAL_PLAN.md`.
