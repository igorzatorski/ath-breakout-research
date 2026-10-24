# Futures trend v001: frozen research prototype

Recorded 2026-10-24 after source coverage audit and before portfolio performance.
One configuration; no grid, optimization or independent OOS claim.

## Data and scope

Public shipped CSVs from `pst-group/pysystemtrade`, pinned commit
`164328bd76d2937d3dd61491377704c488283bc2`. Preserve raw files locally (ignored by
Git), repository license and hashes. Use the predeclared 20 market families.
Use provider adjusted, multiple-price and roll-calendar data. Complete comparable
intraday adjusted changes were reconciled with priced-contract changes, using
the previous forward price on a switch; no mismatches were found.

This is market-level research data, not a complete audited executable contract
chain. Source calendars, metadata and roll choices are inherited; historical
liquidity, first notice/delivery compliance and margin schedules are unverified.
For RUSSELL_mini the optional roll-calendar file is absent; actual source contract
transitions remain observable in multiple prices. Source SILVER uses a 1,000 oz
research unit rather than the standard SI 5,000 oz lot. Use source point values
and costs consistently; do not claim exact standard-contract implementation.
RTY history starts 2015-03-11; all sources end 2024-03-28. This shorter source
coverage determines the common sample, not performance-based window selection.

Collapse each source's intraday records to the last row per source date with
finite priced and adjusted values. Preserve source timezone ambiguity as a
limitation. Mark all portfolios on SPY/NYSE session dates. Carry the last observed
mark across holidays, maximum three consecutive missing NYSE sessions; report
staleness and fail beyond this. Include all price changes/rolls between marks.

## Signal and timing

Pre-performance eligibility amendment: the calendar alignment audit found priced
mark gaps longer than three NYSE sessions in EUR (up to 7), JPY (4) and CORN (8).
The initial portfolio therefore excludes roots 6E, 6J and ZC, retaining 17 of the
20 candidates. No performance had been calculated when exclusions were made.
Keep the maximum-three-session rule unchanged; do not select replacement markets
or backfill missing priced contracts with another maturity. Class budgets remain
25% each, divided across retained members. Save all 20 eligibility decisions.

- Monthly decisions at the final NYSE session of each month.
- Direction = sign of adjusted price change over twelve calendar months, using
  last available prior mark at the lookback date. No percentage/log return on
  additive back-adjusted levels. Zero -> flat.
- One shared configuration for all markets; no SHA or cross-sectional ranking.
- Decisions at close D execute at close D+1, first earning P&L over D+1 to D+2.
  This full-session delay is deliberate given source timestamp limitations.
- Start at the first month-end after all 20 markets have 12 months of valid
  history and 60 observations for risk. Benchmark uses the same execution date.
- Final positions are marked at the common last close, without forced exit costs.

## Position sizing and costs

- Initial capital USD 10 million. Fractional source research units; no integer
  rounding. This is not a tradability claim for smaller accounts.
- 60-session sample volatility of dollar price changes; annualization 252.
  Floor daily dollar volatility at 1% of median absolute 60-session notional,
  divided by sqrt(252). Use rolling information only.
- Standalone risk budget: 25% per broad class, equal within class. Initial
  quantities proportional to budget / dollar volatility, with direction sign.
- Scale using 60-session covariance, 25% shrinkage toward diagonal, to 10%
  predicted annual portfolio volatility. Add diagonal variance floors consistently.
- At decision time cap each market's absolute notional at 0.5 NAV, each class
  at 1.5 NAV, total gross at 4 NAV. Reapply risk scaling downward if caps disturb
  hedges. Do not upscale after caps. No claim of realized equal risk contribution.
- Notional uses absolute source raw price times point value, with a floor of
  10% of trailing median absolute notional, accommodating zero/negative prices.
- Fixed units between monthly executions. Daily risk monitoring uses an explicit
  illustrative margin proxy (10% of gross notional). If this exceeds 50% NAV,
  schedule reduction toward 45% at the next close. It is not historical broker
  margin or a verified liquidation simulation. Report proxy breaches.
- Transaction cost per source unit per leg = source `PerBlock` USD commission
  plus source `SpreadCost` price points times source point value. Static current
  estimates applied throughout history, not historical realized bid/ask costs.
  Reject nonzero unsupported `Percentage`/`PerTrade` config values.
- Charge absolute quantity changes; charge two legs for each inherited source
  roll on held units. This approximates fills with explicit modeled friction.
- Dollar P&L = held units times adjusted price change times point value.
  Back-adjusted levels are never denominators or cash purchase prices.
- Entire NAV is collateral cash; 0% collateral interest, no fund fees or taxes.
  Both gross futures P&L and net modeled execution costs are reported separately.

## Controls and reporting

1. Monthly time-series momentum portfolio, net of modeled costs.
2. Always-long futures using the same risk method and costs (direction control).
3. SPY buy-and-hold with dividends via adjusted close, 1 bp initial execution cost.
4. SPY monthly 10% volatility target, rolling 60 sessions, exposure capped at 100%
   (cash otherwise), 1 bp per changed notional; no borrowing. It is an approximate
   risk comparator, not guaranteed to match realized futures volatility.

All cash earns 0%, dates and close-execution delay match. Report CAGR, realized
volatility, Sharpe with zero risk-free rate, max close-equity drawdown, final NAV,
correlation with SPY, annual returns, per-market P&L/costs and exposure/margin
proxy diagnostics. Save all four paths, decisions, quantities, fees, rolls,
source audit and code/data fingerprints. No results are independent validation.

## Required checks before first run

Hand-calculated long and short mark-to-market, fees and roll costs; no principal
purchase deduction; causal delayed execution; additive-adjustment invariance;
zero/negative price handling; caps and no-leverage SPY self-financing; full daily
cash/equity reconciliation. Review all source-coverage exclusions and report them.
