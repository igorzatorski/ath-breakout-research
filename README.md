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

1. Completed: Yahoo/CSV data layer and data-quality reporting
2. Completed: current and historical screener with transparent ranking
3. Completed: multi-asset portfolio backtest and interactive report
4. Next: cached historical signals and faster research iterations
5. Next: ranking, market-regime, entry, and exit research
6. Target: point-in-time Russell 3000/CRSP backtest

## Status

The current research MVP includes:

- local CSV and Yahoo Finance adapters;
- shared OHLCV validation and chronological sorting;
- raw adjusted-close, dividend, split, and Yahoo repair information;
- split-adjusted strategy prices kept separate from dividend-adjusted returns;
- SMA50, SMA100, SMA150, and SMA200 calculated from split-adjusted closes;
- NYSE-calendar freshness and missing-session quality checks;
- multi-security data identified by `security_id` and `ticker`;
- prior ATH and close breakout signal without using the current day's high;
- an IWV holdings snapshot used as a current Russell 3000 proxy universe;
- ranked current and historical screeners;
- a 33-position, next-open portfolio simulator with transaction costs;
- terminal statistics and an interactive Plotly backtest dashboard.

Install the project and its development tools once inside the active
environment:

```powershell
python -m pip install -e ".[dev]"
```

## Command cheat sheet

### WRDS/CRSP connection check

Install the optional WRDS client in the active environment:

```powershell
python -m pip install -e ".[wrds]"
```

On a private Windows account, the password can optionally be stored in Windows
Credential Manager. The prompt hides all entered characters and the password is
never written to the repository:

```powershell
python scripts/store_wrds_credential.py --username YOUR_WRDS_USERNAME
```

Remove it at any time with:

```powershell
python scripts/delete_wrds_credential.py --username YOUR_WRDS_USERNAME
```

Verify access to the quarterly CRSP Stock Version 2 daily table without
downloading licensed observations:

```powershell
python scripts/check_wrds_connection.py --username YOUR_WRDS_USERNAME
```

After the connection check succeeds, download the limited Apple 2025 sample
used to validate the Python data path:

```powershell
python scripts/download_wrds_apple_sample.py --username YOUR_WRDS_USERNAME
```

The sample is saved under `data/raw/wrds_samples/`, which is excluded from Git.
The script reports only its shape, date bounds, columns, and local path; it does
not print licensed price observations to the terminal.

Audit table and column metadata before changing the production data contract:

```powershell
python scripts/audit_wrds_crsp_schema.py --username YOUR_WRDS_USERNAME
```

The audit reads `information_schema` only. It stores no CRSP observations and
writes its local result under the Git-ignored `data/state/` directory.

Validate CRSP cumulative price and share adjustments around Apple's 2020 4:1
split:

```powershell
python scripts/validate_wrds_apple_split.py --username YOUR_WRDS_USERNAME
```

The script saves the local validation sample under the Git-ignored
`data/processed/wrds_samples/` directory and prints checks rather than price
observations.

Validate daily return components and both ordinary and non-ordinary
distribution handling:

```powershell
python scripts/validate_wrds_distributions.py --username YOUR_WRDS_USERNAME
```

Validate that a ticker change remains one security under a stable CRSP
`PERMNO`:

```powershell
python scripts/validate_wrds_ticker_history.py --username YOUR_WRDS_USERNAME
```

Validate an observed delisting return against the corresponding CRSP daily
return row:

```powershell
python scripts/validate_wrds_delisting.py --username YOUR_WRDS_USERNAME
```

Build one server-aggregated top-3,000 liquidity-universe prototype without
downloading its underlying daily panel:

```powershell
python scripts/validate_wrds_liquidity_universe.py --username YOUR_WRDS_USERNAME
```

Build or resume yearly partitions of all monthly universe snapshots:

```powershell
python scripts/build_wrds_crsp_universe_history.py --username YOUR_WRDS_USERNAME
```

Completed yearly partitions are reused automatically. The combined membership
history and its manifest remain under Git-ignored local data directories.

After the universe history is complete, download or resume yearly CRSP daily
partitions, the pre-1993 ATH seed, and detailed delisting outcomes:

```powershell
python -u scripts/download_wrds_crsp_daily_history.py --username YOUR_WRDS_USERNAME
```

Check the current coverage boundary before running a backtest or screener:

```powershell
python scripts/check_wrds_crsp_coverage.py --username YOUR_WRDS_USERNAME
```

Quarterly CRSP is the authoritative historical source. A requested-date
screener is blocked when the latest CRSP session predates that date; current
signals require a separately validated current-market source.

Audit accessible LSEG-related schemas before selecting a current-market source:

```powershell
python scripts/audit_wrds_lseg_access.py --username YOUR_WRDS_USERNAME
```

The 2026-09-05 audit found no accessible tables in `tr_ds`; the account's other
LSEG-related libraries do not supply the required current daily OHLC history.
The live screener therefore still needs a separate current-market provider.

The scripts first check Windows Credential Manager and otherwise let the WRDS
client request the account password interactively. A connection may trigger a
Duo Mobile push. Do not store the password in this repository. Raw licensed
CRSP data must remain local and be handled according to the WRDS and
institutional terms of use.

### Portfolio backtest

Run the complete ranked multi-asset portfolio over the latest five years:

```powershell
python scripts/run_portfolio_backtest.py
```

When this script is launched with the editor's Run button and no date options,
the terminal asks for the start and end dates. Press Enter at both prompts to
keep the default latest-five-year period.

The terminal prints full equity, S&P 500, drawdown, and exposure charts plus
statistics and recent trades. The command also opens an interactive dashboard.
By default the portfolio holds at most 33 positions, targets 3% of current
equity for each new position, and leaves unused capital in cash. Signals known
at a session close execute at the next available open. Candidates compete for
available slots by setup score and then breakout-quality score.

Select an exact period or change transparent assumptions when needed:

```powershell
python scripts/run_portfolio_backtest.py --start 2021-01-01 --end 2025-12-31
python scripts/run_portfolio_backtest.py --capital 50000 --cost-bps 15
```

`--start` is the first session on which the portfolio may accept a signal and
measure performance. Earlier stored history is still used to calculate prior
ATH, moving averages, consolidation features, and ranking. For example, to
measure from 2017 while retaining all earlier warm-up history:

```powershell
python scripts/run_portfolio_backtest.py --start 2017-01-01 --min-setup-score 70
```

An optional ranking floor can be tested with `--min-setup-score`. The default
is `0`, because the first five-year diagnostic did not show that a higher
absolute score improved returns; this option is a research control, not a
validated source of alpha.

Use `--no-open` to save the interactive HTML dashboard without opening it.
Results are stored under `outputs/backtests/portfolio/<START>_<END>/`.

### Daily data pipeline

The daily data workflow has one entry point. It saves or reuses today's IWV
snapshot, updates every known security through the latest available session,
rebuilds processed features, and writes the quality report:

```powershell
python scripts/run_data_pipeline.py
```

Use this command for the normal daily update. Existing securities receive only
a short overlapping update; a newly discovered security receives its complete
available history.

After the NYSE closes, Yahoo may publish its daily bar with a delay. The normal
pipeline checks SPY first and waits for up to 60 minutes instead of silently
building a stale screener. It checks every two minutes. Both limits can be
changed, for example:

```powershell
python scripts/run_data_pipeline.py --max-wait-minutes 30 --poll-seconds 60
```

In automatic mode the pipeline checks the NYSE calendar and market-close time.
Before or during the US session it uses the previous completed session; after
the close and a 15-minute publication delay it includes the session that just
finished. A specific completed session can be selected manually when needed:

```powershell
python scripts/run_data_pipeline.py --as-of 2026-08-24
```

Use the manual date only for a completed NYSE session. This is useful when you
want the data, report, and screener to represent one exact market close.

Emergency/maintenance command: redownload the complete available Yahoo history
for every security in the registry and rebuild all processed files:

```powershell
python scripts/run_data_pipeline.py --full-refresh
```

The full refresh is intentionally not the everyday command. It may take a long
time and make many Yahoo requests. A security is replaced only after its new
history downloads and validates successfully; an unsuccessful download keeps
the existing Parquet files. The full refresh also tries securities currently
waiting on the normal retry schedule.

Both options can be combined to stop the rebuilt history at a selected session:

```powershell
python scripts/run_data_pipeline.py --full-refresh --as-of 2026-08-24
```

Show all available pipeline options without downloading anything:

```powershell
python scripts/run_data_pipeline.py --help
```

Yahoo treats its end date as exclusive, so the downloader automatically asks
through the day after the selected session. The same selected date is written
to the quality report and later used by the screener.

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

The current development stage includes the screener and transparent candidate
ranking. The IWV
snapshot contains current ETF holdings, not historical point-in-time Russell
3000 membership, so it must not be used to claim a survivorship-bias-free
historical backtest.

Run the first current-universe ATH screener after the daily data pipeline:

```powershell
python scripts/run_screener.py
```

Recreate the same screener at a completed historical NYSE session:

```powershell
python scripts/run_historical_screener.py 2023-05-25
```

When `run_historical_screener.py` is launched with the editor's Run button and
no command-line date, it asks for the session in the terminal.

The historical command truncates every security and the IWV benchmark to the
selected close before calculating ATH, moving averages, filters, and scores.
It writes a separate result to
`outputs/screening/history/screener_YYYY-MM-DD.csv`. The price features are
therefore point-in-time, but the MVP still scans today's IWV constituent list.
Historical results retain survivorship bias and are intended for inspecting
the mechanics and candidate ranking, not for claiming reliable performance.

The terminal shows the completed market session represented by the scan and a
timestamped progress bar followed by the ranking model, fresh breakouts, and
the highest-ranked base-ready watchlist. The
complete ranking-ready table is saved in
`outputs/screening/` with the full feature and score breakdown. The adaptive
consolidation measurement looks back through at most 60
sessions while closes remain within 10% of the prior ATH. It reports the base
duration and actual high-low depth, and excludes a breakout day from its own
base measurement. The basic trend filter requires the close above SMA200 and
an ordered SMA50/SMA100/SMA150 structure; SMA150 does not have to be above
SMA200. A 20% overnight-gap limit removes strongly event-driven charts while
retaining ordinary earnings gaps. These transparent
components are also used by the transparent candidate ranking. Smooth-trend
filters additionally require at least a 0.5% rise in SMA200 over 20 sessions,
at least 40 consecutive sessions above SMA200, no close-to-close drawdown
deeper than 30% during the latest 252 sessions, and no more than
15% extension above SMA50, and ATR20 between 0.5% and 5% of price. A valid base
must last at least 20 sessions, remain no deeper than 15%, follow at least 20
sessions without another close breakout, and pass at least
three of four construction checks: contracting ATR, contracting recent range,
rising lows, and drying volume. The pipeline also maintains IWV price history
so the ranking can compare 3-, 6-, and 12-month relative performance with the
universe proxy. The 0-100 setup ranking separately reports base shape (20),
base maturity (10), trend (20), relative strength (20), contraction (15), and
ATH readiness (15). Liquidity remains a hard eligibility filter rather than a
source of ranking points. A separate 0-100 breakout-quality score uses volume
confirmation (40), closing location within the session (35), and extension
above ATH (25), and is calculated only after a breakout. The broad
watchlist remains in the CSV, while the terminal shows every qualified fresh
breakout and the ten highest-ranked `base_ready` candidates. It does not issue
a `BUY` recommendation. Exact intraday ATH age remains available as a
diagnostic, but it is not a hard rule because one marginally higher wick can
otherwise reset an already mature consolidation.
