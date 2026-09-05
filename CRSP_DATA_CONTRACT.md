# CRSP Data Contract

## Scope

This document fixes the first source contract for migrating the historical
research pipeline from Yahoo Finance to the quarterly CRSP Stock Version 2
(CIZ) database on WRDS. It covers daily security observations only. It does not
yet switch the screener or backtester to CRSP.

## Verified WRDS schema

The local metadata audit on 2026-09-05 found 95 tables and 2,007 columns in
`crsp_q_stock`. No licensed observations were read by the audit.

A coverage check on 2026-09-05 found that the quarterly daily table ends on
2026-06-30. Historical backtests must stop at the latest available CRSP session.
The current screener must reject that release as stale for September 2026 and
use a separately validated current-market source.

The principal daily source is `crsp_q_stock.dsf_v2`. It already combines daily
security observations with point-in-time identifiers, security classifications,
shares outstanding, market capitalization, and cumulative adjustment factors.

Supporting sources required by later milestones are:

| Purpose | Table | Key |
|---|---|---|
| Daily security data | `dsf_v2` | `permno`, `dlycaldt` |
| Historical security identity | `stksecurityinfohist` | `permno`, effective date range |
| Detailed distributions | `stkdistributions` | `permno`, `disexdt`, `disseqnbr` |
| Delisting outcomes | `stkdelists` | `permno`, `delistingdt` |
| Shares history | `stkshares` | `permno`, effective date range |
| Daily cumulative adjustments | `stkdlycumulativeadjfactor` | `permno`, `dlycaldt` |

## Daily raw contract

`src/ath_breakout/data/adapters/crsp.py` maps the selected CIZ columns to stable
internal names. `PERMNO` is the security identifier; ticker is point-in-time
display metadata and must never be used as the historical join key.

The first contract preserves raw OHLC, CRSP returns, dividend summaries,
cumulative adjustment factors, market capitalization, shares outstanding, and
security classification flags. Missing numeric values remain missing. The
adapter does not invent neutral corporate-action values.

## Adjustment boundary

CRSP documents raw price, dividend, share, and volume fields separately from
cumulative adjustment factors. Comparable adjusted prices are calculated as
raw price divided by `DlyCumFacPr`; adjusted shares and volume are calculated by
multiplying by `DlyCumFacShr`.

`add_crsp_comparable_values` implements these calculations under explicit
`comparable_*` names. They are not yet wired into the strategy's
`split_adj_*` columns. Before the current strategy consumes CRSP prices, the
implementation must verify:

1. a normal security with no adjustment events;
2. a forward or reverse split;
3. an ordinary cash dividend;
4. a non-ordinary distribution;
5. a ticker change under one `PERMNO`;
6. a delisted security.

The bounded live validation currently covers items 2-4: Apple's 2020 split,
Apple's 2025 ordinary cash dividends, and one 2025 non-ordinary distribution.
`stksecurityinfohist` supplies point-in-time ticker and name intervals while
`PERMNO` remains the stable security key. A bounded live check confirmed the
2022 `FB` to `META` transition in two non-overlapping intervals under one
`PERMNO`.

`stkdelists` supplies the observed total return from the final tradable price
to the delisting outcome. CIZ also stores that return in the daily file on
`DelDlyDt`, conventionally the trading date immediately after delisting. The
pipeline must apply this terminal return once. A missing `DelRet` remains
missing until an explicit research rule is separately chosen and documented.
A bounded live check confirmed one 2025 `stkdelists` outcome against its exact
daily `DlyRet` row and `DlyDelFlg` marker.

CRSP return components remain separate: `total_return` maps to `DlyRet`,
`return_ex_distributions` maps to the price return `DlyRetx`, and
`income_return` maps to `DlyRetI`. Ordinary and non-ordinary distribution
amounts are never inferred from the difference between returns. For available
components, CIZ uses the additive identity `DlyRet = DlyRetx + DlyRetI`.

## Point-in-time universe boundary

The existing `in_current_universe` registry flag cannot be used by the CRSP
backtest. Monthly snapshots select up to 3,000 U.S.-incorporated common stocks
on NYSE, NYSE American, and Nasdaq. A security needs a formation-date price of
at least USD 5 and at least 40 valid observations in the approximate 60-session
lookback. Ranking uses median daily dollar volume, with market capitalization
and `PERMNO` as deterministic tie-breakers. Aggregation runs inside WRDS so the
prototype transfers ranked rows rather than the underlying daily panel.

A bounded prototype formed on 2025-09-30 returned 2,729 qualifying securities
and transferred no underlying daily observations. The target is therefore a
ceiling of 3,000 rather than a requirement to fill every snapshot.

Membership formed after a session close becomes effective on the following
session. The production builder will repeat this snapshot monthly from 1993,
with each membership interval ending immediately before the next snapshot takes
effect.

Until that table and delisting handling exist, CRSP data must not be presented
as a survivorship-bias-free portfolio backtest.
