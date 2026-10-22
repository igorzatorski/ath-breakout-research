# Z-score index signal study v001

Frozen before running results, 2026-10-22. Separate from ATH research.

- Source: existing local Yahoo SPY daily parquet; SPY is an investable S&P 500 proxy, not the cash index or a futures/CFD contract. No source refresh or credentialed access.
- Primary: 30-session close-price Z-score <= -1. Sensitivity: 60 sessions, same threshold. No parameter selection after results.
- Z(t) = (close(t) - rolling mean(close, L)) / rolling sample standard deviation(close, L), including t; ddof=1. Price-level dispersion, not return volatility or a Gaussian probability.
- Signal observed after close t. Entry at open t+1, exit at close t+5 (five trading sessions). Adjust OHLC by adj_close/close for dividend-adjusted return proxy. Also report raw price return.
- Common eligible dates for both windows; complete five-session forward windows only. Compare conditional forward returns against all eligible forward windows, not buy-and-hold CAGR.
- Report all qualifying days and a secondary non-overlapping implementation: first eligible signal, ignore signals through exit close; next entry strictly after exit. No stops, leverage, stock selection or portfolio optimization.
- Report count, mean, median, win rate, tail quantiles, worst return, 20 bps round-trip cost sensitivity, and subperiods 1993-2009 / 2010-2017 / 2018-end. Historical splits are diagnostics, not untouched out-of-sample evidence.
- Moving-block bootstrap over common signal dates, 20-session blocks, 2,000 draws, seed 42; paired conditional-minus-unconditional mean difference and conditional mean 95% intervals. Overlapping windows and persistent signals are not independent trades. Bootstrap is approximate, not causal evidence.
- Save source hash, date coverage, settings, event ledger, summary tables and English results. Validate timing, prefix invariance and independent formula calculations.

## User-requested extension: threshold -2

Declared before the extension run on 2026-10-22, after observing -1 results.
Repeat the same study with Z <= -2 for both windows, preserving all dates,
execution, cost assumptions and statistics. Save separately as v002_minus2;
do not replace the -1 baseline. Retain both 20- and 60-session bootstrap blocks.
This is an additional exploratory comparison, not a new independent validation
sample; confidence intervals are not adjusted for multiple comparisons.
Run: `.venv/Scripts/python.exe scripts/research/study_zscore.py --threshold -2`.

## Nasdaq-100 replication

Declared before inspecting QQQ signal results, 2026-10-22. Use public Yahoo
QQQ adjusted daily OHLC, 1999-03-10 to 2026-10-05, fetched on 2026-10-22.
QQQ proxies Nasdaq-100, not Nasdaq Composite. Repeat the same four combinations
(30/60 sessions, thresholds -1/-2), execution rules and bootstrap settings.
Compare SPY on the exact same eligible signal dates, starting after QQQ's
60-session warmup, as well as the previously reported full SPY history.
No new threshold optimization or stops. This is cross-market replication;
correlated equity indices do not constitute independent validation.
