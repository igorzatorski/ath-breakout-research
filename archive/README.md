# Research archive

## 2026-10-05 — workspace reset before ATH research

The local `2026-10-05_workspace_reset/` directory contains:

- `experiments/bloomberg_momentum/` — all Bloomberg code and reports;
- `experiment_tests/` — two files containing 18 experiment tests;
- `outputs/` — previous ATH reports, screens and test artifacts;
- `source_before_reset.zip` — 143 source, test and documentation files from before cleanup;
- `inventory.json` — relocation map, snapshot hashes and data inventory;
- `cleanup_log.json` — removed caches and any access restrictions.

The archive payload is local and excluded from Git. It is not a backup on
another drive. Raw and processed market observations remain under `data/`.
Historical snapshots retain their original contents, including their original language.

Bloomberg: 1994–2026-06-30, costs of 10 bps per side. Final comparison:
`experiments/bloomberg_momentum/outputs/comparison_20261005T224234794475Z/`.
Short signal top8 CAGR: -9.26%; top20: -0.59%. Long signal top20:
CAGR 11.95%, volatility 41.37%, maximum drawdown -87.99%, versus SPY CAGR 10.87%.
SMA50 entry / entry+exit CAGR: 7.40% / 5.96%. These are exploratory results
with assumptions for missing quotes; alpha was not established.
The comparison corrected weight accounting for frozen positions.
The first top8 reports used an earlier accounting version.

## Restoration

Read `inventory.json` first. To run the previous Bloomberg experiment,
restore `experiments/` to its original location and both test files to
`tests/backtesting/`. Do not overwrite new research files. The experiment
derives its root from its location, so running directly inside the archive
is not supported. HTML reports can be opened without restoring the code.

The ZIP snapshot supports comparison with the previous code. Do not extract
it indiscriminately over the new workspace. Previous results are not the
baseline for the new ATH study.

## 2026-10-06 — command and documentation restructuring

The local `2026-10-06_structure_cleanup/` contains obsolete compatibility
wrappers, the old PowerShell-launching environment script and its test,
the redundant daily-screen wrapper/test, and CSV demonstration files.
`relocation_map.json` maps the active implementation/document paths before
and after restructuring. No observations or CRSP partitions were relocated.

The supported entry points now live in `run/`. Implementations are grouped
under `scripts/data/`, `scripts/screening/`, `scripts/backtesting/` and
`scripts/research/`. Archive payload remains local and excluded from Git.
