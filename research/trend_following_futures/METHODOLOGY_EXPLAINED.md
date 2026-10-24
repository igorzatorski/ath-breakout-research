# v001 methodology and missing-data follow-up

2026-10-24. This note explains the existing result; it does not change the
baseline, rerun performance or authorize a new 50-market performance search.

## What the gap investigation established

The v001 eligibility gate measured missing priced-contract marks on NYSE
valuation dates, not on individually verified futures session calendars.
It is a conservative prototype gate, not a definitive exchange-closure test.
The three-session cutoff is an engineering choice, not an economic law.

Follow-up on the archived raw multiple-price files found:

- EUR on 2018-10-22 through 2018-10-25: no marks for the selected December
  2018 priced maturity, but March 2019 forward-maturity marks are present.
- JPY on those dates: no marks for the December 2018 priced maturity, while
  the March 2019 forward has multiple changing intraday observations.
- CORN from 2019-12-23 through 2020-01-03, on NYSE valuation dates: the priced
  December 2020 maturity is missing, while other maturities have marks. The
  source uses a deferred/seasonal roll policy, not necessarily the front month.
- The CME [2019 Christmas settlement notice](https://www.cmegroup.com/tools-information/holiday-calendar/files/2019-christmas-holiday-settlement-times.pdf)
  specifies grain and FX settlement times on 2019-12-24; that missing priced
  observation cannot be explained simply by every relevant market being shut.

These are observations about the archived data, not proof of the precise vendor
failure mechanism. Possible causes include missing source collection, selection
of a maturity with sparse quotes, or archival processing. Historical volume and
the original data collection logs are unavailable here. A currency banking/value
date holiday also does not by itself establish a futures trading closure.

Evidence: `outputs/trend_following_futures/gap_diagnostic/gap_evidence.csv`.
Reproduce with `.venv/Scripts/python.exe -m run.futures_gap_diagnostic`.
Do not substitute another maturity without rebuilding and validating its roll
and P&L history. Full per-market session-calendar classification remains open.

## Exact existing model

1. At the final NYSE session of each month, compare each market's adjusted price
   with its last available mark twelve calendar months earlier. Positive ->
   long, negative -> short, zero -> flat. No Z-score or cross-sectional ranking.
2. Execute at the following full NYSE session's closing mark. New positions
   first earn the next close-to-close change. Positions are fixed between
   monthly orders apart from the predefined margin-proxy emergency rule.
3. Estimate each source unit's daily dollar P&L volatility over 60 sessions.
   Dollar volatility includes the price-point multiplier. Quantities are
   inversely proportional to that volatility, with an annual-volatility floor.
4. Allocate initial standalone risk budgets equally to four classes (25% each),
   then equally within each retained class. This is not exact equal marginal
   risk contribution after correlations and caps.
5. Estimate 60-session covariance, shrinking off-diagonal terms by 25%; apply
   variance floors. Scale the portfolio to 10% predicted annual volatility.
   The realized v001 annual volatility was 10.95%; target is not a loss limit.
6. At monthly sizing, cap a market at 0.5 NAV, class at 1.5 NAV and aggregate
   gross at 4 NAV. Drift between trades can exceed these decision-time caps;
   observed trend gross peaked at 4.38 NAV. Average gross was 2.99 NAV.
7. Use fractional source units and USD 10 million initial collateral. Charge
   modeled source commissions and adverse spread costs on changes and both
   roll legs. Cash interest is 0%, with no fund fees/taxes. Historical broker
   margin is unavailable; the 10%-of-gross proxy is an explicit approximation.

## Volatility-sizing intuition

If a unit of instrument A has USD 500 daily P&L standard deviation and a unit
of B has USD 1,000, two A units and one B unit each have USD 1,000 standalone
daily standard deviation. This is risk normalization, not the selection of a
more profitable market. Correlations determine their combined volatility.
When measured volatility rises, desired quantity falls at the next sizing date;
the model does not automatically exit on an intramonth loss or trend reversal.

## Expansion toward 50 markets

A broader universe is a sensible next research question, with candidate global
equity indices, non-US government bonds, additional FX and commodity subgroups.
Define it using data availability, economic coverage, liquidity and operational
criteria before seeing performance, not by selecting historical winners.
Multiple similar bond maturities or US equity indices are correlated exposures,
not independent trend opportunities. Keep sector controls and evaluate added
markets' contribution, costs, risk concentration and effect on data coverage.

Compare unchanged v001 and the expanded portfolio on an explicitly aligned
sample. Do not silently shorten the sample to accommodate newer markets or
pretend contracts existed before listing. Repair calendar and source issues
before interpreting a 50-market result as a strategy improvement.
