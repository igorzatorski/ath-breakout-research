# CRSP repair verification — 2026-09-06

The five defects identified in the independent review have been addressed.

- Portfolio price return is applied once. The distribution multiplier divides
  total-return growth by price growth; it no longer compounds both.
- Opening exits receive explicit ex-date distributions in cash without using
  the closing return. Position sizing rounds nominal shares before converting
  to adjusted units. Terminal outcomes replace regular terminal-day accrual.
- The optimized loader retains all available history for candidate securities.
  It rejects duplicate security dates instead of silently keeping one row.
- Nominal prices/volumes drive the eligibility filters. Existing partitions
  recover these fields from stored adjustment factors; no download is needed.
- NYSE sessions drive the portfolio calendar independently of IWV availability.
  Missing benchmark history remains missing, including full-period metrics.
- A limited PERMNO run is explicitly diagnostic, not the monthly top-3000
  liquidity universe. Each report has its own timestamped directory.
- Missing held terminal returns stop execution. Missing-return fallbacks and
  stale position marks are counted in the summary.

## Executed checks

- Full suite: **231 passed** (`uv run python -m pytest -q -p no:cacheprovider`).
- Ruff and `git diff --check`: passed.
- Independent arithmetic: +10% price change turns 100,000 into 110,000;
  mixed price/distribution growth, opening dividend entitlement, terminal loss,
  future-data independence and missing-return handling are covered.
- Full-history versus optimized loader: identical candidate tables and retained
  simulation histories on the real 2024 diagnostic sample; 5 signals.
- Local CRSP period screen: 2025-01-02 to 2025-01-10 produced one signal and
  used the exact next NYSE session open (RL, 243.76).
- Local CRSP control backtest: 2025-01-02 to 2025-02-28 completed and generated
  the dashboard without opening a browser.
- Pre-IWV calendar/reporting check: January 1993 runs without a benchmark.
- Three legacy report directories now contain INVALID_RESULTS.txt; their
  pre-fix performance must not be used.

## Remaining scope

This is verification of the repaired code and the locally available full
partitions, not certification of every source observation or of strategy
performance. Inspect fallback/stale counts, terminal coverage, trades and
rejected source rows before interpreting returns. SPY is the benchmark proxy
and begins on 1993-01-29; it is not an official total-return index history.
Raw licensed data was not modified or downloaded again. No Git push was
performed in this repair.

The CRSP delisting convention is documented in the provider's mapping:
https://www.crsp.org/wp-content/uploads/appendix/FlagType_MU.html
