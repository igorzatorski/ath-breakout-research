# Source and eligibility audit: futures v001

Public source repository: https://github.com/pst-group/pysystemtrade
Pinned commit: `164328bd76d2937d3dd61491377704c488283bc2`. Raw downloaded files and hashes are local under ignored `data/raw/futures/`.

Twenty predeclared candidates were audited before portfolio performance. Seventeen pass the frozen maximum-three-missing-NYSE-session rule; EUR/JPY/CORN fail. No replacement markets were selected.

| root   | source_code   | first_date   | last_date   |   daily_rows |   adjustment_mismatches |   unexplained_roll_contracts |   maximum_consecutive_stale | eligible   |
|:-------|:--------------|:-------------|:------------|-------------:|------------------------:|-----------------------------:|----------------------------:|:-----------|
| ES     | SP500         | 1982-09-14   | 2024-03-28  |        10713 |                       0 |                            0 |                           2 | True       |
| NQ     | NASDAQ        | 1999-12-14   | 2024-03-28  |         6288 |                       0 |                            0 |                           2 | True       |
| RTY    | RUSSELL_mini  | 2015-03-11   | 2024-03-28  |         2653 |                       0 |                            0 |                           0 | True       |
| ZT     | US2           | 2000-03-02   | 2024-03-28  |         6193 |                       0 |                            0 |                           2 | True       |
| ZN     | US10          | 1982-08-30   | 2024-03-28  |        10559 |                       0 |                            0 |                           2 | True       |
| ZB     | US20          | 1978-05-31   | 2024-03-28  |        11635 |                       0 |                            0 |                           2 | True       |
| 6E     | EUR           | 1999-06-15   | 2024-03-28  |         6246 |                       0 |                            0 |                           7 | False      |
| 6J     | JPY           | 1977-06-14   | 2024-03-28  |        11901 |                       0 |                            0 |                           4 | False      |
| 6B     | GBP           | 1975-12-16   | 2024-03-28  |        12326 |                       0 |                            0 |                           1 | True       |
| 6A     | AUD           | 1987-06-16   | 2024-03-28  |         9405 |                       0 |                            0 |                           2 | True       |
| 6C     | CAD           | 1972-09-14   | 2024-03-28  |        13744 |                       0 |                            0 |                           0 | True       |
| CL     | CRUDE_W       | 1990-10-16   | 2024-03-28  |         8604 |                       0 |                            0 |                           2 | True       |
| NG     | GAS_US        | 1990-07-26   | 2024-03-28  |         8536 |                       0 |                            0 |                           3 | True       |
| GC     | GOLD          | 1975-04-01   | 2024-03-28  |        12400 |                       0 |                            0 |                           2 | True       |
| SI     | SILVER        | 1970-06-15   | 2024-03-28  |        14241 |                       0 |                            0 |                           1 | True       |
| HG     | COPPER        | 1995-09-01   | 2024-03-28  |         7622 |                       0 |                            0 |                           0 | True       |
| ZC     | CORN          | 1972-10-18   | 2024-03-28  |        13022 |                       0 |                            0 |                           8 | False      |
| ZW     | WHEAT         | 1973-12-19   | 2024-03-28  |        12752 |                       0 |                            0 |                           0 | True       |
| ZS     | SOYBEAN       | 1985-09-20   | 2024-03-28  |         9703 |                       0 |                            0 |                           2 | True       |
| LE     | LIVECOW       | 1971-10-21   | 2024-03-28  |        13192 |                       0 |                            0 |                           0 | True       |

Comparable adjusted changes match same-contract price changes or previous-forward roll differences at source intraday timestamps. No mismatches were observed.

Raw missing observations were retained. Last valid source marks are carried across at most three NYSE sessions in the prototype; remaining staleness is reported, not represented as fresh quotes.

Provider adjusted/multiple files contain intraday as well as daily observations. Daily samples select the last valid source-date row. Source timestamp timezone conventions are not fully verified, so portfolio orders wait one full NYSE session.

All source contracts use USD P&L in current provider configuration. RUSSELL_mini maps a market history beginning 2015-03-11; historical venue changes are not independently audited. SILVER uses a 1000 oz research unit.

Optional RUSSELL_mini roll-calendar file is not published. Multiple-price contract IDs and forward identifiers are available and their transitions reconcile. Historical delivery/first-notice compliance is not verified.

Provider roll choices are inherited; for example some grains/oil histories use a seasonal/deferred contract rather than the front month. Do not describe this as a generic front-month benchmark.

Initial/maintenance margins, historical volume/OI, executable bid/ask fills and exact dated contract specification changes remain unresolved. This source supports a clearly labeled market-level prototype, not a certified live strategy.
