# Project status — 2026-10-06

## Current position

The project has moved from Data Layer construction to preparation for quant
research. No new unfiltered ATH event study has been implemented or run.
Prior strategy performance does not establish an ATH premium or alpha.

## Available infrastructure

- Local CRSP daily history: 1993-01-01 through 2026-06-30, with PERMNO identity,
  corporate actions, distributions, delistings and pre-period ATH seed.
- Historical monthly liquidity population of approximately 3,000 securities.
  This is not official Russell 3000 membership or the complete CRSP market.
- Independent Yahoo/IWV current screener and SPY benchmark observations.
- Local manifests, fingerprints, partition checks and quality audit.
- Incremental WRDS availability checks and explicit local-only option.
- Portfolio accounting, cost handling, SPY growth/drawdown dashboard and metrics.
- Locked `.venv`, automatic interpreter selection through `run/`, ETA reporting.
- Isolated output directories, configuration/provenance records and comparison.
- Windows/Linux CI configuration; live downloads are outside CI coverage.

A local readiness pass checks artifact consistency, not research unbiasedness,
return correctness in every economic case or statistical significance. The
historical CRSP repair report remains evidence for the previous review.

## Next research deliverable

Implement `ath_01_signal_baseline_v001` as a short-period event export from
appropriate PIT data. Audit pre-period ATH seeds, processed-data exclusions,
next-session observed openings, splits, repeated breakouts and censoring.
The current candidate loader applies prior strategy filters and cannot be
used unchanged as the unfiltered baseline.

After event verification, study 5/21/63/126-session total returns with 21 as
the primary horizon, aligned SPY execution and size/volatility matched controls.
Then study individual features; construct a simple portfolio only after that.

## Before interpreting performance

Record changes and unsuccessful trials. Account for overlapping events,
previously inspected history, transaction costs, concentration, cash and
missing observations. The proposed chronological split is not an untouched
holdout. Current portfolio ratios use rf=0; SPY is an index proxy.

## Technical closeout

The restructuring preserves local observations and previous experiments.
The obsolete shell launcher is replaced by `run/venv.py`: setup/check only;
other launchers automatically use `.venv`. Generated reports and licensed
data are excluded from GitHub. Verification details are recorded in
`docs/VERIFICATION.md` after the final checks.
