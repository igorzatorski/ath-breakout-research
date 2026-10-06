# Technical verification — 2026-10-06

Completed locally on Windows with Python 3.11.14 and the locked project `.venv`.

- `run/venv.py`: locked synchronization and all required imports passed;
  `scikit-learn` 1.9.1 is available. No interactive shell is opened.
- `run/check_data.py`: local manifests, partition counts, source fingerprints
  and planned coverage passed. Local CRSP ends on 2026-06-30.
- Full suite: 257 tests passed; Ruff and `uv lock --check` passed.
- Public launchers were tested from outside the project working directory.
- A real local CRSP pipeline check used 2024-01-02 through 2024-01-12 and
  the first 20 sorted PERMNOs, with two portfolio configurations. Both saved
  summaries, tables, dashboards and provenance manifests in isolated folders.
- The saved-run comparison produced HTML, full metrics CSV and warning JSON.
  The small subset produced no trades: this verifies output plumbing, not
  representative selection, execution with trades or strategy performance.
- Unit checks cover run preservation/failure status, private-settings exclusion,
  differing periods, growth normalization and modified artifact rejection.
- CI is configured for Windows and Linux. Local checks do not imply that the
  new GitHub Actions runs have completed; inspect their results separately.

Diagnostic runs stay under `outputs/diagnostics/backtests/`, excluded from Git.
They are not registered research results. Existing accounting/economic tests
remain in the full suite. The unfiltered event extractor is not implemented.
