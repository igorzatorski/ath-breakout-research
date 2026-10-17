# ATH29: what the SMA50 exits cut

SMA50 truncated both tails in this inspected sample: it prevented many much larger eventual losses, but also sold many stocks that subsequently recovered or became large winners. The remaining execution gap after the sale decision explains only a small share of realized losses. This is a descriptive trade-path study, not a new portfolio backtest or proof of a better exit.

## Scope and comparison

ATH28 signals and portfolio rules are unchanged. Analyze both10bps policies, with drift primary. Every SMA50 sale is decomposed using actual ledger cashflows. For the paired path study, compare one original share-equivalent sold at its actual SMA50 opening then held in cash versus the same unit kept until session252 from entry (entry counts as1). Both pay10bps entry/exit cost; dividends remain cash; terminal CIZ proceeds settle once with no second fee. Endpoint is fixed from entry, not252 days after exit. Results are episode returns, not CAGR.

Primary:3,100 SMA50 exits;2,982 complete paired paths. Exclude103 immature horizons and15 paths with missing observations, with no outcome-based exclusion. Monthly:3,111 exits;2,993 complete pairs, also103 immature and15 missing. No SMA sale occurs at or beyond the252nd session in these saved episodes. The123 terminal exits in each original portfolio and still-open positions are outside this SMA-exit-conditioned cohort. Future terminal events after an SMA sale are retained in hypothetical holding paths,147 in the primary complete cohort.

## Same episodes, same endpoint

| Metric | SMA50 sale then cash | Hold to session252 |
| --- | ---: | ---: |
| Mean return | 1.95% | 17.13% |
| Median return | -3.87% | 7.29% |
| Loss of at least20% | 4.26% | 25.12% |
| Loss of at least50% | 0.10% | 9.39% |
| 5th percentile | -18.98% | -62.29% |
| 95th percentile | 39.79% | 120.76% |

Keeping the unit finishes ahead in58.69% of pairs; mean paired advantage15.18 pp, median7.19 pp. Of1,880 losing standardized sales,924 (49.15%) become positive by the fixed endpoint.

208 episodes finish at least+100% if held; their average sale return is36.86%. Excluding those final doublers reduces the mean hold-minus-sale difference to3.77 pp. This is a hindsight-conditional concentration diagnostic, not a permissible exclusion or signal. A post-sale closing-price maximum at least10% above the fill occurs in78.34%; the maximum cannot be earned without a future-aware exit.

## Mean paired hold-minus-sale difference by entry cohort

| Entry cohort | Drift pairs | Drift difference (pp) | Monthly pairs | Monthly difference (pp) |
| --- | ---: | ---: | ---: | ---: |
| 1994_2009 | 1284 | 16.70 | 1293 | 16.99 |
| 2010_2017 | 842 | 14.52 | 842 | 14.51 |
| 2018_end | 856 | 13.54 | 858 | 13.55 |
| 2023_end | 283 | 17.83 | 285 | 18.21 |

Recent entry cohorts are restricted by annual maturity through2026-06-30. The same company can appear repeatedly and holdings overlap; no independent-observation confidence interval or statistical/causal superiority is claimed. Monthly comparisons are standardized original units and do not reproduce the rebalanced cashflow return.

## Were large losses caused by the final execution gap?

| Policy / loss group | Episodes | Mean realized ratio | Loss already present before execution | Execution movement share of dollar losses | Exit-fee share |
| --- | ---: | ---: | ---: | ---: | ---: |
| drift_10bps / all_losses | 1954 | -9.41% | 97.10% | 1.96% | 0.94% |
| drift_10bps / large_losses_le_minus20pct | 137 | -27.86% | 94.83% | 4.92% | 0.25% |
| monthly_equal_10bps / all_losses | 1931 | -9.12% | 96.96% | 2.08% | 0.96% |
| monthly_equal_10bps / large_losses_le_minus20pct | 126 | -27.31% | 94.95% | 4.80% | 0.25% |

The components reconcile exactly to actual episode PnL, including prior rebalance flows and entitled dividends. Execution movement is decision close to actual fill; deferred fills may span several sessions. Dollar shares are net signed contributions, so favorable movements offset adverse ones. They do not claim every losing trade had an adverse gap.

Large drift losses mean actual episode loss at least20%:137 episodes, average realized ratio-27.86%, with average entry-to-decision price return-26.20%. All-holding gap decomposition has complete prices for136 of137 episodes. Their average additive entry-price contribution is-4.80 pp from all overnight moves and-22.91 pp from intraday moves. 12/136 experienced at least one overnight gap of-20% or worse. These are additive price contributions, not compounded gap-only investment returns, and differ from net cashflow returns.

Thus the final sale gap is not the dominant accounting source of these losses. SMA50 can lie far below a rapidly rising entry price, so a first close below it can already mean a severe entry loss. Earlier overnight gaps also matter in some cases; the analysis does not establish that every loss was slow or avoidable.

## Examples, primary actual large dollar losses

| Ticker at entry | Entry | Sale | Realized return | Entry-to-decision price return | Decision-to-fill movement |
| --- | --- | --- | ---: | ---: | ---: |
| GME | 2021-01-28 | 2021-02-10 | -80.88% | -81.02% | 0.91% |
| QUBT | 2024-12-18 | 2025-01-14 | -62.87% | -66.08% | 9.66% |
| ANVS | 2021-05-24 | 2021-07-30 | -43.47% | -33.23% | -15.17% |
| SOUN | 2024-12-19 | 2025-01-28 | -39.40% | -37.27% | -3.20% |
| INNT | 2018-04-04 | 2018-04-24 | -60.56% | -60.95% | 1.19% |

## Interpretation and next step

The intended asymmetry is not delivered automatically by one moving average. SMA50 gives meaningful left-tail protection versus keeping the selected stocks for a year, while truncating part of the right tail; for some entries it still permits very large losses. Those are three distinct observations, not evidence to abandon all stops or select a longer SMA after seeing results.

A possible next separately frozen hypothesis is to distinguish initial loss control from the rule used to follow an established winner. Do not implement that from this report alone or select thresholds from the largest historical winners. First agree on one simple pair of rules and a fixed portfolio comparator; retain capacity, reinvestment, ranking, costs and exposure controls.

The same-unit comparison holds sale proceeds idle; the actual portfolio may redeploy them, and a hold-to252 portfolio would occupy slots and block other entries. Repeated episodes may overlap in the same company. The measured15.18 pp mean difference cannot be added to portfolio CAGR, interpreted as alpha, or used to claim a buy-and-hold portfolio wins. Equal episode weighting differs from actual capital weights. The paired sample is selected by the original exit rule and is not an independent holdout. Missing-price exclusions may affect comparisons. SPY was not newly retested here: ATH28 remains the portfolio-level benchmark evidence.

## Verification and files

Four focused synthetic tests passed, including ex-date entitlement, terminal-once treatment, invalid paths and all-holding gap versus last-gap decomposition. Actual PnL reconciled for all6,211 SMA exits across the two policies, maximum error below USD0.000001. Primary standardized sale returns match actual drift episode returns to1.4e-15. Independent raw CRSP reconstruction of79 paths, including terminal cases, has zero return discrepancy. All10 aggregate rows were independently checked. Further602,894 distinct regular source-return checks across primary forward paths reconcile adjusted prices/distributions to CIZ within0.000001; no unexplained error. Source hashes verified for38 inputs; Ruff passed.

Run: `outputs/research/ath/ath_29_sma50_exit_diagnostic_v001/20261017T151459193734Z`. Saved event-level paths, both-policy summaries, coverage, quantiles, loss decomposition, top20 losses, independent checks and manifest. Source ATH28 is unchanged. Reproduce with `scripts/research/diagnose_ath_sma50_exits.py`, then `verify_ath_sma50_exit_diagnostic.py RUN` and `report_ath_sma50_exit_diagnostic.py RUN`.
