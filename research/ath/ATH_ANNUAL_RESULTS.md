# Annual extension: ATH versus matched-date SPY

Study: `ath_06_annual_v001`; run `20261015T221839273190Z`.
Protocol: [ATH_ANNUAL_PLAN.md](ATH_ANNUAL_PLAN.md).
User-requested descriptive extension; original 21-session primary remains unchanged.

## Annual result

Same 75,884 frozen ATH events; 71,961 have valid 252-session stock/SPY windows
across 2,736 securities. Last fully observed signal: 2025-06-27; last exit:
2026-06-30. Later horizons are censored, not assigned zero returns.

| Gross arithmetic event mean | Return |
| --- | ---: |
| Stock after ATH, 252 sessions | +12.6411% |
| SPY over identical opening-entry / closing-exit dates | +10.0911% |
| Paired excess stock minus SPY | +2.5499 percentage points |

These are overlapping one-year event returns, NOT portfolio CAGR or the
unconditional mean of calendar-year S&P 500 returns. SPY is a total-return proxy,
not the official index. Entry is next-session observed open, not signal close.
Subsequent CIZ distributions/terminal returns are included; terminal proceeds
remain zero-interest cash until the prescribed horizon. Values are before costs.

Annual median stock return is +6.64%; median paired SPY excess is -3.40 pp.
Mean excess is driven by positive-tail outcomes and weighting of recurring
events; it does not imply that the typical event beats SPY.

## Uncertainty and periods

Circular signal-date bootstrap, 252-session blocks, 2,000 draws:
annual SPY excess interval -1.99 to +8.82 pp. A 504-session-block sensitivity
also includes zero (-1.85 to +8.10 pp). Persistent firm dependence is not fully
addressed by calendar blocks. This is not a confirmed risk-adjusted alpha.

| Signal period | Events | Mean ATH | Mean matched-date SPY | Excess |
| --- | ---: | ---: | ---: | ---: |
| 1994-2009 | 25,633 | +15.44% | +6.22% | +9.22 pp |
| 2010-2017 | 22,117 | +12.87% | +12.19% | +0.68 pp |
| 2018 through last complete 2025 signal | 24,211 | +9.46% | +12.27% | -2.81 pp |

The small annual mean excess is not stable over the predefined periods.
These are previously observed history, not untouched out-of-sample tests.

## Common sample across all five horizons

Each row uses the SAME 71,961 valid event IDs. This prevents attributing changes
solely to different censoring/coverage populations. It does not remove overlap.

| Sessions | Mean ATH | Same-window SPY | Excess |
| --- | ---: | ---: | ---: |
| 5 | -0.25% | +0.01% | -0.27 pp |
| 21 | +0.79% | +0.54% | +0.24 pp |
| 63 | +2.95% | +2.13% | +0.82 pp |
| 126 | +5.96% | +4.94% | +1.01 pp |
| 252 | +12.64% | +10.09% | +2.55 pp |

The annual interval is calculated on its prescribed sample; no joint best-horizon
selection or adjustment for choosing an optimum is claimed. Shorter means here
differ from earlier available-sample summaries because the sample is now fixed.

## Additional fixed sensitivities

- Original fixed five controls: 67,803 complete annual matched events. Mean ATH
  +12.53%, SPY +10.05%, controls +9.06%. Excess controls +3.48 pp, with descriptive
  calendar-block interval +0.92 to +6.70 pp (252 blocks). This is conditional
  association and a retrospective secondary result; controls omit past momentum,
  sector and other risk exposures. It is not multifactor alpha or a reason to
  replace the predeclared primary test.
  Equal-security control excess is -13.00 pp, while equal-date control excess
  is +4.12 pp; the positive interval for the event-weighted mean is not evidence
  of robustness to company weighting or persistent within-company dependence.
- Previously frozen 21-session repeat suppression: 22,001 stock/SPY annual
  windows. ATH +12.55%, SPY +10.32%, excess +2.23 pp; interval -2.12 to +8.44 pp.
  We did not change exclusion length to 252 or choose a better-performing sample.
- Equal-security annual SPY excess is -19.54 pp in the all-SPY sample, versus
  event-weighted +2.55 pp. This first averages within each security, then across
  securities, and is not an equal-weight portfolio. It shows severe sensitivity
  to recurring events and heterogeneous company outcomes.

## Coverage, controls and verification

3,505 censored event horizons, 243 invalid paths, 175 missing entries, 71,961
valid annual outcomes. All source signal/history-quality restrictions remain:
this is a conditional sample, not all market ATHs. Missing control horizons are
not replaced with different companies after observing future availability.

Local raw source hashes reconciled with the original run. Three new annual
tests passed: a 252-session window extending into a second January, strict
data-cutoff censoring despite hypothetical later prices, and terminal cash once.
189 production scalar/vector return comparisons passed, along with identity,
coverage, excess arithmetic and artifact hash checks. Ruff passed. No visual QA.

The calendar extends far enough for years with fewer than 252 sessions; no
year-end truncation was silently introduced. Original files/runs are preserved.
No WRDS connection or data refresh was used.

Reproduce: `.venv/Scripts/python.exe scripts/research/extend_ath_annual.py`.
Artifacts: `outputs/research/ath/ath_06_annual_v001/20261015T221839273190Z/`.
Includes annual outcomes, common-horizon comparison, period/coverage summaries,
bootstrap intervals and SHA256 manifest. New changes remain uncommitted.

Decision: positive annual mean excess exists in this selected historical sample,
but it is not a demonstrated repeatable SPY advantage. Retain annual horizon as
an explicit extension and inspect momentum/history selection before adding
filters or claiming an optimal holding period.
