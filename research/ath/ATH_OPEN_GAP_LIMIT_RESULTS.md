# ATH37: opening-only gap limits

Clean 2008-01-02 to 2026-06-30 simulation; same ATH35 fresh ATH + market6-1/top20 signals, MV priority, maximum20 companies, 5% initial weights, SMA150 next-opening exits, 10bps per buy/sell and zero cash yield. Only entry eligibility changes. Opening-only order cap = signal close + k times strictly prior ATR20. Equality fills; downward gaps are allowed. No later intraday fill or chase of that signal. A later fresh ATH can qualify. Entry information does not include future close, low or outcomes. 

Daily prices model an opening-only limit fill at the recorded opening when within the known cap. Auction participation, queue priority, spread and volume availability are unverified; this is not a validated live execution model.

## Net portfolio results

| Opening cap | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |
|---|---:|---:|---:|---:|
| unrestricted | 8.70% | 8.48% | -45.28% | -44.49% |
| gap05 | 10.37% | 9.97% | -42.72% | -42.75% |
| gap10 | 9.21% | 9.14% | -42.64% | -44.12% |
| gap20 | 8.98% | 8.76% | -44.21% | -43.70% |
| SPY | 11.24% | 11.24% | -52.45% | -52.45% |

## Recent calendar slices

| Opening cap | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |
|---|---:|---:|---:|---:|
| unrestricted | 6.89% | 6.55% | 8.53% | 5.48% |
| gap05 | 9.76% | 9.77% | 13.21% | 10.67% |
| gap10 | 7.49% | 7.50% | 8.69% | 6.95% |
| gap20 | 7.49% | 7.16% | 10.01% | 6.83% |
| SPY | 14.67% | 14.67% | 22.83% | 22.83% |

Subperiods retain positions from the clean 2008 start; they are not fresh portfolio starts. All calendar years and registered periods remain in summary.csv.

## Foregone opportunities: separate annual signal outcomes

| Rule | Over-cap candidates | Mature annual outcomes | Annual losses | Annual returns >=100% | Mean annual excess vs SPY |
|---|---:|---:|---:|---:|---:|
| gap05 | 1044 | 934 | 427 | 57 | -2.64 pp |
| gap10 | 264 | 234 | 101 | 22 | 2.19 pp |
| gap20 | 82 | 71 | 33 | 7 | 3.51 pp |

There are 17,266 screened candidates per variant, including 26 with no executable opening that the baseline also could not buy. The candidate tables exclude those missing openings from over-cap counts. Common mature executable annual coverage is15,853. Annual returns include distributions and original terminal treatment. These are gross buy-and-hold signal outcomes, not actual SMA150 realized profits, portfolio CAGR, independent observations or the causal value of rejecting a trade. Missing/immature counts remain explicit. Full accepted, rejected and executable summaries are saved.

| Cap rule | Policy | Actual baseline entries | Baseline entries over cap |
|---|---|---:|---:|
| gap05 | drift | 809 | 69 |
| gap05 | monthly_equal | 806 | 73 |
| gap10 | drift | 809 | 26 |
| gap10 | monthly_equal | 806 | 27 |
| gap20 | drift | 809 | 6 |
| gap20 | monthly_equal | 806 | 5 |

A rejected high-ranked candidate can free capacity for the next eligible candidate in the unchanged MV ordering. Later holdings, entries and weights consequently diverge. Rejected baseline entry counts therefore do not describe all differences between portfolios.

## Interpretation

All three caps improve the inspected full-period CAGR against unrestricted SMA150 under both weighting policies. The tightest tested0.5ATR cap improves drift8.70% to10.37% and monthly8.48% to9.97%, with smaller drawdowns. Recent2018 CAGR also improves, but all variants still trail SPY. This is an exploratory lead, not a proven optimal cap or confirmed alpha. The accepted versus rejected annual signal means differ only modestly at0.5ATR; high-gap cohorts at1/2ATR have positive mean excess despite portfolio improvements. Portfolio differences depend on capacity, weights and subsequent paths, not a uniform claim that large-gap signals are bad.

The filter rejects future losers and large winners. Do not combine it automatically with the previously strongest stepped exit: this experiment keeps SMA150 fixed. No new confidence interval, equal-risk attribution or untouched validation is claimed. Inspected 2008-present data remain development history; auction feasibility needs separate validation.

## Verification

All 50 unrestricted control period rows exactly reproduce ATH35 SMA150 CAGR, NAV, drawdown and exposure.24 focused tests pass. All eight independent eligibility/next-opening/cash/share replays passed, checking 17,266 entry screens per variant. Independently rebuilt 17,285 modern candidate ATR/signal-close windows, 46,008,280 SMA cells, 200 portfolio summaries and eight SPY curves. Final verification status and source/code hashes are recorded in manifest.json.

Run: `outputs\backtests\ath_37_open_gap_limit_v001\20261017T184924934825Z`. Protocol: `ATH_OPEN_GAP_LIMIT_PLAN.md`.
