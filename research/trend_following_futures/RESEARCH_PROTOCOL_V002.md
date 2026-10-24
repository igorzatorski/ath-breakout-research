# Futures trend research: staged protocol for v002

Prepared 2026-10-24 before inspecting any 50-market portfolio performance.
Goal: determine whether a simple shared trend signal produces useful net,
risk-controlled returns and portfolio diversification. A high in-sample CAGR
or a large symbol count is not sufficient evidence.

## Research roles and history boundary

Keep the existing 17-market v001 result, source and code fingerprints intact.
Its April 2016-March 2024 performance has been inspected and is development
evidence. That same history cannot later be renamed independent OOS.

Prepare 50 candidates in UNIVERSE_50.json. Existence of source CSVs is only
feasibility evidence. Current provider metadata can mix standard, mini and micro
units or stale descriptions; verify mappings instead of assuming exchange roots.
Eligibility is decided from data/execution requirements, not profitable returns.

Primary universe comparison window: the existing v001 anchor 2016-03-31 through
2024-03-28, with initial execution 2016-04-01. A candidate needs sufficient prior
history for the signal/risk estimator. Do not fabricate early history, silently
shorten the test to suit new contracts or remove markets after poor results.
If adequate data cannot be obtained, report eligible counts and limitations.
The 50-target label is a candidate target, not a requirement to force all rows in.

Reserve data from 2024-04-01 onward as prospective validation for the frozen
strategy, if a suitable source becomes available. Do not inspect that strategy's
validation performance while choosing the development specification. A source
ending in March 2024 does not provide this validation. Rolling historical
subperiod diagnostics are still development checks, not untouched confirmation.

## 1. Data gate: can the accounting be trusted?

Audit genuine session closures separately from missing observations of the
chosen maturity. Repair using same-contract source data or rebuild a documented
causal chain; do not plug in another maturity without its roll adjustment.
Reconcile per-contract changes, roll dates, units and costs on hand-worked cases.

Add multi-currency P&L and fee conversion before any 50-market simulation.
Source metadata contains non-USD contracts; dollar contract volatility must not
be confused with local-currency volatility. Align FX timestamps causally.
Handle market-specific holidays, price limits, delivery restrictions and missing
or zero cost estimates explicitly. Treat venue-specific price anomalies as audit
questions, not automatic profitable opportunities.

Required evidence: a per-market coverage/eligibility ledger, source/code hashes,
hand-calculated long/short and roll/FX examples, prefix-causality tests, and full
daily cash/P&L reconciliation. Passing this gate establishes implementation
credibility under the documented assumptions, not signal alpha.

## 2. Universe question: does breadth help this fixed strategy?

First reproduce v001. Then run validated 17-market and expanded eligible-market
portfolios using identical 12-month direction, monthly timing, risk method,
cost assumptions and dates. Apply any necessary data/engine corrections to both
arms; retain old v001 as a separately labeled historical result.

Primary measures: net Sharpe and maximum drawdown, with realized volatility and
net CAGR alongside them. Context: correlation with SPY, sector exposure, risk
concentration, trading/roll costs and market/sector P&L. Report all eligible and
excluded markets. More listed markets need not mean more independent exposures.

## 3. Signal question: does direction add value?

Use the same diversified universe/risk/cost framework for time-series momentum
and an always-long futures control. SPY full exposure is investment context;
the lagged volatility-targeted SPY comparator is an approximate risk comparator.
Report collateral interest consistently in every arm and show sensitivity to
the zero-cash-yield assumption before making total-return claims.

Test only the registered horizon alternatives after the universe comparison.
Keep one shared specification for all markets. Store every outcome; never assign
each market its own best historical horizon in the initial study.

## 4. Risk and implementation questions

One risk-estimation change at a time, with signal/universe held fixed. Examine
predicted vs realized volatility, leverage, concentration and emergency actions.
Stress execution costs at twice baseline; this is a fragility check, not proof
that baseline costs are accurate. Report exact changes in assumptions.

Win rate is descriptive. Trend following can rely on relatively few large gains;
require payoff distribution and drawdown duration alongside win rate. Check
dependence on individual markets/episodes, but do not demand that every market
or every year be profitable. Concentration prompts investigation, not automatic
deletion of the offending market.

## 5. How to interpret results

Use these evidence labels, not a binary "works/does not work" from one run:

| Label | Meaning | Next action |
| --- | --- | --- |
| Data/implementation failure | Missing quotes, unexplained P&L, timing leakage, unsupported currency/roll model | Repair; do not interpret strategy performance |
| Fragile historical result | Benefit vanishes under small justified changes, costs or concentration diagnostics | Retain results; investigate mechanism; do not adopt |
| Exploratory evidence | Reproducible net results, reasonable sensitivity and contribution across observations, with uncertainty still material | Freeze specification for validation |
| Inconclusive validation | Insufficient duration/independent trend episodes or uncertainty spans no benefit | Collect more evidence; no profitability claim |
| Supported on the tested validation | Frozen design performs usefully on later unseen data after costs, with uncertainty and limits reported | Consider paper execution and operational tests |

Do not invent a universal Sharpe cutoff or claim statistical significance from
400 overlapping parameter trials. For consequential performance differences,
report dependence-aware uncertainty (e.g. jointly resampled calendar blocks),
and separate predetermined comparisons from hindsight-selected maxima.
An interval spanning zero means inconclusive evidence, not demonstrated equality.

## Work in small increments

The immediate deliverable is the 50-candidate registry and a clear readiness
list, followed by data/calendar/FX repairs. Once that gate is passed, run the
universe comparison first and explain it before expanding the test queue.
The registered queue is ordered; it is not permission to execute every possible
combination of all settings or to optimize a large search grid.
