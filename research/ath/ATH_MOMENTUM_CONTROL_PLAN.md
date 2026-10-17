# ATH incremental information beyond momentum

Study `ath_08_momentum_control_v001`. Fixed before inspecting outcomes.

Question: does ATH have higher 252-session total return than contemporaneous
non-ATH stocks with similar size, volatility AND prior momentum?

Use the frozen ath_04 v002 events, quality restrictions, PIT monthly membership,
ADV21 >= $10m, same-day non-ATH controls, next-open entry, existing CIZ terminal
cash handling and data end 2026-06-30. No new downloads or WRDS connection.

Momentum at signal session t is compounded CRSP total return over sessions
t-251 through t-21 inclusive (231 returns, the 12-minus-1-month convention).
All 231 returns must be observed and >= -1; gaps are not bridged. Return -100%
produces -100% momentum. No future information enters features or matching.

Five distinct control PERMCOs excluding the event PERMCO. Original size ratio
<= 2 and volatility ratio <= 1.5; additional absolute momentum difference <=
0.10 (10 percentage points). Rank by sum of squared standardized same-day
log size, log volatility and momentum differences, ties by PERMNO. Fixed rules,
no alternate windows/calipers searched. Controls may break ATH on later dates.

Rebuild the original eligible control pool using the exact original history
rules; assert reconstructed event IDs/feature values and original matches agree.
Save matching diagnostics, IDs, features, exclusions and return status. Do not
replace controls after observing forward validity. Require all five valid.

Primary descriptive comparison: annual ATH minus new controls on the intersection
where old and new five-control annual baskets and stock/SPY are valid. Show old
and new excess on those SAME events, and paired change with 252/504-session
date-block bootstrap (2000 draws, seed 20261015). Also report full available new
sample, coverage attrition, year/period summaries, equal-date/equal-security
weight sensitivity and frozen cooldown21 subset. These are not independent tests
or portfolio returns. Check feature balance before/after.

This retrospective annual extension is exploratory, not causal alpha. Matching
one momentum measure does not remove sector, beta, other momentum definitions,
history-quality selection, dependence, or uncertainty from choosing the annual
horizon after seeing results. A reduced excess would be consistent with shared
momentum information but would not prove momentum caused the original effect.
