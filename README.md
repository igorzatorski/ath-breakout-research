# ATH Breakout Systematic

A modular Python platform for systematic equity research, stock screening,
portfolio management, and backtesting of an ATH breakout/momentum strategy in
the US equity market.

## Project objective

The final system should use a point-in-time Russell 3000 universe, include
delisted securities, and support research without survivorship bias or
look-ahead bias. During the MVP stage, data may come from local CSV files or
Yahoo Finance. Results obtained from the current index constituents and Yahoo
Finance data must not be treated as a reliable historical Russell 3000
backtest.

The core strategy rules and open decisions are documented in
[STRATEGY_SPEC.md](STRATEGY_SPEC.md).

## Development roadmap

1. Data layer and data/universe validation
2. Screener and candidate ranking
3. Simple backtest
4. Portfolio Manager
5. Full point-in-time backtest
6. Position sizing and research
7. Dashboard

## Status

The data pipeline required before building the first screener is available:

- local CSV and Yahoo Finance adapters;
- shared OHLCV validation and chronological sorting;
- raw adjusted-close, dividend, split, and Yahoo repair information;
- split-adjusted strategy prices kept separate from dividend-adjusted returns;
- SMA50, SMA100, and SMA150 calculated from split-adjusted closes;
- NYSE-calendar freshness and missing-session quality checks;
- multi-security data identified by `security_id` and `ticker`;
- prior ATH and close breakout signal without using the current day's high;
- an IWV holdings snapshot used as a current Russell 3000 proxy universe.

Install the project and its development tools once inside the active
environment:

```powershell
python -m pip install -e ".[dev]"
```

The daily data workflow has one entry point. It saves or reuses today's IWV
snapshot, updates every known security through the latest available session,
rebuilds processed features, and writes the quality report:

```powershell
python scripts/run_data_pipeline.py
```

Maintenance command: rebuild every processed file from the locally stored raw
Parquet files without downloading market data:

```powershell
python scripts/maintenance/rebuild_processed_data.py
```

Example command: process the small tracked CSV without contacting external
services:

```powershell
python examples/process_local_csv.py
```

The updater stores one raw Parquet file and one processed Parquet file per
security. Existing securities receive a short overlapping Yahoo download,
duplicate sessions are replaced, and the complete validated history is
processed again. Securities that leave the current universe remain in the
security registry and their prices continue to update, but they are marked as
outside the current universe and will not be used by the current screener.

Yahoo historical OHLC is already adjusted for stock splits but not cash
dividends. The pipeline records that source convention explicitly, preserves
`adj_close`, dividends, and split events in raw Parquet, and calculates ATH
from `split_adj_high` and `split_adj_close`. Dividend-adjusted prices are not
used to generate the price-breakout signal. Existing raw files created with
the older schema request a full-history refresh on their next update. A
successful full refresh replaces the old Parquet completely, so placeholder
corporate-action values from the legacy schema cannot survive the migration.

Every completed update writes `data/state/data_quality_report.csv`. It records
freshness, missing NYSE sessions, history bounds, corporate-action counts, and
update failures for each attempted security.

Download failures are remembered between runs. A failed ticker is retried
individually immediately, then on the next daily run. After three consecutive
failed runs it moves to a weekly retry schedule instead of repeatedly querying
Yahoo every day. A later successful download automatically returns it to the
active state and clears its failure counter. The manifest and quality report
show the error category, failure count, last failure date, and next retry date.

The next development stage is the screener and candidate ranking. The IWV
snapshot contains current ETF holdings, not historical point-in-time Russell
3000 membership, so it must not be used to claim a survivorship-bias-free
historical backtest.
