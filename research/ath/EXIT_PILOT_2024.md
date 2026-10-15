# Three fixed exit families — 2024 ATH pilot

Study: `high_03_exit_families_pilot_v001`; run `20261015T211100349011Z`.
Protocol: [EXIT_PILOT_PLAN.md](EXIT_PILOT_PLAN.md).
Research context: [RESEARCH_MAP.md](RESEARCH_MAP.md).

## Scope

Exactly the same 3,376 qualified local-history ATH events in 2024. One missing
entry open in every rule; the common paired sample has 3,375 events across 340
PERMNOs. No signal changes, technical filters, ranking, sizing, re-entry or
parameter search. The known ATH historical-provenance qualifications remain.

Three rules, defined before these results:

- Hold until session-126 close, unless a terminal event occurs earlier.
- Closing break below frozen prior ATH: sell next exchange-session open.
- Fixed signal-date ATR20 (simple mean true range): initial level 2 ATR below
  entry; trailing level 3 ATR below the highest observed closing price, anchored
  at entry. Use the tighter level. Closing trigger, next-session opening exit.
  ATR is frozen; 20/2/3 are starting conventions, not optimized parameters.

## Results

Means per hypothetical event, not annualized returns or portfolio performance.
Net stock returns include 10 bps at purchase and sale. After exit, proceeds remain
in zero-interest cash through the same 126-session observation horizon.

| Exit | Mean gross | Mean net | Mean holding sessions | Loss frequency net | 5th percentile net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hold 126 | 4.74% | 4.53% | 125.50 | 44.59% | -33.39% |
| Failed breakout | 0.81% | 0.61% | 24.55 | 82.99% | -9.01% |
| ATR trend | 1.36% | 1.16% | 25.32 | 63.53% | -11.81% |

Holding sessions counts sessions held through close for opening exits; the final
opening sale itself does not add a full holding session. Terminal exits account
for the baseline mean slightly below 126. Risk-tail numbers are event outcomes,
not portfolio drawdown. Lower holding times mean much lower market exposure:
the smaller raw mean cannot alone establish that an exit family is worse.

## Matched exposure benchmark

For each event, SPY enters at the same opening and exits at the same opening or
closing time as the stock. Ex-date dividends are credited when entitled. Both
then hold cash at zero interest. SPY is gross while stocks include costs.

| Exit | Mean SPY over matching holding window | Mean net stock excess | Equal-security mean excess |
| --- | ---: | ---: | ---: |
| Hold 126 | 5.30% | -0.77 pp | -7.64 pp |
| Failed breakout | 0.78% | -0.17 pp | -1.84 pp |
| ATR trend | 1.05% | +0.11 pp | -2.37 pp |

The equal-security calculation averages each security's event returns before
averaging across securities. It is not an executable equal-weight portfolio.
The ATR event-weighted excess is small, disappears under this sensitivity, and
does not establish alpha. Exit dates are selected by stock outcomes; this matched
benchmark is descriptive, not a risk-factor or causal adjustment.

Full-horizon SPY gross is 5.33% for all variants. Net excess to it is -0.81 pp,
-4.72 pp and -4.18 pp respectively, but that comparison includes the large cash
periods following early exits. Freed capital is NOT reinvested into other signals.

## The loss/winner tradeoff

| Exit | Mean net outcome among fixed-hold losers | Mean net among fixed-hold big winners | Of 738 fixed-hold gross +20% winners still reaching gross +20% |
| --- | ---: | ---: | ---: |
| Hold 126 | -16.19% | +39.51% | 738 |
| Failed breakout | -3.48% | +11.26% | 206 |
| ATR trend | -3.40% | +11.11% | 183 |

Future fixed-hold cohorts are retrospective explanation only. Earlier exits
reduce losses but capture much less of the later upside in this configuration.
This does not show that every asymmetric-exit strategy fails: different regimes,
re-entry, freed-capital allocation and portfolio constraints remain untested.

## Decision

No robust edge or optimal configuration found. Do not tune more parameters to
rescue 2024. The next useful test is the SAME rules on other predefined periods,
with historical-data limitations resolved or consistently disclosed. These are
model-family pilots; parameter sensitivity and portfolio design are later stages.

## Verification

302 tests passed; Ruff and Git whitespace check passed. Nine new tests cover
next-open gaps, absence of exit-day-close leakage, dividend entitlement,
missing-opening behavior, terminal events, splits, ATR timing and SPY matching.
All 3,375 fixed-hold outcomes match the previous independent baseline.
Opening/cash-distribution accounting reconciles with 180,641 observed regular
daily returns: maximum absolute error 0.000000550 (within CRSP return rounding).
Execution-sequence invariants and artifact fingerprints checked. No visual QA.

Reproduce: `.venv/Scripts/python.exe scripts/research/compare_exit_families.py`.
Artifacts under `outputs/research/high_breakouts/high_03_exit_families_pilot_v001/20261015T211100349011Z/`:
frozen config, all outcomes, common paired outcomes, coverage, summary, monthly
results, exit reasons and SHA256 provenance. Code remains locally uncommitted.
