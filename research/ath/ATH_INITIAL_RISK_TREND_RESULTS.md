# ATH30: original-entry risk floor and longer trend following

The fixed5% entry-floor plus SMA200 candidate improves on SMA50 in both weighting policies, but only slightly exceeds full-history SPY and still underperforms SPY since2018. The attribution controls are informative: extending the trend leg to200 sessions is favorable over the full inspected history; adding the5% floor reduces full-history CAGR at either SMA. No optimal exit or current alpha is established.

## Frozen design

Same25,250 pre-outcome ATH +6-1/top20 signals and MV priority as ATH28,1994-01-03 to2026-06-30,8,177 sessions, USD100,000 initial cash, maximum20 companies,5% entry target. Fresh next-opening signals only. Exits free slots, so actual executed entries and reinvestment change endogenously; source signals and candidate ranking are unchanged.

Candidate: close strictly below95% of the original opening purchase price OR below arithmetic SMA200 including the current close; sell at the next observed opening. The floor stays fixed through monthly rebalances and is price-based, not dividend-adjusted or trailing. Both legs remain active throughout; no profit activation threshold. With missing SMA200 the trend leg is suspended and the floor remains active. No forced signal exclusion. This close-triggered floor is not an intraday stop and cannot cap execution losses at5%.

Exactly four exit definitions were registered before results: SMA50, floor+SMA50, SMA200 and floor+SMA200. Both existing weighting policies at10bps per buy/sell. Candidate-only0bps is a gross reference. No threshold/SMA search. Monthly equal resets held weights to5% without replacing securities; drift retains quantities. Cash yield0%, fractional shares, no leverage/taxes. SPY total-return buy-and-hold receives the same initial entry fee. Holdings remain marked at the end.

## Full-history net results

| Exit | Drift CAGR | Monthly equal CAGR | Drift max drawdown | Monthly max drawdown |
| --- | ---: | ---: | ---: | ---: |
| SMA50 baseline | 7.95% | 8.48% | -70.70% | -69.97% |
| Entry floor5% + SMA50 | 6.42% | 5.43% | -66.63% | -66.73% |
| SMA200 control | 15.63% | 13.61% | -63.77% | -64.78% |
| Entry floor5% + SMA200 candidate | 11.63% | 11.02% | -72.49% | -64.31% |
| SPY | 10.87% | 10.87% | -55.19% | -55.19% |

The candidate exceeds SMA50 by3.67 pp drift /2.54 pp monthly in CAGR, but its SPY gap is only+0.76/+0.15 pp. The candidate drift drawdown is worse than the original SMA50 drawdown; adding a trade-level floor does not guarantee a smaller portfolio drawdown.

Gross candidate CAGR is12.26% drift /11.79% monthly. Net candidate final wealth is approximately USD3.55m /2.97m versus SPY USD2.85m. CAGR annualizes252 sessions and is not a mean episode return.

## Calendar portfolio periods, net

| Period | Weight policy | SMA50 | Floor + SMA50 | SMA200 | Floor + SMA200 | SPY |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1994_2009 | drift | 9.21% | 7.25% | 18.59% | 11.50% | 7.48% |
| 1994_2009 | monthly_equal | 9.41% | 5.85% | 15.91% | 12.16% | 7.48% |
| 2010_2017 | drift | 7.51% | 6.78% | 18.00% | 15.41% | 13.84% |
| 2010_2017 | monthly_equal | 7.56% | 6.47% | 16.14% | 14.07% | 13.84% |
| 2018_end | drift | 6.03% | 4.54% | 8.15% | 8.40% | 14.67% |
| 2018_end | monthly_equal | 7.60% | 3.70% | 7.15% | 6.14% | 14.67% |
| 2018_2020 | drift | 21.97% | 14.84% | 10.80% | 14.91% | 14.01% |
| 2018_2020 | monthly_equal | 23.59% | 17.31% | 15.01% | 15.93% | 14.01% |
| 2021_2022 | drift | -14.99% | -18.87% | -13.63% | -17.04% | 2.64% |
| 2021_2022 | monthly_equal | -12.65% | -16.44% | -15.30% | -20.49% | 2.64% |
| 2023_end | drift | 6.67% | 11.51% | 20.53% | 20.22% | 22.83% |
| 2023_end | monthly_equal | 7.61% | 5.53% | 15.37% | 16.12% | 22.83% |

These are continuing portfolio calendar returns, not restarts and not forward signal-cohort means. All inspected dates are development history. Since2018 the candidate returns8.40%/6.14% against14.67% SPY. Since2023 the candidate returns20.22%/16.12% against22.83% SPY. The unconstrained SMA200 control also lags SPY in both these recent windows.

## Trade risk, exposure and concentration

| Exit / weighting | Mean invested | Largest daily name weight | Closed losing episodes | Mean losing cashflow ratio | Median holding calendar days | Top5 company share of net dollar PnL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SMA50 baseline / drift | 74.95% | 26.00% | 61.15% | -9.35% | 45 | 33.16% |
| SMA50 baseline / monthly_equal | 74.25% | 10.51% | 60.24% | -9.06% | 45 | 30.25% |
| Entry floor5% + SMA50 / drift | 70.06% | 27.48% | 69.55% | -6.68% | 24 | 52.23% |
| Entry floor5% + SMA50 / monthly_equal | 68.83% | 11.16% | 69.33% | -6.64% | 24 | 42.08% |
| SMA200 control / drift | 91.93% | 48.99% | 56.06% | -18.47% | 162 | 45.95% |
| SMA200 control / monthly_equal | 91.97% | 10.13% | 52.52% | -16.34% | 164 | 37.56% |
| Entry floor5% + SMA200 candidate / drift | 84.70% | 43.55% | 78.55% | -7.55% | 22 | 55.65% |
| Entry floor5% + SMA200 candidate / monthly_equal | 82.56% | 9.72% | 76.91% | -7.30% | 21 | 43.04% |

Closed ratios include buys, sales, fees and dividends. Under monthly rebalancing they are cashflow ratios rather than time-weighted stock returns. Ending-open holdings contribute to company PnL but not closed-loss statistics; all values are nominal dollars. A high top-company share is a concentration diagnostic, not a reason to remove those companies after seeing results.

Candidate drift loses on roughly79% of closed episodes, with average loser about-7.55%; a5% close threshold is not a5% realized-loss guarantee. The floor reduces average loser size versus SMA200 alone but sells many more episodes at losses. Candidate drift can allocate over43% of current wealth to one winner despite its5% entry target; SMA200 alone reaches49%. Monthly resets limit these observed maxima to about10%. Full-period SMA200 lead therefore is not a clean equal-risk comparison to SPY.

## What the controls establish and what they do not

At either SMA, the fixed5% floor lowers full-history net CAGR. At either floor setting, SMA200 improves full-history CAGR over SMA50. These are fixed system-level comparisons with different holding durations, exposure, vacancies, costs and executed entries, not an isolated causal stock-level exit treatment. Recent outcomes vary; the floor is not uniformly harmful in every subperiod.

Do not select SMA200 as an optimum from this experiment. Keep it as an exploratory longer-trend reference. A next controlled diagnostic should compare exposure/risk and concentration, then risk-adjusted portfolio returns, before claiming an entry or exit alpha. Current historical recent underperformance and source/missingness limitations remain material. No new filter, portfolio-size or cash-allocation rule was tested.

## Validation and data limitations

Twelve focused tests passed: five new exit/anchor cases plus seven existing ledger regressions. They cover strict equality, next-open gaps, longer-trend holding, fixed anchor after rebalances, floor with missing SMA, combined triggers, terminal-once behavior and same-open sale/reentry. Both SMA50 controls reproduce the saved daily NAV/cash/count/fees/benchmark and every transaction from ATH28.

Independent replay reconstructs every first qualifying exit close and earliest tradable opening, original-entry anchors, pending exits, cash/share/dividend/fee accounting, terminal settlement, source signal timing, daily holdings, company capacity and monthly targets. All ten variants are checked. Raw reconstruction verifies16,174,106 SMA200 cells;400 calendar summaries and ten SPY curves are independently checked. Closed plus ending-open PnL reconciles to final wealth. See baseline_replay.json, independent_verification_*.json and raw_feature_summary_verification.json.

The first run was invalidated by an implementation error: a same-open exit/reentry could inherit the old effective floor for that day. Independent first-trigger verification detected it, a regression test was added, and all variants rerun without changing strategy parameters. The invalid directory is retained with failure metadata and is not research evidence.

Missing trend, stale-close and deferred-fill cases are preserved and reported per variant below. Missing trend means that trend leg cannot issue a new decision; it does not remove the position. Stale quotes are carried rather than invented executable prices; inspect ending stale status before any live use.

| Run | Missing trend position-days | Stale close position-days | Deferred exit-days |
| --- | ---: | ---: | ---: |
| floor5_sma200__drift_0bps | 632 | 8 | 2 |
| floor5_sma200__drift_10bps | 632 | 8 | 2 |
| floor5_sma200__monthly_equal_0bps | 635 | 9 | 1 |
| floor5_sma200__monthly_equal_10bps | 635 | 9 | 1 |
| floor5_sma50__drift_10bps | 31 | 4 | 5 |
| floor5_sma50__monthly_equal_10bps | 31 | 4 | 5 |
| sma200__drift_10bps | 431 | 6 | 1 |
| sma200__monthly_equal_10bps | 431 | 6 | 1 |
| sma50__drift_10bps | 31 | 4 | 5 |
| sma50__monthly_equal_10bps | 31 | 4 | 5 |

As in ATH28, dividends are available on ex-date rather than actual payment date, execution costs are fixed proportional estimates rather than impact models, and historical data is current-vintage. Cash receives no interest. No statistical superiority, independent holdout, optimal threshold or confirmed alpha is claimed.

## Files and reproduction

Run: `outputs/backtests/ath_30_initial_risk_trend_v001/20261017T154917914966Z`.
Protocol: `research/ath/ATH_INITIAL_RISK_TREND_PLAN.md`. Engine extension preserves the original ATH28 engine. Commands: `backtest_ath_initial_risk_trend.py`; `verify_ath_initial_risk_trend.py RUN [RULE]`; `verify_ath_initial_risk_features.py RUN`; `report_ath_initial_risk_trend.py RUN`. Saved summary.csv includes all400 variant/period rows. Full decisions, transactions, daily holdings/equity, company PnL, closed and open cashflows, skipped reasons and source hashes are retained.
