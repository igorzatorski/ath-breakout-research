# Initial 20-market candidate universe

Proposed 2026-10-24 before futures performance testing. These are market families;
actual positions use dated contract series. Product roots are CME Globex-style
identifiers, not universal vendor symbols or orders to submit.

| Class | Market | Root | Listing venue |
| --- | --- | --- | --- |
| Equity indices | E-mini S&P 500 | ES | CME |
| Equity indices | E-mini Nasdaq-100 | NQ | CME |
| Equity indices | E-mini Russell 2000 | RTY | CME |
| Government bonds | 2-Year US Treasury Note | ZT | CBOT |
| Government bonds | 10-Year US Treasury Note | ZN | CBOT |
| Government bonds | US Treasury Bond | ZB | CBOT |
| Currencies | Euro FX (USD per EUR) | 6E | CME |
| Currencies | Japanese yen (USD per JPY) | 6J | CME |
| Currencies | British pound (USD per GBP) | 6B | CME |
| Currencies | Australian dollar (USD per AUD) | 6A | CME |
| Currencies | Canadian dollar (USD per CAD) | 6C | CME |
| Commodities / energy | WTI crude oil | CL | NYMEX |
| Commodities / energy | Henry Hub natural gas | NG | NYMEX |
| Commodities / precious metals | Gold | GC | COMEX |
| Commodities / precious metals | Silver | SI | COMEX |
| Commodities / industrial metals | Copper | HG | COMEX |
| Commodities / grains | Corn | ZC | CBOT |
| Commodities / grains | Chicago SRW wheat | ZW | CBOT |
| Commodities / oilseeds | Soybeans | ZS | CBOT |
| Commodities / livestock | Live cattle | LE | CME |

Counts: 3 equity index + 3 bond + 5 currency + 9 commodity markets = 20.
Settlement/P&L currency is USD for these candidates; quotation conventions vary.
Historical multiplier, unit and currency specifications remain to be audited.

## Why this starting list

USD P&L and one exchange group simplify the first accounting model while still
covering four asset classes and several commodity subgroups. Standard contracts
are candidate research histories; micro contracts, where available, are later
execution alternatives, not interchangeable historical liquidity observations.

This is an intentionally incomplete global universe. ES/NQ/RTY share US equity
risk; ZT/ZN/ZB share US rates; the FX contracts share a USD leg. Commodity markets
also have correlated subgroups. Twenty symbols do not equal twenty independent
bets. Class budgets and exposure/correlation diagnostics matter.

No current liquidity ranking or full-history suitability is claimed. Initial
prototype eligibility is now recorded in universe.json: 17 retained markets,
with EUR/JPY/CORN excluded by the pre-performance missing-mark rule.
Fully executable-contract suitability is unverified for all candidates. Final inclusion and
historical start dates require available contract-chain data, historically
observable liquidity, expiry/first-notice information and acceptable costs.
Do not backfill newer contracts as if their current product existed earlier.

## Primary exchange references inspected

- [Equity index product slate](https://www.cmegroup.com/markets/equities.html)
- [Treasury contract tenors and root codes](https://www.cmegroup.com/trading/interest-rates/basics-of-us-treasury-futures.html)
- [FX contracts, quote direction and root codes](https://www.cmegroup.com/trading/why-futures/welcome-to-cme-fx-futures.html)
- [WTI crude oil](https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.html)
- [Henry Hub natural gas](https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.html)
- [Gold](https://www.cmegroup.com/markets/metals/precious/gold.html), [silver](https://www.cmegroup.com/markets/metals/precious/silver.html), [copper](https://www.cmegroup.com/markets/metals/base/copper.html)
- [Corn](https://www.cmegroup.com/markets/agriculture/grains/corn), [Chicago SRW wheat](https://www.cmegroup.com/markets/agriculture/grains/wheat), [soybeans](https://www.cmegroup.com/markets/agriculture/oilseeds/soybean)
- [Live cattle and LE root](https://www.cmegroup.com/markets/agriculture/livestock/live-cattle)

Several product pages render detailed specifications dynamically. The references
establish the candidate product families, not completion of a contract-spec/data
audit. Do not fill missing multipliers or ticks from these overview pages alone.
