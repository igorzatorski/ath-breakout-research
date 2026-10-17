# ATH31: why historical and contemporary results differ

Primary practical focus is2018 through2026-06-30, with2023 onward as a short recent sensitivity. Earlier periods are context, not evidence that a current edge exists. This diagnosis reads frozen ATH30 outputs; it introduces no strategy, parameter, entry filter, exclusion or new holdout. Known recent history remains development data.

## What is established

There are two separate evidence layers: the earlier fixed252-session signal study and the actual capital-constrained portfolio. Their arithmetic event means and calendar CAGRs must not be mixed.

The saved ATH13 event study reports early1994-2009 stock mean21.57%, matching-window SPY4.46%, excess17.11 pp; recent2018-complete2025 signals stock11.34%, SPY13.58%, excess-2.23 pp. The19.34 pp excess decline reconciles to10.23 pp lower stock mean and9.12 pp stronger SPY (rounding applies). Under the fixed company nonoverlap sensitivity, stock means14.92% versus14.19% barely change and SPY explains most of the difference. Repeated-signal weighting therefore matters. These are inherited documented ATH13 results, not freshly recomputed event estimates here.

The same earlier study reports1998/1999 cohorts contribute14.65 pp of the early17.11 pp net excess mean. Events beating SPY by more than200 pp fall from4.24% of early events to0.86% recently. This explains much of the arithmetic concentration pattern, not a causal market mechanism. ATH13 uncertainty does not establish structural decay, crowding, sector causation or statistical superiority.

## Portfolio growth and exposure comparison

For each saved day create a zero-cost synthetic series r_proxy,t = previous-close strategy exposure * SPY total return,t. Cash earns0%. Apply the actual previous-day exposure path before restricting calendar subperiods. This controls approximately for the pattern of stock/cash exposure, including timing, rather than just average invested capital. It omits intraday entry/exit exposure, rebalancing/impact costs and security differences; it is not an executable backtest or risk-matched/factor-adjusted alpha.

The arithmetic identity between CAGRs is exact: strategy minus SPY = proxy minus SPY + strategy minus proxy. Its terms are comparisons to a synthetic reference, not independent economic causes or a unique attribution.

| Period | Rule | Weights | Portfolio CAGR | SPY CAGR | Exposure-path SPY proxy | Mean invested |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 2010_2017 | floor5_sma200 | drift | 15.41% | 13.84% | 11.16% | 93.51% |
| 2018_end | floor5_sma200 | drift | 8.40% | 14.67% | 11.03% | 91.14% |
| 2021_2022 | floor5_sma200 | drift | -17.04% | 2.64% | -2.04% | 87.84% |
| 2023_end | floor5_sma200 | drift | 20.22% | 22.83% | 19.42% | 93.69% |
| 2010_2017 | floor5_sma200 | monthly_equal | 14.07% | 13.84% | 10.74% | 92.40% |
| 2018_end | floor5_sma200 | monthly_equal | 6.14% | 14.67% | 10.79% | 90.82% |
| 2021_2022 | floor5_sma200 | monthly_equal | -20.49% | 2.64% | -3.24% | 86.39% |
| 2023_end | floor5_sma200 | monthly_equal | 16.12% | 22.83% | 18.91% | 92.87% |
| 2010_2017 | sma200 | drift | 18.00% | 13.84% | 12.30% | 97.40% |
| 2018_end | sma200 | drift | 8.15% | 14.67% | 12.30% | 95.58% |
| 2021_2022 | sma200 | drift | -13.63% | 2.64% | 1.22% | 96.00% |
| 2023_end | sma200 | drift | 20.53% | 22.83% | 20.77% | 96.15% |
| 2010_2017 | sma200 | monthly_equal | 16.14% | 13.84% | 12.37% | 97.77% |
| 2018_end | sma200 | monthly_equal | 7.15% | 14.67% | 12.52% | 96.42% |
| 2021_2022 | sma200 | monthly_equal | -15.30% | 2.64% | 0.93% | 97.05% |
| 2023_end | sma200 | monthly_equal | 15.37% | 22.83% | 21.00% | 97.31% |

Since2018, SMA200 drift returns8.15% versus14.67% SPY and12.30% synthetic exposure-path SPY. Cash/exposure timing therefore does not explain the entire underperformance. The fixed-floor candidate drift returns8.40% versus11.03% proxy, also below its proxy. Since2023, SMA200 drift20.53% is close to20.77% proxy, while the floor candidate20.22% exceeds19.42% proxy. Their remaining gap versus full SPY is much smaller than in the broader modern period. This changes interpretation by period without establishing alpha.

## The2021-2022 interruption

In the actual calendar portfolio, SMA200 drift annualized-13.63% and floor+SMA200 drift-17.04%, while SPY annualized+2.64%. These are two-year calendar CAGRs, not the annual forward outcomes of2021 signals. The source portfolios therefore lost money in names/weights/exits that behaved much worse than broad SPY over this interval. Even same-exposure proxies are much better (+1.22% and-2.04%). This is a measurable episode, not proof that a particular sector, economic shock or market microstructure caused it.

The saved2021_2022_security_pnl.csv reconciles every security contribution to start-to-end portfolio wealth change using ending marked value minus starting value plus intervening trade/dividend cashflows. Labels use only source transactions through2022-end. No future classifications or winner deletion. Nominal dollar contributions are path/capital-weighted and not comparable across strategies as independent stock effects.

## Interpretation and research priorities

The supported explanation is a combination: old average signal results depended strongly on rare extreme winners and repeat weighting; contemporary SPY is a stronger comparison; and the capital-constrained strategy suffered a large2021-2022 loss episode. Execution rules, exposure and weighting change the observed portfolio result, with longer SMA200 avoiding some SMA50 truncation but not fixing the broader modern shortfall.

Economic causes such as more efficient breakout pricing, strategy crowding, sector composition, benchmark concentration or valuation changes remain unestablished. Do not narrate them as findings without an explicitly defined comparison and appropriate historical data.

Use2018 onward as the principal diagnostic window and2023 onward as a short sensitivity; retain2010-2017 and older history for robustness and context. Do not delete2021/2022 or keep only a favorable recent start date. Before new parameters, compare modern signal opportunity quality, current-portfolio concentration/exposure and risk-factor returns under frozen definitions. Longer history can test robustness; it cannot rescue absent modern performance.

## Verification and files

Run: `outputs/research/ath/ath_31_recent_history_diagnostic_v001/20261017T173830834133Z`. Hash-checked24 source files from eight net variants,40 exposure/period rows,72 annual observations and eight exact2021-2022 security-PnL reconciliations. Every CAGR uses geometric daily compounding and252-session annualization; annual chart rows use unannualized calendar total returns, with2026 explicitly first-half only. Source ATH30 is unchanged.
