# ATH Breakout Systematic

A point-in-time systematic-equity research platform for studying all-time-high
(ATH) breakouts in US stocks. It separates licensed historical research data
from the current end-of-day screening feed and applies the same transparent
signal definitions to both paths.

> **Research status:** the platform produces CRSP portfolio backtests and
> current Yahoo Finance screens. The strategy has not completed robust
> out-of-sample validation, paper trading, or broker integration and is not yet
> a production trading system.

## Current status

### Implemented and tested

- reproducible Python 3.11 environment managed by `uv` and `uv.lock`;
- WRDS credentials stored outside the repository in Windows Credential Manager;
- resumable WRDS/CRSP extraction into yearly local Parquet partitions;
- CRSP history beginning in 1993, stable PERMNO identity, ticker history,
  corporate actions, distributions, delisting returns, and a pre-period ATH seed;
- monthly point-in-time liquidity universe of approximately 3,000 securities;
- strategy-ready partitions that carry ATH and moving-average state across years;
- incremental Yahoo Finance end-of-day pipeline for the current screener;
- shared OHLCV validation and strategy-feature definitions;
- one-day screener with ranking and period screener with signal date and
  next-session nominal opening price;
- multi-asset CRSP backtester with next-session execution, costs, position
  limits, delisting exits, SPY benchmark, CSV results, terminal report, and an
  interactive Plotly dashboard;
- compact strategy/benchmark statistics including volatility, Sharpe, drawdown,
  beta, alpha, tracking error, information ratio, Sortino, and Calmar;
- dashboard panels for normalized log-scale growth, both drawdowns, exposure,
  rolling 21-session volatility, and monthly/yearly strategy-benchmark returns;
- validation of manifests, source fingerprints, Parquet row counts, and actual
  partition date bounds;
- 235 passing automated tests at the latest local verification.

The full CRSP preparation stage was reduced from about 24 minutes to about
9 minutes on a cold run on the development machine. A persistent prepared-input
cache reduces an otherwise identical full-period rerun to about 34 seconds.
Exact regression comparisons confirmed that the optimizations did not change
candidates, events, trades, the equity curve, or annual performance outputs.

### Current limitations

- local CRSP coverage currently ends on 2026-06-30 and is not a live feed;
- the live Yahoo/IWV universe differs from the historical CRSP liquidity universe;
- CRSP and Yahoo histories are not concatenated by ticker because their
  identities and adjustment bases differ;
- Yahoo Finance is a best-effort personal-use feed, not institutional market data;
- the latest full baseline needs a focused review of its 34 stale-position
  sessions before it can be frozen;
- ranking weights and entry/exit filters are not validated out of sample;
- there is no holdings ledger, paper-trading process, broker connection, or
  automated execution;
- outputs are research results, not buy or sell recommendations.

## User-facing commands

The normal workflow has three entry points:

```powershell
# Latest screen, or enter a completed historical date when prompted
python scripts/run_screener.py

# CRSP breakouts between two dates, with next-session entry prices
python scripts/run_period_screener.py

# Point-in-time CRSP portfolio backtest against SPY
python scripts/run_backtest.py
```

Press Enter in `run_backtest.py` to use the first supported SPY/CRSP date and
the end date recorded by the local CRSP manifest. Acquisition, rebuilding,
auditing, and compatibility commands live under `scripts/maintenance/` and
`scripts/internal/`.

The first run for a period stores prepared point-in-time prices and ranked
signals under the ignored `data/cache/backtesting/` directory. Later runs with
the same data, dates, and signal definition reuse that cache. Portfolio settings
such as capital, costs, weights, and position limits can change without
rebuilding signals. Changes to CRSP partitions, universe or delisting files,
benchmark observations, feature code, dates, or signal-loader code create a new
cache key automatically. To deliberately rebuild the same key, run:

```powershell
python scripts/run_backtest.py --start 1993-01-29 --end 2026-06-30 --rebuild-cache
```

## Environment

Create or synchronize the repository-local environment:

```powershell
uv sync --all-extras
```

Run commands through `uv run`:

```powershell
uv run pytest -q
uv run python scripts/run_backtest.py
```

Alternatively, activate the environment on Windows:

```powershell
.venv\Scripts\activate.bat
```

The environment, downloaded data, generated outputs, passwords, and local state
are excluded from Git.

## Data architecture

```text
WRDS/CRSP
  -> yearly raw Parquet partitions
  -> schema, coverage, identity, return, and delisting audits
  -> yearly strategy-ready partitions
  -> point-in-time universe and candidate loader
  -> portfolio backtester

Yahoo Finance + current IWV holdings
  -> incremental current-data update
  -> canonical strategy features and quality report
  -> latest one-day screener
```

CRSP is authoritative for historical research. Yahoo Finance supplies current
end-of-day observations for the live personal screener. Their raw histories
remain separate. See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for module
ownership.

## Strategy and portfolio baseline

The signal is a close above the true prior all-history high. The current day is
excluded from the prior ATH, and an accepted close signal executes no earlier
than the next available session open.

Features include trend structure and persistence, nominal dollar liquidity,
ATR, gaps, extension, drawdown, consolidation duration and depth, contraction,
rising lows, volume dry-up, relative strength, and breakout cooldown. The
portfolio currently targets 3% per new position, holds at most 33 positions,
charges 10 basis points per side, and applies the configured moving-average exit
at the next tradable open. These are research assumptions, not optimized rules.

## Data maintenance

The quarterly WRDS refresh is run from the maintenance layer:

```powershell
python scripts/maintenance/update_data_layer.py --username YOUR_WRDS_USERNAME
```

It downloads missing coverage, rebuilds affected strategy partitions, and
validates the local layer. Licensed observations remain in ignored `data/`
directories and must be handled under the applicable WRDS and institutional
terms.

The current Yahoo feed refreshes automatically when the latest screener runs.
It downloads the required overlap for existing securities, fuller history for
new securities, and records freshness and failures in the local quality report.

## Backtest outputs

Each CRSP run is written beneath:

```text
outputs/backtests/crsp/<START>_<END>/run_<TIMESTAMP>/
```

It contains `summary.csv`, `equity_curve.csv`, `trades.csv`, `events.csv`,
`ranked_candidates.csv`, `annual_performance.csv`, and
`interactive_dashboard.html`. The current valid
full-period run covers 1993-01-29 through 2026-06-30. Runs extending beyond CRSP
coverage, or predating accounting version 2, must not be used for conclusions.

## Development roadmap

### 1. Freeze a trustworthy baseline — next

- explain or eliminate every stale-position session;
- manually reconcile representative entries, exits, delistings, returns, and costs;
- add experiment names, parameter snapshots, data fingerprints, Git commit hash,
  and elapsed time to every run;
- extend dashboard reporting with rolling performance, turnover, and deeper
  trade-distribution diagnostics.

### 2. Build the research layer

- benchmark and refine the persistent prepared-input cache as the research
  workload grows;
- define immutable train, validation, and final out-of-sample periods;
- add walk-forward and market-regime evaluation;
- analyze feature deciles and forward-return distributions;
- run one-factor-at-a-time and ablation tests;
- use bootstrap confidence intervals and multiple-testing controls;
- test realistic fees, slippage, liquidity, and capacity.

### 3. Research portfolio rules

- compare SMA, ATR, trailing, time, and relative-strength exits while holding
  the entry sample fixed;
- optimize ranking only after individual features prove stable;
- compare equal weight, volatility scaling, position limits, sector caps, and
  portfolio risk controls;
- develop any SPY/QQQ mean-reversion strategy as a separate module and then
  measure its diversification benefit against the ATH trend strategy.

### 4. Forward test and paper trade

- add a persistent holdings and cash ledger;
- generate deterministic proposed orders from the latest completed session;
- reconcile assumed and realized fills;
- run the daily workflow unattended with monitoring and failure alerts;
- paper trade before considering live capital.

### 5. Application and broker integration

- build a Streamlit control panel for data health, candidates, holdings, orders,
  exposure, performance, and audit history;
- connect to IBKR in read-only mode first;
- add manually approved paper orders, idempotency, risk limits, and a kill switch;
- permit automated execution only after stable forward-test evidence and
  operational controls exist.

## Research discipline

Parameter combinations must not be selected from the same period used to report
their performance. Statistical significance alone is insufficient: findings
must remain economically meaningful across regimes, costs, neighboring
parameters, and untouched out-of-sample data. The final holdout should remain
unseen until the research process and decision rules are frozen.
