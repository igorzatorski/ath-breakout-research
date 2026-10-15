# 52-week high versus ATH — 2024 descriptive pilot

Date: 2026-10-15. Study: `high_01_52w_vs_ath_pilot_v001`.
Run: `20261015T205046302698Z`.
Protocol: [HIGH_BREAKOUT_PILOT_PLAN.md](HIGH_BREAKOUT_PILOT_PLAN.md).

## Question and result

Does buying after a 252-session high breakout outperform SPY, and does an ATH
condition improve the result? In this single-year pilot, the unfiltered 52-week
signal underperformed matched-date SPY at every measured horizon. The local-history
ATH subgroup had a small gross 21-session excess that did not survive the
illustrative stock trading costs or equal-security event weighting. No alpha,
optimal-signal or general no-effect claim follows from this year.

## Sample

12,550 events across 1,386 PERMNOs. 12,539 have observed next-session entry opens;
11 remain non-executable and are not assigned returns. All valid entries have
complete measured horizons under the stated terminal-cash convention.

Preliminary price-breakout exclusions: 3,616 below the USD 10m liquidity floor,
1,293 outside effective PIT membership. These counts do not include all stock
days lacking 252 valid prior highs: those cannot generate a qualified signal.

## All 52-week breakouts

Each row averages the same 12,539 executable event windows, not a portfolio.
SPY is measured over the exact entry/exit dates of each event. Costs below apply
to the stock at 10 bps each side; benchmark is gross.

| Sessions | Mean stock return | Mean SPY return | Mean excess | Mean excess after stock costs |
| --- | ---: | ---: | ---: | ---: |
| 5 | -0.10% | 0.11% | -0.22 pp | -0.42 pp |
| 21, primary | 1.01% | 1.43% | -0.42 pp | -0.62 pp |
| 63 | 2.74% | 3.95% | -1.20 pp | -1.41 pp |
| 126 | 4.18% | 5.89% | -1.71 pp | -1.92 pp |

## Disjoint groups at the primary 21-session horizon

| Group | Events / valid | Mean stock | Mean SPY | Mean excess | Excess after stock costs |
| --- | ---: | ---: | ---: | ---: | ---: |
| 52W breakout below/equal known ATH | 5,951 / 5,942 | 0.53% | 1.39% | -0.86 pp | -1.06 pp |
| ATH using local history without either identified history flag | 3,376 / 3,375 | 1.63% | 1.47% | 0.16 pp | -0.04 pp |
| Candidate ATH with uncertain history | 3,223 / 3,222 | 1.25% | 1.45% | -0.20 pp | -0.40 pp |

The groups can contain the same security on different dates. The ATH label is
qualified: missing pre-1993 maximum highs and historical gaps prevent certifying
all candidate ATHs. Even the unflagged group does not independently establish
complete listing-inception coverage. The pre-1993 close seed was not repaired.

## Sensitivity and limitations

- Equal-security averaging first averages each security's events, then gives
  each security equal weight. 21-session mean excess changes from -0.42 pp to
  -3.40 pp for all 52W, and from +0.16 pp to -2.23 pp for local-history ATH.
  This is event-weighting sensitivity, not an equal-weight portfolio backtest.
- Equal-signal-date mean excess: -0.65 pp for all 52W and +0.02 pp for local ATH.
- All-52W median stock return is 0.53%, median event excess is -0.97 pp,
  loss frequency 46.77%, 5th/95th return percentiles -14.29%/+17.53%.
- Repeated breakouts and forward windows overlap. Rough signal-month bootstrap
  intervals cross zero, but 12 blocks cannot supply robust inference and the
  method does not eliminate cross-month dependence, especially at long horizons.
- Single previously seen year; no untouched holdout. No size/volatility/sector
  matched controls or factor-risk adjustment. Groups cannot establish causality.
- CRSP CIZ terminal Y returns are applied exactly once, then terminal proceeds
  are held as zero-interest cash until the horizon. There are 60 such primary
  windows. This does not simulate actual settlement or successor-stock holding.
- First-day close/open excludes entry-day overnight gain and ex-date dividend;
  later CIZ total returns include distributions. Exotic intraday entry
  distributions are not separately modeled. SPY uses a different vendor's
  dividend-reinvestment proxy. Source semantics:
  https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-guide-flat-file-format-2-0/

## Validation and reproducibility

288 tests passed; Ruff passed. Eight new tests cover complete prior windows,
entry timing, missing observations, terminal handling and benchmark entry basis.
20 sampled thresholds agree with independent raw-row maximum calculation.
52 additional numerical checks passed: 24 regular windows, 12 terminal windows,
12 terminal-record reconciliations and 4 missing-entry horizon checks. These
check local arithmetic and consistency, not vendor accuracy. No chart review.

Reproduce: `.venv/Scripts/python.exe scripts/research/compare_high_breakouts.py`.
Main artifacts under
`outputs/research/high_breakouts/high_01_52w_vs_ath_pilot_v001/20261015T205046302698Z/`:
events, forward returns, summary, coverage, monthly summaries, sample checks and
manifest with source/code/artifact SHA256 fingerprints. Research code remains
locally uncommitted; original observations and previous runs are preserved.

Decision: retain both signal definitions for research. Do not choose a winner
or optimize filters from 2024. Next compare predefined historical periods,
resolve ATH provenance, introduce appropriate controls and review dependence
and weighting before estimating risk-adjusted alpha.
