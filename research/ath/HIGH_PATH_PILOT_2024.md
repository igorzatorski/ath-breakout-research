# Breakout path diagnostic — 2024

Study: `high_02_paths_pilot_v001`; run: `20261015T210123396481Z`.
Protocol: [HIGH_PATH_PILOT_PLAN.md](HIGH_PATH_PILOT_PLAN.md).
Same frozen events and raw-source hashes as the first 52W/ATH pilot.

## Main finding

In the qualified local-history ATH group, many eventual large winners revisit
the breakout level. A close below that level is therefore not equivalent to
identifying a failed long-run trade. Early warnings show only a small separation
in subsequent raw mean returns in this pilot. No exit was simulated or optimized.

## Population and retrospective cohorts

12,550 frozen events; 12,539 complete wealth paths; 11 missing entry opens.
Intraday high/low observations were complete for every valid pre-terminal path.
All four closing-return checkpoints match the original pilot (50,156 checks).

Primary local-history ATH group: 3,375 valid events across 340 securities.
ATH provenance qualifications remain unchanged; these are not all independently
certified inception-history ATHs.

- 738 events across 107 securities finish at least +20% after 126 sessions.
- 1,489 events finish below entry wealth; 1,148 finish between 0% and +20%.
- These labels use future returns and cannot be known at entry. Events repeat
  in the same security; they are not independent trials.

## What eventual +20% winners experienced

| Measure | Result |
| --- | ---: |
| Close below frozen ATH level before first +20% closing wealth | 519 / 738 = 70.33% |
| Close below ATH within first 5 holding sessions | 369 / 738 = 50.00% |
| Median session reaching first +20% close | 59 |
| Median minimum closing return before that milestone | -2.83% |
| Median intraday low-price excursion before that milestone | -4.20% |
| At least -5% closing excursion before milestone | 32.66% |
| At least -10% closing excursion before milestone | 13.41% |
| At least -5% intraday price excursion before milestone | 42.41% |
| At least -10% intraday price excursion before milestone | 20.19% |
| Median eventual 126-session return | +33.22% |

Intraday excursions refer to price; closing wealth includes subsequent
distributions. Intraday tallies at the same round 5%/10% levels are descriptive,
not a tested stop strategy. Daily bars cannot establish intraday hit order;
the milestone here is the FIRST CLOSING wealth at +20%, not the first intraday
touch. No claim about actual order fills, re-entry or net portfolio returns.

## Early-warning landmark

Classify at the fifth holding-session close: did ANY close since entry return
below the fixed breakout level? Include only stocks still quoted and nonterminal
at that close. Evaluate only returns AFTER that close through session 126.

| Local ATH subgroup | Events | Mean future stock return | Mean future SPY | Mean excess | Equal-security mean excess |
| --- | ---: | ---: | ---: | ---: | ---: |
| No breach by day 5 | 1,497 | +4.78% | +4.43% | +0.35 pp | -5.83 pp |
| Breach by day 5 | 1,872 | +4.62% | +5.68% | -1.06 pp | -6.17 pp |

The raw future mean return is very similar. Different dates and company
characteristics affect the benchmark difference. Neither subgroup's positive
raw return establishes alpha. Equal-security weighting is not a portfolio and
reveals substantial dependence on recurring events in successful securities.
This landmark is conditional on survival to day 5, explicitly not an entry rule
or a causal test of selling at the first breach.

## Winners can surrender gains

1,387 local ATH events reached at least +20% on a close somewhere in the window.
649 of those (46.79%) finished below +20%, including 220 that finished below
entry wealth. This motivates studying profit protection but does not show that
a trailing rule can capture the historical peak or improve net performance.

Retrospective example: VST signal 2024-01-08 returned about +138.08% by session
126 but closed below its frozen breakout level on holding session 2. This is a
selected illustration, not representative evidence or a recommendation.

## Decision and next experiment

Keep the idea of asymmetrical exits as a hypothesis. Do not interpret every
ATH retest as failure and do not select an optimal stop from these paths.
A follow-up can compare a small number of economically motivated exit families
with a fixed baseline, including failed-breakout exits and a loose trailing exit.
That requires actual next-open execution, gaps, costs and exposure-aware SPY
comparison, followed by other periods. No such strategy test was run here.

## Verification and artifacts

293 tests passed; Ruff passed. Five new tests cover wealth paths, terminal
handling, warning-time leakage, missing returns and incomplete intraday bars.
Artifact hashes, cohort/sequence invariants and original checkpoint agreement
passed. Numerical review only; no visual chart inspection.

Reproduce: `.venv/Scripts/python.exe scripts/research/analyze_breakout_paths.py`.
Artifacts: `outputs/research/high_breakouts/high_02_paths_pilot_v001/20261015T210123396481Z/`.
Includes event paths, cohort/landmark/coverage summaries, selected retrospective
examples and source/code/artifact fingerprints. Changes remain uncommitted.
