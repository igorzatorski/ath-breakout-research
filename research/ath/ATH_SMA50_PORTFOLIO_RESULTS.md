# First ATH portfolio: SMA50 exit and two weighting policies

Exploratory development-history backtest completed 2026-10-17. Both fixed versions underperform SPY over the full history and since 2010; neither establishes a useful net edge. Monthly equal weighting improves this inspected result slightly, but drawdowns remain worse than SPY. This does not isolate the causal benefit of SMA50 versus another exit.

## Frozen implementation

1994-01-03 to 2026-06-30, 8,177 sessions; USD100,000 initial cash. All25,250 pre-outcome ATH + market6-1/top20 candidates from ATH27; no annual-outcome availability mask. Fresh next-session-open signals only, ordered by saved momentum/volume score. Up to20 distinct companies, target5% of opening wealth at entry. Close below SMA50 triggers next observed open sale. No holding cap, take-profit or rank-drop exit. No extra consolidation, industry or other filter stack.

Drift leaves existing quantities unchanged. Monthly equal resets every current holding to5% of post-cost opening wealth after month-end; it does not force monthly replacement. Fewer20 eligible holdings leave cash. Cash earns0%; dividends are cash, not automatically reinvested in the issuer. Fractional shares, no leverage/tax. Primary costs10bps per buy/sell, with0bps gross reference. SPY is total-return buy-and-hold from the first opening, with the same one-time entry fee. Final holdings are marked, not forcibly sold.

## Full-history results

| Version | CAGR | SPY CAGR | CAGR gap (pp) | Maximum drawdown | Average invested | Final USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| drift_0bps | 8.95% | 10.87% | -1.92 | -70.01% | 74.94% | 1,615,715 |
| drift_10bps | 7.95% | 10.87% | -2.92 | -70.70% | 74.95% | 1,197,931 |
| monthly_equal_0bps | 9.56% | 10.87% | -1.31 | -69.23% | 74.24% | 1,936,974 |
| monthly_equal_10bps | 8.48% | 10.87% | -2.39 | -69.97% | 74.25% | 1,402,876 |

SPY maximum drawdown is55.19%; net final wealth is USD2,845,973. CAGR uses252 sessions per year. These are compounded portfolio returns, not the earlier arithmetic mean annual event returns or CAPM alpha.

## Calendar subperiods, 10bps

| Period | Drift CAGR | Monthly equal CAGR | SPY CAGR |
| --- | ---: | ---: | ---: |
| 1994_2009 | 9.21% | 9.41% | 7.48% |
| 2010_2017 | 7.51% | 7.56% | 13.84% |
| 2018_end | 6.03% | 7.60% | 14.67% |
| 2018_2020 | 21.97% | 23.59% | 14.01% |
| 2021_2022 | -14.99% | -12.65% | 2.64% |
| 2023_end | 6.67% | 7.61% | 22.83% |

These are actual continuing portfolio calendar returns, not portfolios restarted in each subperiod. The recent window ends2026-06-30. All annual rows are retained in summary.csv.

## Exposure, costs and trade distribution

| Diagnostic, net | Drift | Monthly equal |
| --- | ---: | ---: |
| Average names | 14.68 | 14.74 |
| Days at least95% invested | 46.72% | 47.08% |
| Days with20 names | 38.42% | 41.65% |
| Total nominal fees USD | 171,340 | 201,645 |
| Closed position episodes | 3223 | 3234 |
| Closed episodes losing money | 61.15% | 60.24% |
| Median episode cashflow profit ratio | -3.46% | -3.14% |
| Mean losing episode cashflow ratio | -9.35% | -9.06% |
| Mean non-losing episode cashflow ratio | 20.31% | 18.40% |
| Median calendar holding days | 45 | 45 |
| Largest daily single-name weight | 26.00% | 10.51% |

The desired near100% exposure was not consistently reached under fresh-signal rules. This is an implementation consequence, not a tested market-allocation filter. Do not attribute all underperformance to cash: equity selection, exit timing, weighting and costs are jointly present; no cash-matched counterfactual was run.

A right tail exists, but frequent small losses do not by themselves guarantee an attractive portfolio. Episode ratios include all purchases, sales and dividends; with monthly additions/trims they are cashflow profit ratios, not time-weighted stock returns. Open episodes are excluded from this closed-trade table. Observed average losing episodes are about9%, so SMA50 is not a hard5% loss cap. Monthly trimming reduces concentration but also sells parts of winners.

## Accounting and verification

Seven focused tests passed: next-open gap exits, no same-day signal use, ex-date entitlement, once-only terminal settlement, monthly fees/target conservation, company uniqueness, deferred exits, missing-price reconciliation, split consistency and simultaneous split/dividend example. Ruff passed.

Independent transaction replay checks cash, shares, prices, fees, source-signal identity, next-session entry timing, SMA decision and deferred-exit timing, daily company/capacity constraints, holdings NAV, full CAGR and drawdown. Raw CRSP reconstruction checks16,174,106 close/SMA cells. See independent_verification.json and raw_panel_verification.json.

Each variant has4 carried stale-close position-days,5 deferred exit-days and4 return comparisons skipped because the previous source close is missing. There are31 unique held security-days with unavailable SMA50; no new SMA decision is possible then. All ending holdings have observed prices. Monthly policies have9 deferred-rebalance days. Valid matched regular-return checks total119,895 drift /120,407 monthly, maximum error below0.000001. These price/SMA gaps are retained, not silently excluded.

Technical amendments during blocked runs: terminal nonordinary cash is settled through the CIZ Y return once; source-return checks require matching observed previous-close endpoints; CIZ dividends on simultaneous split dates use the pre-event share basis (current cumulative factor times period price factor). Strategy parameters were unchanged. Earlier incomplete directories are failed technical attempts, not candidate strategy results.

Terminal returns already include delisting effects; no second delisting return is applied. Normal cash-ledger distributions are not also compounded via total_return. Splits preserve adjusted economic units. This remains a simplified model: ex-date cash availability rather than payment dates, a fixed proportional execution cost rather than market impact, possible stale quotes and historical-source revisions. No live trading or WRDS connection was needed.

## Decision and next experiment

Keep this as the first reproducible portfolio reference, not an adopted live strategy. Do not optimize SMA length, rebalance frequency or filter combinations from these outcomes. First diagnose the already saved trade paths: how many winners were sold on a temporary SMA50 break, how much subsequent recovery occurred, and whether large losses were gap-driven or slow exits. Use fixed252-session post-entry paths for descriptive comparison, explicitly conditional on observed exits; that will not itself prove a better executable strategy. A later rule change needs its own frozen comparator and cost/exposure controls.

All inspected history is development data. No untouched holdout, risk-adjusted alpha or statistical superiority of one weighting rule has been established.

## Reproduce

```powershell
.venv/Scripts/python.exe scripts/research/backtest_ath_sma50_portfolio.py
.venv/Scripts/python.exe scripts/research/verify_ath_sma50_portfolio.py outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z
.venv/Scripts/python.exe scripts/research/verify_ath_sma50_panels.py outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z
```

Run: `outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z`. Protocol: `research/ath/ATH_SMA50_PORTFOLIO_PLAN.md`. Daily equity, holdings, closed/open cashflows, transactions, skipped reasons, summaries and hashes are retained.
