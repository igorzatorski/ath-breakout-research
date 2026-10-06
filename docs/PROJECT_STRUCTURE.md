# Project structure

## Ownership

- `run/`: small launchers. These choose `.venv` and the project working directory.
- `scripts/data/acquisition/`: WRDS downloads and derived-history builders.
- `scripts/data/validation/`: schema, coverage, identity, economics and quality checks.
- `scripts/data/credentials/`: credential-manager utilities.
- `scripts/data/maintenance/`: CRSP refresh, Yahoo pipeline and local rebuilding.
- `scripts/screening/`: current Yahoo, historical snapshots and CRSP range commands.
- `scripts/backtesting/`: CRSP reference portfolio and Yahoo diagnostic portfolio.
- `scripts/research/`: readiness and saved-run comparisons; future study commands.
- `src/ath_breakout/data/`: source adapters, identities, adjustments, storage and validation.
- `src/ath_breakout/strategy/`: existing ATH/features/rules.
- `src/ath_breakout/screening/`: reusable screening and ranking logic.
- `src/ath_breakout/backtesting/`: PIT inputs, execution/accounting and reports.
- `src/ath_breakout/research/`: common run records and provenance.
- `research/ath/`: protocol, planned baseline configuration and experiment registry.
- `docs/data/`: source contract and historical repair evidence.
- `docs/legacy/`: previous strategy specification, retained as a reference.
- `tests/`: reusable-module tests and command tests; no live download requirement.

## Naming

Python files and configuration names use `snake_case`. Documents use
`UPPER_SNAKE_CASE.md`, except repository entry points such as `README.md`.
Study IDs use `ath_<stage>_<description>_v<version>`. Reference outputs use
`reference_ath_v001` to distinguish existing rules from the unfiltered baseline.
All active project text is English.

## Data boundary

Keep `data/raw/`, `data/processed/`, `data/universe/`, `data/state/` and
`data/cache/` stable: manifests and caches refer to these paths. Cosmetic
renaming of local observations is unnecessary and risks invalidating provenance.
`data/processed/crsp/strategy_by_year/` includes previous filters/exclusions;
it is not automatically a neutral baseline event population. The retained
backtesting cache also belongs to that previous loader.

## Output contract

Every generated command report has a unique UTC run directory and
`manifest.json`. Portfolio reports include `summary.csv`, `equity_curve.csv`,
`annual_performance.csv`, `trades.csv`, `events.csv`, `ranked_candidates.csv`
and `interactive_dashboard.html`. Screens produce `screen.csv` or
`breakouts.csv`. Comparison outputs include `comparison.csv`, `comparison.html`
and `warnings.json`. Only artifacts actually written are listed in manifests.

The common run recorder stores save status, full command configuration,
source-manifest hashes, benchmark hash, code fingerprint, lock fingerprint,
Git commit and artifact hashes. Input hashes describe local snapshots; they
are not a historical vendor revision service or a full copy of licensed data.
A Git commit may precede working-tree edits; use the code fingerprint too.

Future ATH event studies use `outputs/research/ath/<study_id>/<run_id>/`.
They must record event/exclusion definitions and aligned economic-return
assumptions. The event extractor is the next implementation task.

## Archive

See [archive/README.md](../archive/README.md). Bloomberg experiments and previous
ATH outputs were archived on 2026-10-05. Redundant wrappers, demonstrations and
the old shell launcher were archived on 2026-10-06. Payloads stay local; the
index is on GitHub. Restore deliberately using relocation maps, never by
extracting a source snapshot over current work.

Small `--max-securities` pipeline checks are saved under `outputs/diagnostics/`
and explicitly labeled diagnostic; they are not research results.
