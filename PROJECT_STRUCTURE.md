# Project structure and data-layer boundary

## User-facing commands

Only three Python entry points are visible in `scripts/`:

- `run_screener.py`: date prompt; Enter refreshes Yahoo and screens the latest completed session.
- `run_period_screener.py`: CRSP breakout signals in an inclusive date range, with nominal next-session open and explicit unavailable entries.
- `run_backtest.py`: CRSP portfolio simulation against SPY.

Acquisition, validation and compatibility tools live in `scripts/maintenance/`
and `scripts/internal/`. This layout does not depend on editor hiding rules.

## `src/ath_breakout` ownership

| Package | Role | Keep? |
| --- | --- | --- |
| `strategy/` | ATH and moving-average rules | Yes; shared by every source |
| `screening/` | snapshots, ranking, output | Yes; live and historical screens |
| `backtesting/portfolio.py` | portfolio accounting | Yes; source-neutral engine |
| `backtesting/crsp_inputs.py` | PIT CRSP loader | Yes; historical research |
| `backtesting/reporting.py` | reports and dashboard | Yes |
| `data/adapters/yfinance.py` | current EOD acquisition | Yes; live screener |
| `data/adapters/crsp*.py` | WRDS acquisition and normalization | Yes |
| `data/adapters/ishares.py` | current IWV proxy snapshot | Yes; live universe |
| `data/processing.py` | shared feature recalculation | Yes |
| `data/crsp_processing.py` | partitioned CRSP features | Yes |
| `data/preparation.py`, `validation.py` | canonical checks | Yes |
| `data/market_update.py` | incremental Yahoo updater | Yes; live screener |
| `data/quality.py`, `crsp_quality.py` | data-quality reports | Yes |
| `data/storage.py`, `security_registry.py`, `universe*.py` | persistence and universe state | Yes |
| `data/market_calendar.py` | NYSE session rules | Yes |
| `data/retry_policy.py` | Yahoo retry behavior | Yes |
| `data/wrds_credentials.py` | local credential lookup | Yes; no credentials in Git |
| `data/adjustments.py` | Yahoo-compatible adjusted fields | Yes for Yahoo; CRSP uses its own adapter |
| `data/crsp_adjustments.py`, `crsp_returns.py`, `crsp_coverage.py` | CRSP-specific factors/returns/audit | Yes |

## What was removed conceptually

The old Yahoo historical backtest is no longer the research path. The legacy
`scripts/maintenance/run_portfolio_backtest.py` and `prepare_historical_inputs` remain
temporarily for compatibility and regression tests, but new research must use
`run_crsp_portfolio_backtest.py`. They are isolated in `scripts/maintenance/`; their regression tests remain.

Yahoo itself is not obsolete: it is the inexpensive live EOD feed. CRSP remains
the historical source. Raw source files are never merged by ticker; the shared
strategy layer receives each source's canonical features.

## Data flow

```text
Yahoo -> market_update -> processed/features -> run_daily_screen
CRSP  -> strategy_by_year -> PIT loader -> CRSP portfolio backtest
```

The live screen is a ranking of current candidates. Sell decisions for owned
positions require a separate holdings ledger and entry-date/exit-state logic;
the screener does not invent those orders.
