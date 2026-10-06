# Start here

## Environment

Open `run/venv.py` and click **Run Python File**. It prepares `.venv`, verifies
required imports including `scikit-learn`, and exits. It does not open a shell.
Every other file in `run/` selects `.venv` automatically. No activation is needed.
`--check` only checks the existing environment; the default synchronizes it.

If `.venv` does not exist yet, install uv and run `uv sync --all-extras --locked`.
In VS Code, select `.venv/Scripts/python.exe` as the workspace interpreter.

## Tomorrow's research session

1. Run `run/check_data.py`. This is read-only and does not contact WRDS.
2. Read `docs/PROJECT_STATUS.md` and `research/ath/RESEARCH_PLAN.md`.
3. Review `research/ath/baseline.json` and its predeclared hypothesis/horizons.
4. Implement a short-period **unfiltered ATH event export**, auditing seeds,
   PIT membership, split adjustments, repeated events and missing openings.
5. Inspect events and exclusions before calculating forward returns.
6. Record the trial in `research/ath/experiments.csv`, including its saved run.

Do not substitute the existing filtered candidate loader for the baseline.
No new signal/portfolio research results are claimed by this workspace cleanup.

## Existing commands

Use `run/update_data.py` for CRSP availability checks and incremental updates.
Use `run/update_yahoo.py` only for the separate current-universe market pipeline.
`run/screen.py`, `run/screen_period.py` and `run/backtest.py` execute the previous
strategy for reference. They check CRSP remotely unless `--skip-crsp-check` is
explicitly supplied. A current screen also updates Yahoo.

For a backtest with no interactive prompts:

```powershell
.\.venv\Scripts\python.exe run\backtest.py --skip-crsp-check --start 2024-01-02 --end 2024-12-31 --no-open
```

Read the printed result path. Open `interactive_dashboard.html` for equity and
drawdown against SPY. Use `run/compare_backtests.py` with two saved directories;
it writes a separate comparison and preserves both originals.

## Files and backups

User commands live in `run/`; implementations in `scripts/`; reusable modules
in `src/ath_breakout/`. Documentation lives in `docs/`. Generated results live
under `outputs/`; observations and manifests stay under `data/`.
See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for the detailed layout.
Archive indexes are tracked, but local archive payloads and licensed CRSP data
are not uploaded to GitHub. The archive is not an external backup.
