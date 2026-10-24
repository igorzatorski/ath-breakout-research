# Trend Following on Futures

Independent Python research track for a diversified, long/short futures trend
portfolio. Created 2026-10-24 at the user's request. Conversation label:
"Trend following na futuresach".

Status: first market-level research prototype executed on 17 eligible markets
from 20 candidates, April 2016 through March 2024. Exact executable-chain,
historical liquidity/margin and delivery audits remain incomplete.

## Research question

Does a simple, shared time-series momentum signal add value across equity index,
government bond, currency and commodity futures when position risk, rolling,
costs and collateral are accounted for consistently?

## Start here

- [Research sequence and baseline draft](PLAN.md)
- [Candidate markets and selection rationale](UNIVERSE.md)
- [Data requirements and audit checklist](DATA_REQUIREMENTS.md)
- [Machine-readable candidate registry](universe.json)
- [Frozen v001 methodology](BASELINE_V001_PLAN.md)
- [Source and eligibility audit](DATA_AUDIT.md)
- [First results vs SPY](BASELINE_V001_RESULTS.md)
- [Methodology explained and missing-data follow-up](METHODOLOGY_EXPLAINED.md)
- [Fifty-market candidate preparation](UNIVERSE_50.md) and [registry](UNIVERSE_50.json)
- [Staged research protocol](RESEARCH_PROTOCOL_V002.md) and [experiment queue](EXPERIMENTS_V002.csv)

## Boundaries

This track owns `research/trend_following_futures/`,
`src/ath_breakout/research/trend_following_futures/`, `run/futures_*.py`,
`tests/research/test_futures_trend.py` and `outputs/trend_following_futures/`.
Raw public snapshots live under ignored `data/raw/futures/`.

```powershell
.venv/Scripts/python.exe run/futures_fetch.py
.venv/Scripts/python.exe -m run.futures_audit
.venv/Scripts/python.exe -m run.futures_backtest
```

ATH, Z-score and SHA research remain separate. Reuse verified infrastructure,
but do not inherit the SHA single-asset all-in/cash engine, ETF dividend logic,
positive-price restriction or commission assumptions as a futures engine.
SHA is a possible later signal comparator, not this project's primary signal.

## Investment-research relevance

This is a credible foundation for learning systematic portfolio management:
multiple markets, reproducible signals, risk allocation, execution and operations.
Trend following is an established strategy family. A familiar signal alone does
not establish a differentiated investment edge or readiness to manage outside
capital. Evaluate robustness, implementability and portfolio contribution before
considering a fund proposition.
