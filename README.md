# ATH Breakout Research

A modular Python platform for researching all-time-high breakouts in US equities.
The Data Layer and portfolio engine exist. The current focus is an **unfiltered
ATH signal study**, without portfolio, stop or filter tuning. The conditional
1994-2026 study is implemented; see [results and limitations](research/ath/ATH_SIGNAL_STUDY_RESULTS.md).

Start with [the working guide](docs/START_HERE.md),
[project status](docs/PROJECT_STATUS.md) and
[the research protocol](research/ath/RESEARCH_PLAN.md).

## Independent research tracks

- [Trend Following on Futures](research/trend_following_futures/README.md):
  separate long/short time-series momentum research; first 17-market research
  prototype and SPY comparison, with explicit data/execution limitations.
- [Smoothed Heikin Ashi](research/smoothed_heikin_ashi/README.md): separate Python
  indicator and trend-following research; first SPY EMA(10,10) baseline available.
- [Index mean reversion](research/zscore/README.md): separate SPY / QQQ studies.

## Language convention

All quant research artifacts are maintained in English: Python code, comments,
docstrings, messages, research notes, Markdown documentation, generated reports,
and related Notion pages. Conversation language is independent of this convention.

## Run files

Open a file in `run/` and click **Run Python File** in VS Code. Every task uses
this project's `.venv` and working directory automatically. No activation
script, extra PowerShell window or execution-policy change is required.

| File | Purpose |
| --- | --- |
| `run/venv.py` | Create/synchronize the locked environment and verify dependencies |
| `run/check_data.py` | Read-only local CRSP readiness check; start here tomorrow |
| `run/update_data.py` | Check latest available CRSP date and update missing coverage |
| `run/update_yahoo.py` | Update the separate Yahoo current-universe dataset |
| `run/screen.py` | Existing current/date-selected ATH screener |
| `run/screen_period.py` | Existing historical CRSP range screener |
| `run/backtest.py` | Existing CRSP portfolio reference configuration |
| `run/compare_backtests.py` | Compare saved results without rerunning simulations |

Use Python 3.11+ and [uv](https://docs.astral.sh/uv/). `run/venv.py` runs
`uv sync --all-extras --locked`, including WRDS, Yahoo repair (`scikit-learn`)
and development dependencies. `--check` verifies without installing.
VS Code defaults to `.venv/Scripts/python.exe`; select this interpreter if the
workspace already has a different saved interpreter. Recreate the old terminal
once if an earlier launcher left a nested shell running.

Equivalent Windows terminal commands, with no activation needed:

```powershell
.\.venv\Scripts\python.exe run\venv.py --check
.\.venv\Scripts\python.exe run\check_data.py
.\.venv\Scripts\python.exe run\backtest.py --skip-crsp-check --start 2024-01-02 --end 2024-12-31 --no-open
.\.venv\Scripts\python.exe run\screen.py --as-of 2024-01-02 --skip-crsp-check
```

For the first installation without `.venv`, run `uv sync --all-extras --locked`
or execute `run/venv.py` with an available Python interpreter.

## Organization

```text
run/                    simple user launchers; no strategy logic
scripts/
  data/                 acquisition, validation, credentials, maintenance
  screening/            current and historical screen commands
  backtesting/          existing CRSP and Yahoo portfolio commands
  research/             readiness and saved-run comparison commands
src/ath_breakout/        reusable Data Layer, strategy, screening and portfolio code
research/ath/           research protocol, planned baseline and trial registry
docs/                   working guide, status, architecture and data contracts
tests/                  infrastructure and accounting checks
data/                   local observations, processed artifacts, state and caches
outputs/                generated runs and comparisons; excluded from Git
archive/                previous experiments and relocation indexes
```

Detailed ownership and naming: [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).
All active code, documentation and report messages use English.

## Data and automatic refresh

The verified local CRSP coverage is 1993-01-01 through 2026-06-30. Availability
is checked against WRDS rather than inferred from a calendar or release schedule.
Historical membership uses a monthly liquidity selection of approximately
3,000 stocks, not the official Russell 3000. PERMNO is the historical identity.
Yahoo/IWV serves the separate current screener; the two sources are not joined
by ticker. CRSP returns include distributions and delisting accounting.

The screen and backtest commands first check CRSP availability. Complete,
validated local coverage is skipped. New coverage is acquired incrementally;
stale derived artifacts can be rebuilt without redownloading current raw data.
The current screener separately updates Yahoo data. `--skip-crsp-check` means
explicit local-only CRSP use; it does not disable a live screener's Yahoo update.

Supply `--wrds-username YOUR_USERNAME` to screen/backtest commands, or
`--username YOUR_USERNAME` to `run/update_data.py`. The username can also come
from `WRDS_USERNAME` or ignored local settings. Passwords use the credential
manager/WRDS authentication; they are never saved in run manifests.
Connection failures stop the check. Deliberate vendor revision refreshes use
an explicit downloader overwrite; automatic extension does not promise to
find historical vendor corrections outside requested coverage.

## Saved results

Each report gets a unique UTC run directory. Repeated runs never overwrite
previous results. `manifest.json` records configuration, code and lock hashes,
source-manifest/benchmark hashes, artifact hashes, timestamps and save status.
The code hash identifies working-tree changes even before committing.

```text
outputs/
  backtests/reference_ath_v001/<run_id>/
  backtests/yahoo_current_universe_reference/<run_id>/
  screens/<source_and_mode>/<run_id>/
  comparisons/backtests/<run_id>/
  research/ath/<study_id>/<run_id>/       future signal studies
```

Backtests save summary, equity, annual performance, trades, events, candidates
and an interactive SPY growth/drawdown dashboard. Metrics include CAGR,
volatility, drawdown, Sharpe, Sortino, Calmar, alpha with HAC uncertainty,
beta, exposure and costs. Sharpe/Sortino/alpha currently assume a zero
risk-free rate. SPY is an S&P 500 total-return proxy, not the official index.

Run `run/compare_backtests.py` and paste directories separated by `|`, or pass
`--runs DIR_A DIR_B`. It exports every summary column, normalized growth and
drawdown charts, and warnings for differing periods, calendars, inputs,
accounting or diagnostic subsets. Changed artifact hashes and incomplete runs
are rejected. No automatic winner or alpha claim is produced.

## Research boundary and verification

The existing screener/backtest has prior strategy filters and scoring. It is a
reference implementation, **not** the planned unfiltered signal baseline.
The new standalone signal study and matched controls are implemented, with
explicit historical-quality selection and uncertainty; they do not establish alpha.
Follow the protocol: signal baseline, individual features, simple portfolio,
construction/risk changes, then chronological and forward validation.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src scripts run tests
uv lock --check
git diff --check
```

CI runs tests/lint on Windows and Linux. Live WRDS/Yahoo downloads are not CI
tests. Market data, generated outputs, caches, credentials and archive payloads
stay local; code, contracts, protocol and archive indexes are versioned.
See [the archive guide](archive/README.md) before restoring old experiments.

## Yahoo download hardening — 2026-10-06

The updater checks revisions in overlapping OHLC, adjusted close, volume and
corporate actions (within numerical tolerance). A detected revision or new
split/dividend triggers a full-history request for that ticker before replacing
its stored basis. Failed or boundary-truncated revision downloads preserve the
previous raw and processed files. Vendor revisions outside the overlap without
a newly observed corporate action can still go undetected; use explicit full
refresh when a deliberate complete revision check is needed.

Yahoo responses are normalized across flat and both MultiIndex layouts, with
local session dates, exact required-session checks, request bounds, duplicate
request removal and finite-value checks. The first fresh-cache request is
serial before enabling workers, reducing SQLite initialization contention.
Retries remain bounded; unavailable/delisted ticker histories remain failures.

In an interactive terminal downloads show a Rich spinner/bar, percentage,
completed securities, elapsed time, ETA, successes and failures. Animation
continues while a request is running. Redirected/dumb-terminal output remains
plain batch lines without terminal-control sequences. ETA is an estimate,
initially unknown, and includes validation/saving and revision-request overhead.
Upstream yfinance repair warnings remain visible; repair is not a guarantee
that the source history is correct. Invalid numerical outputs are rejected.
