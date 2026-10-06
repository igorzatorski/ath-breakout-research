# ATH research protocol

Status: prepared on 2026-10-05; the new study has not been run.
Stage 01 configuration: [baseline.json](baseline.json).
Registry of all trials: [experiments.csv](experiments.csv).

## 01 — study the signal itself

Hypothesis: a close above the previous all-time high is associated with a
different forward-return distribution than an appropriate control group.
Do not assume a positive premium or its feasibility in a portfolio.

- Identify securities by PERMNO; use historical monthly liquidity membership
  of approximately 3,000 stocks. This is not the official historical Russell 3000.
- Baseline nominal liquidity threshold: average dollar volume of $10 million
  over 21 sessions, using information available by the signal-date close.
- ATH: the maximum of previous split-adjusted highs, excluding the current
  session and auditing the pre-1993 ATH seed. Do not substitute a 252-day high.
- Signal: `split_close[t] > prior_ath[t]`. The following session and its
  observed opening define the earliest entry opportunity.
- No trend, consolidation or relative-volume filters, scoring, cooldown,
  position limit or top-N selection.
- Retain all daily events meeting the definition. Flag repeated breakouts
  in the same security; do not treat them as independent trials.

First implement event export over a short period and inspect it manually.
The existing CRSP candidate loader applies previous strategy rules; its
filtered list must not serve as the baseline population. Processed partitions
also reject some records. Audit the impact of these exclusions rather than
equating file validation with an unbiased sample.

The event table should retain PERMNO, signal date, nominal entry date, PIT
membership, close/high/prior ATH and their adjustment basis, opening price
and availability flag, liquidity, features known at the close, repeated-event
flags and quality flags. Record exclusions and their reasons separately.

Measure returns over 5, 21, 63 and 126 sessions from entry at the next opening,
including dividends, share adjustments and correct delisting accounting.
The 21-session horizon is the primary measurement; others are descriptive,
not a search for the best parameter. A simple adjusted-close ratio does not
replace a correctly calculated return from the opening.

Report event counts and unique securities, mean/median/return quantiles,
loss frequency, extreme gains and losses, adverse excursions and benchmark
returns over the same dates. The benchmark must use a consistent entry basis;
SPY adjusted-close observations alone are insufficient for an exact
open-to-close comparison. Also compare with stocks of similar market
capitalization and volatility from the same available PIT universe,
matched exclusively using information available on date t.

A missing opening means a non-executable nominal entry, not a trade at a
stale price. An incomplete forward horizon is a censored observation, not
a zero return. A delisting does not automatically remove an event from the
sample. Report these cases and the assumptions used.
Do not calculate independent-observation standard errors for overlapping
events. Define and justify time-block or clustering methods before
interpreting significance. An event study has no portfolio CAGR or drawdown.

## 02 — individual features

Study consolidation duration and depth, relative strength, relative volume,
volatility and extension separately. Examine distributions and ordered groups
before introducing filters. Features must be available at the signal time;
group boundaries must be established during development. Compare every trial
with the same baseline and record failures to improve. Do not immediately
combine multiple conditions into a score.

## 03 — a simple portfolio

After the signal study, define one explicit configuration: position count,
weights, excess-candidate selection, decision frequency, exit and cash rules.
Then use the existing engine after auditing execution and accounting.
S&P 500/SPY total return is the portfolio benchmark. Report CAGR, volatility,
drawdown, Sharpe, Sortino, Calmar, exposure, turnover, costs and loss distribution.
The risk-free rate needs an explicit source; rf=0 is a simplification.

## 04 — construction and risk

Change one element per trial: position count, sizing, sector limits, exits
or exposure constraints. Check costs and concentration. Then remove individual
model components to assess their contribution. A good portfolio result does
not replace an explanation of where performance comes from.

## 05 — validation

The available history has already been examined in previous studies. It is
not an untouched holdout. The 1994–2009 / 2010–2017 / 2018–2026-06-30 split
provides planned chronological validation on previously seen data, not proof
of genuine out-of-sample performance. Add period stability and walk-forward
analysis. New observations after freezing the model can support forward evaluation.

Each trial records an identifier, hypothesis, one change, configuration,
data/code fingerprints, period, costs, results and decision. Retain every
version in the registry. Changing results after inspecting validation requires
a new registered trial and acknowledgment that the period informed development.

## Naming and language

- Study ID: `ath_01_signal_baseline_v001`, followed by later versions and stages.
- Python files: `snake_case.py`; configurations: `snake_case.json`.
- Documents: `UPPER_SNAKE_CASE.md`.
- Outputs: `outputs/research/ath/<study_id>/<UTC run timestamp>/`.
- Each run: `manifest.json`, `events.parquet`, `exclusions.csv`,
  `summary.csv`, `report.html` (only artifacts actually generated).
- Use English for documentation, code comments, messages and reports.

## Next task

Implement and test unfiltered ATH event extraction without portfolio simulation
or filter tuning. Check seeds, memberships, splits, consecutive breakouts and
missing openings. Calculate forward returns only after these checks.
