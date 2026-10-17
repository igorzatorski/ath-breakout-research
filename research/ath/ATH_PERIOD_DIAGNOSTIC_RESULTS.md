# Historical-period diagnostic: annual ATH plus momentum 6-1/top20

Study: `ath_13_period_diagnostic_v001`.
Successful run: `20261016T211113381140Z`.
Protocol: [ATH_PERIOD_DIAGNOSTIC_PLAN.md](ATH_PERIOD_DIAGNOSTIC_PLAN.md).

## Answer and limits

The observed early-to-recent decline is associated with a much smaller positive
tail, a few influential signal-year cohorts, and stronger same-window SPY.
Simple shifts in observed size/volatility composition do not account for it.
This explains the arithmetic pattern substantially better than saying a broadly
validated strategy stopped working. It does NOT identify a causal market change.

Even the early positive premium and the early/recent difference have approximate
intervals including zero. Do not claim statistically established structural decay,
market efficiency, institutional crowding or an economically identified cause.
The 6-1/top20 focus was selected after its high mean was observed. All history is
known and quality-selected; no new strategy, filter or parameter was introduced.

## Frozen sample and headline reconciliation

Same ath_12 common-momentum annual population (65,650 events); focus on its 23,712
6-1/top20 events. Same next-open entry, 252-session horizon, gross total returns,
aligned SPY, original exclusions, frozen controls and company non-overlap flags.
Historical PERMCO, not current tickers, defines company groups. Dates are SIGNAL
cohorts, not calendar-year strategy returns. Latest complete 2025 cohort is partial.

| Signal period | Events | Mean stock | Same-window SPY | Excess SPY | Median excess |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1994-2009 | 8,462 | +21.57% | +4.46% | +17.11 pp | -3.50 pp |
| 2010-2017 | 6,892 | +12.97% | +12.08% | +0.90 pp | -3.08 pp |
| 2018 through complete 2025 signals | 8,358 | +11.34% | +13.58% | -2.23 pp | -9.03 pp |

Recent minus early excess = **-19.34 pp**, reconciled exactly:

- Stock mean changed by -10.23 pp (52.86% of the observed decline).
- SPY mean rose by +9.12 pp, contributing -9.12 pp (47.14%).

These are accounting components of stock-minus-SPY, not independent economic
causes. SPY averages only the event-specific holding windows, not unconditional
calendar-year index returns. Stronger SPY is not itself proof of crowding.

With the fixed non-overlap flags: early stock +14.92%, SPY +4.01%, excess +10.91
pp; recent stock +14.19%, SPY +14.48%, excess -0.29 pp. The excess change is
-11.20 pp: stock component -0.73 pp and benchmark component -10.46 pp.
Thus the raw stock-return decline is much weaker under this different sampling.
Do not present it as a portfolio, or select whichever weighting tells the best story.

## Historical episodes and company concentration

Signal-year contributions to the EARLY event-weighted mean:

- 1999: 934 events, mean excess +94.14 pp, contribution +10.39 pp.
- 1998: 687 events, mean excess +52.45 pp, contribution +4.26 pp.
- Together: 1,621 events (19.16% of early events), contribution +14.65 pp to
  the total early +17.11 pp (85.61% of the NET mean, not all positive returns).
- The fixed exclusion of 1998-2000 leaves 6,156 early events with +5.37 pp excess.
  This removes a negative 2000 cohort as well as large positive 1998/1999 cohorts;
  it is not an optimized or tradable exclusion.

Largest early positive PERMCO contributors include historical YHOO, SDLI, DELL,
DISH and AMCC. Retrospectively removing the top five leaves +9.42 pp; removing
the top ten (432 events) leaves +5.36 pp. These are influence diagnostics only.
Positive contributions remain outside the leaders; the result is not literally
produced by just one company, nor does deletion identify future winners.

The most recent group is also heterogeneous:

| Signal year | Events | Mean annual excess SPY | Contribution to recent mean |
| --- | ---: | ---: | ---: |
| 2019 | 1,269 | +17.60 pp | +2.67 pp |
| 2021 | 1,420 | -22.80 pp | -3.87 pp |
| 2023 | 658 | +2.86 pp | +0.23 pp |
| 2024 | 1,245 | -3.22 pp | -0.48 pp |
| 2025, partial | 337 | -19.75 pp | -0.80 pp |

Leaving out 2021 retrospectively changes the recent mean from -2.23 to +1.98 pp
(6,938 events). This identifies an influential cohort, not a rule that could have
excluded it prospectively. A 2021 signal's annual outcome extends beyond its
signal year; the row is not the strategy's calendar-2021 return. All annual and
leave-one-year-out figures are saved, including unhighlighted years.

Recent positive company contributors include TSLA, VST, APP, ELF and AXSM;
large negative contributions include Z/ZG, INGN, NFLX, REGI and TPL. Labels are
historical descriptions, not industry classification or trading recommendations.

## Positive tail versus typical events

Fixed paired-excess buckets reconcile the mean exactly. Events beating their
same-window SPY by more than 200 pp:

| Tail statistic | Early | Recent |
| --- | ---: | ---: |
| Events | 359 | 72 |
| Event share | 4.24% | 0.86% |
| Mean excess within this tail | +377.57 pp | +351.19 pp |
| Contribution to whole-period mean | +16.02 pp | +3.03 pp |

This tail's contribution fell by 12.99 pp, about 67.17% of the observed net
19.34 pp decline. Its frequency fell sharply; average excess within the tail
changed much less. The symmetric excess-bucket identity attributes -18.10 pp
to changes in bucket shares and -1.24 pp to within-bucket means. Because buckets
are defined by outcomes, this is distribution accounting, not a predictive model.

Clipping positive event excess at +100 pp, ONLY as an influence diagnostic,
changes early/recent means to +3.49 / -5.32 pp. No baseline return is replaced.
The clipped decline is -8.81 pp rather than -19.34 pp. This is not an investable
payoff or a proposed profit-taking rule.

The stock median is +1.13% early and +2.20% recent, while the mean falls from
+21.57% to +11.34%. Median paired SPY excess is already negative early (-3.50 pp),
and 52.93% of early events underperform SPY (59.46% recent). The early positive
mean did not mean the typical breakout beat the market.

These tail, year, company and stock/SPY decompositions overlap: do NOT add their
percentage contributions as though they were separate independent causes.

## Observed composition does not explain the gap

Reconstructed relative size using positive finite raw market caps within the
frozen same-day eligible 6-1 ranking universe. No current classifications or
nominal-dollar size bucket assumptions are used. Original signal-day vol63 is
split at the fixed 20/40/60% annualized levels; missing values remain explicit.

Main-population median relative size rises from the 52.41st to 63.35th percentile;
median volatility falls from 44.68% to 38.83%; pre-signal beta median from 1.23
to 1.12. These shifts are observed, not explanations by themselves.

Symmetric size-quartile x volatility-cell decomposition, recent minus early:

| Component | Contribution |
| --- | ---: |
| Changes in observed cell shares | +0.13 pp |
| Changes in mean excess WITHIN shared cells | -19.46 pp |
| Cells present in only one period | -0.01 pp |
| Total | -19.34 pp |

15 joint cells have shared support; they cover 99.82% of early events and 100%
of recent events. Pooled-shared-mix standardized means are +16.52 / -2.96 pp,
a -19.48 pp difference. Marginal size-only and volatility-only decompositions
give the same broad message. Coarse observed size/risk composition is not the
main accounting source of the decline; within-cell differences are NOT causal
period effects and can still contain omitted sector, valuation and other shifts.
Some cells are small; this is a diagnostic standardization, not causal adjustment.

## Benchmark and sample dependence

The frozen 12-1-momentum-control subset is narrower than the full 6-1/top20 sample:

| Complete annual control sample | Early | Middle | Recent |
| --- | ---: | ---: | ---: |
| Events | 2,987 | 4,165 | 4,808 |
| Excess SPY | +6.84 pp | +2.03 pp | -0.10 pp |
| Excess over frozen matched stocks | +4.51 pp | +1.43 pp | +3.53 pp |

There is no monotonic disappearance of the relative association versus these
controls. They match 12-1 momentum, size and volatility, not the newly tested
6-1 momentum directly, and are not a randomized counterfactual.

In the even narrower COMPLETE common-CAPM subset (2,459 / 3,650 / 4,333 events),
ATH CAR averages +5.57 / +1.30 / +1.76 pp; control CAR +2.55 / -1.14 / -2.38 pp;
their difference +3.01 / +2.44 / +4.14 pp. These are descriptive CAR means on
identical rows within each comparison, not compounded annual excess or portfolio
alpha. CAR columns are suppressed in the merely annual-matched row to prevent
mixing different missing-data populations.

Thus "stopped working" depends on benchmark, sample, weights and period. No
full-sample old mean is compared with a reduced new mean as a pure factor effect.

## Uncertainty and unresolved economic causes

Crossed event-company/calendar bootstrap, 2,000 draws, fixed seed:

- Early excess +17.11 pp: 252-block interval -0.59 to +42.58 pp.
- Recent excess -2.23 pp: interval -13.54 to +10.83 pp.
- Recent minus early -19.34 pp: interval -47.23 to +3.03 pp.
- 504-session-block change interval: -47.24 to +2.64 pp (1,992 valid draws).

All include zero. The data support an observed, highly episode-sensitive mean
pattern; they do not establish a persistent structural regime shift. Approximate
bootstrap calibration, cross-company/control dependence, few long blocks, focus
selection and known-history quality exclusions remain limitations.

No PIT industry/SIC or fundamentals exist in the selected saved raw schema.
We did not test sector-mix changes, valuations, institutional adoption, crowding,
information diffusion, execution costs or why extreme winners became rarer.
Do not infer these mechanisms from the return decomposition. New evidence and
a separately scoped hypothesis would be needed for a causal economic explanation.

## Verification, repairs and files

11 relevant tests passed (five period/decomposition/bootstrap cases including
production-length index regression, six prior robustness tests); Ruff passed.
Independent verification checks saved hashes, source preservation, every main
event size percentile, period/contribution/decomposition/context arithmetic.
The verification JSON records exact counts and reviewed scope. No new full
repository suite, provider-truth audit, visual chart QA or bootstrap calibration.
The independent verifier passed 2,624 numerical reconciliations and all 23,712
main-event size percentiles; source returns, filter flags and non-overlap are
unchanged.

Two failed attempts were retained: manifest path-separator key normalization,
and an int8 categorical index overflow before bootstrap. A production-length
test now covers the latter. An initial completed diagnostic was superseded only
to suppress CAR columns with differing missingness in the annual-only context;
the explicitly complete CAR rows remain. No economic rule or main result changed.

Protocol: `research/ath/ATH_PERIOD_DIAGNOSTIC_PLAN.md`.
Code: `scripts/research/diagnose_ath_periods.py`, `scripts/research/verify_ath_periods.py`,
`src/ath_breakout/research/period_diagnostic.py`.
Output: `outputs/research/ath/ath_13_period_diagnostic_v001/20261016T211113381140Z/`.
Includes saved PIT size cross-sections, year/company/tail contributions, mix/within
identities, all omission diagnostics, matched/CAPM context, uncertainty and hashes.
All prior results remain; changes are local, without a new commit.

Practical research decision: retain the evidence that high full-history means
are episode/tail dependent. Do not rescue the result by dropping 2021 or retaining
only 1998-1999. A next causal explanation or new filter requires its own scope;
this diagnostic does not authorize another parameter search.
