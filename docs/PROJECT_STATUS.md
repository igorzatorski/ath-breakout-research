# Project status — 2026-10-15

## Current position

The project is studying the signal itself: unfiltered ATH forward returns versus
same-date SPY and five size/volatility matched non-ATH stocks. No current portfolio,
exit or filter optimization. The completed conditional 1994-2026 study has a
small positive 21-session event-weighted excess, but intervals include zero and
period/weighting sensitivity prevents a confirmed repeatable-premium claim.
See `research/ath/ATH_SIGNAL_STUDY_RESULTS.md` and `RESEARCH_MAP.md`.

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

Audit the large history-quality selection and concentration in repeated events
before extending conclusions or introducing new hypotheses. The authorized WRDS
retry produced an isolated true-high seed without overwriting the legacy seed.
Missing historical highs still restrict the primary sample; this is not a
complete-market ATH study. The standalone study uses raw observations, not the
previous strategy-filtered candidate loader. All four planned horizons and
matched controls are calculated; 21 remains primary. Earlier 2024 exit pilots
are retained as exploratory trials, not the current research scope.

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
