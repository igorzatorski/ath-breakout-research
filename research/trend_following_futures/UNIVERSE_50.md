# Fifty-market candidate universe: preparation

Status: prepared, not backtested. The candidate list preserves all original 20 and adds 30 markets.
Selection uses economic breadth and source metadata/file availability; no v002 returns were inspected.

## Candidate markets

| market_id     | market                    | asset_class      | pnl_currency   | prior_audit_status       | preparation_flags                                                                                                        |
|:--------------|:--------------------------|:-----------------|:---------------|:-------------------------|:-------------------------------------------------------------------------------------------------------------------------|
| SP500         | S&P 500                   | equity_indices   | USD            | v001_prototype_eligible  |                                                                                                                          |
| NASDAQ        | Nasdaq-100                | equity_indices   | USD            | v001_prototype_eligible  |                                                                                                                          |
| RUSSELL_mini  | Russell 2000              | equity_indices   | USD            | v001_prototype_eligible  | published roll calendar missing                                                                                          |
| DAX           | DAX                       | equity_indices   | EUR            | not_audited              | USD conversion of P&L, notional and fees required; provider point value is micro-sized; historical unit mapping required |
| EUROSTX       | Euro Stoxx 50             | equity_indices   | EUR            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| FTSE100       | FTSE 100                  | equity_indices   | GBP            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| NIKKEI        | Nikkei 225                | equity_indices   | JPY            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| SPI200        | ASX SPI 200               | equity_indices   | AUD            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| CAC           | CAC 40                    | equity_indices   | EUR            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| SMI           | Swiss Market Index        | equity_indices   | CHF            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| US2           | US 2-year Treasury note   | government_bonds | USD            | v001_prototype_eligible  |                                                                                                                          |
| US10          | US 10-year Treasury note  | government_bonds | USD            | v001_prototype_eligible  |                                                                                                                          |
| US20          | US Treasury bond          | government_bonds | USD            | v001_prototype_eligible  |                                                                                                                          |
| US5           | US 5-year Treasury note   | government_bonds | USD            | not_audited              |                                                                                                                          |
| US30          | US Ultra Treasury bond    | government_bonds | USD            | not_audited              |                                                                                                                          |
| BUND          | German Bund               | government_bonds | EUR            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| BOBL          | German Bobl               | government_bonds | EUR            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| SHATZ         | German Schatz             | government_bonds | EUR            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| GILT          | UK Long Gilt              | government_bonds | GBP            | not_audited              | USD conversion of P&L, notional and fees required; commission estimate missing or zero; verify                           |
| JGB           | Japanese government bond  | government_bonds | JPY            | not_audited              | USD conversion of P&L, notional and fees required                                                                        |
| EUR           | Euro vs USD               | currencies       | USD            | v001_gap_repair_required | priced-series gaps unresolved                                                                                            |
| JPY           | Yen vs USD                | currencies       | USD            | v001_gap_repair_required | priced-series gaps unresolved                                                                                            |
| GBP           | Pound vs USD              | currencies       | USD            | v001_prototype_eligible  |                                                                                                                          |
| AUD           | Australian dollar vs USD  | currencies       | USD            | v001_prototype_eligible  |                                                                                                                          |
| CAD           | Canadian dollar vs USD    | currencies       | USD            | v001_prototype_eligible  |                                                                                                                          |
| CHF           | Swiss franc vs USD        | currencies       | USD            | not_audited              |                                                                                                                          |
| NZD           | New Zealand dollar vs USD | currencies       | USD            | not_audited              |                                                                                                                          |
| MXP           | Mexican peso vs USD       | currencies       | USD            | not_audited              |                                                                                                                          |
| NOK           | Norwegian krone vs USD    | currencies       | USD            | not_audited              |                                                                                                                          |
| SEK           | Swedish krona vs USD      | currencies       | USD            | not_audited              |                                                                                                                          |
| CRUDE_W       | WTI crude oil             | commodities      | USD            | v001_prototype_eligible  |                                                                                                                          |
| GAS_US        | Henry Hub natural gas     | commodities      | USD            | v001_prototype_eligible  |                                                                                                                          |
| GOLD          | Gold                      | commodities      | USD            | v001_prototype_eligible  |                                                                                                                          |
| SILVER        | Silver                    | commodities      | USD            | v001_prototype_eligible  | source 1000 oz unit differs from standard SI 5000 oz                                                                     |
| COPPER        | Copper                    | commodities      | USD            | v001_prototype_eligible  |                                                                                                                          |
| CORN          | Corn                      | commodities      | USD            | v001_gap_repair_required | priced-series gaps unresolved                                                                                            |
| WHEAT         | Chicago wheat             | commodities      | USD            | v001_prototype_eligible  |                                                                                                                          |
| SOYBEAN       | Soybeans                  | commodities      | USD            | v001_prototype_eligible  |                                                                                                                          |
| LIVECOW       | Live cattle               | commodities      | USD            | v001_prototype_eligible  |                                                                                                                          |
| BRENT_W       | Brent crude oil           | commodities      | USD            | not_audited              |                                                                                                                          |
| HEATOIL       | Heating oil               | commodities      | USD            | not_audited              |                                                                                                                          |
| GASOILINE     | RBOB gasoline             | commodities      | USD            | not_audited              |                                                                                                                          |
| GASOIL        | Low sulphur gasoil        | commodities      | USD            | not_audited              |                                                                                                                          |
| ALUMINIUM_LME | LME aluminium             | commodities      | USD            | not_audited              |                                                                                                                          |
| NICKEL_LME    | LME nickel                | commodities      | USD            | not_audited              | commission estimate missing or zero; verify; exchange suspensions/cancelled trades and venue history require audit       |
| PLAT          | Platinum                  | commodities      | USD            | not_audited              |                                                                                                                          |
| PALLAD        | Palladium                 | commodities      | USD            | not_audited              |                                                                                                                          |
| COFFEE        | Coffee                    | commodities      | USD            | not_audited              |                                                                                                                          |
| SUGAR11       | Sugar No. 11              | commodities      | USD            | not_audited              |                                                                                                                          |
| COTTON2       | Cotton No. 2              | commodities      | USD            | not_audited              |                                                                                                                          |

## Verified preparation

| asset_class      |   candidates |   adjusted_listed |   multiple_listed |   calendar_listed |
|:-----------------|-------------:|------------------:|------------------:|------------------:|
| commodities      |           20 |                20 |                20 |                20 |
| currencies       |           10 |                10 |                10 |                10 |
| equity_indices   |           10 |                10 |                10 |                 9 |
| government_bonds |           10 |                10 |                10 |                10 |

Foreign-currency P&L markets: 12. Required non-USD currencies: AUD, CHF, EUR, GBP, JPY.
A listed CSV does not establish complete usable history, venue/session calendars, liquidity or correct historical contract units.
Historical source descriptions and units are preserved as provider metadata, not represented as current exchange specifications.

## Readiness gates

Resolve original EUR/JPY/CORN priced-series gaps using actual same-maturity data or a newly audited roll chain.
Add and test timestamp-aligned FX conversion for foreign contract P&L, fees, collateral and notional limits.
Audit per-market sessions, raw multiple-price continuity, source roll IDs, current/historical units, and missing or zero cost estimates.
Use the declared eligibility rules for the primary comparison window; exclude/investigate failures without choosing by profitability.
Keep v001 artifacts unchanged. No 50-market portfolio has been simulated by this preparation step.

See RESEARCH_PROTOCOL_V002.md and EXPERIMENTS_V002.csv for the staged questions and decision rules.
