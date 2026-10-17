# CAPM correction of the frozen ATH event study

Study `ath_09_capm_v001`; completed run `20261016T193755193800Z`.
Protocol: [ATH_CAPM_PLAN.md](ATH_CAPM_PLAN.md).

## Answer

The mean post-ATH CAPM abnormal return is positive, but its signal-date-block
interval includes zero. ATH has a positive event-weighted incremental abnormal
return against frozen size/volatility/momentum-matched non-ATH controls; that
interval excludes zero. However, the incremental estimate changes sign when
PERMNOs receive equal weights. We do NOT establish robust alpha attributable
to the breakout, or the Jensen alpha of an investable strategy.

## Exact estimand

Estimate an OLS slope with intercept from daily excess stock returns against
the Kenneth French Mkt-RF factor, using 252 NYSE sessions strictly before the
signal and requiring 200 valid pairs. Freeze beta, do not subtract the fitted
pre-signal intercept. Expected CAPM return = RF + beta * Mkt-RF.

Sum daily actual-minus-expected returns, i.e. CAR. Official factors are
close-to-close. The 252-session next-open gross window is still required for
validity, but its initial intraday return is excluded from CAPM: **251 complete
daily returns from entry close to prescribed exit close**. CAR is additive,
not a compounded abnormal buy-and-hold return, a per-year rate or portfolio
regression intercept. It is not directly interchangeable with earlier SPY
excess or gross matched-stock excess.

Terminal CIZ Y return counted once on the terminal day. Thereafter actual cash
return and market beta are zero; residual = -RF, reflecting the established
zero-interest cash convention. No future control replacements or beta fitting.

## Results

| Sample / metric | Events | Mean CAR or CAR difference | 95% interval, 252-session blocks |
| --- | ---: | ---: | ---: |
| All available ATH CAR | 67,213 | +2.3331 pp | -0.3267 to +5.7921 pp |
| Common ATH CAR | 39,561 | +1.6026 pp | -0.2501 to +3.6036 pp |
| Common original-control CAR | 39,561 | -1.2938 pp | See paired difference |
| Common momentum-control CAR | 39,561 | -0.6381 pp | See paired difference |
| Common ATH minus original controls | 39,561 | +2.8964 pp | +1.5315 to +4.4452 pp |
| Common ATH minus momentum controls | 39,561 | +2.2407 pp | +1.1429 to +3.5014 pp |

Common sample = 1,732 PERMNOs with valid ATH and all five old and all five new
control CARs. All-stock available = 2,374 PERMNOs. Original 75,884 signals were
preserved; 71,961 had valid annual stock/SPY outcomes, 67,213 also have CAPM
observability and pre-beta. Old CAR pairs 55,473; momentum CAR pairs 44,397.
The latter are not the same sample as common 39,561. No substitution for missing
history. 2025 signals are partial; all outcomes end by 2026-06-30.

Common mean beta: ATH 1.0459, original controls 1.0687, momentum controls 1.0886.
All available ATH beta averages 1.1232. Market beta differences do not erase the
event-weighted matched association under this model; beta can change after ATH.

504-session blocks: common ATH CAR interval -0.2307 to +3.5747 pp; incremental
momentum-control interval +0.9711 to +3.4709 pp. Fixed cooldown21 common sample
12,014: incremental +2.3169 pp, interval +1.2704 to +3.5047 pp (252 blocks).

## Stability and the material weighting warning

| Common signal period | Events | ATH CAR | Momentum-control CAR | Difference |
| --- | ---: | ---: | ---: | ---: |
| 1994-2009 | 9,783 | +4.3798 pp | +1.5358 pp | +2.8440 pp |
| 2010-2017 | 14,532 | +1.6380 pp | -0.4823 pp | +2.1203 pp |
| 2018 through full 2025 signals | 15,246 | -0.2132 pp | -2.1815 pp | +1.9683 pp |

The recent positive relative difference accompanies negative ATH CAR: beating
weak controls does not mean positive standalone CAPM alpha.

Equal-date incremental CAR is +2.8040 pp. Equal-security (average within PERMNO,
then across PERMNOs) incremental CAR is **-4.3865 pp**, and common ATH CAR itself
is -6.0647 pp. Fixed cooldown21 equal-security difference is -2.2730 pp.
These are weighting diagnostics, not investable portfolio returns. Typical-event
and typical-security means answer different questions; the sign reversal does
not mechanically invalidate the former, but calls for concentration and
dependence analysis before claiming a broad effect. The date
bootstrap does not fully handle persistent company dependence, beta-estimation
uncertainty or research selection. A positive date-block interval alone cannot
resolve the sign reversal.

## Sources and verification

CRSP raw and frozen signal/control/outcome hashes reconciled with preceding
studies. All 33 years' original and momentum-control gross and CAR baskets were
independently reconciled. 500 OLS and CAR scalar checks are recorded in manifest.
35 further independently sampled raw-data OLS/CAR reconstructions passed.
Four new unit tests cover lag, exact additive CAR, missing/minimum observations,
terminal cash/censoring and degenerate market variance. Fourteen related tests
and Ruff passed. This is not a newly executed full repository test suite.

Official daily factors downloaded and preserved:
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip
Definition:
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/f-f_factors.html
Archive SHA256 `2f29e22546069914890a712680a6f81f3680ebc3543b52864484d209ca13a7db`.
26,317 factor rows through 2026-08-31; analysis uses only through June 2026.
Factors are a current revised historical vintage, not an archived PIT release.
Market is broad US CRSP market, not SPY; RF is one-month T-bill proxy.
No WRDS connection. Only the public factor file was newly downloaded.

First run `20261016T193716095408Z` stopped by a protective assertion at 2002:
2001 had fewer than 252 sessions. Extend the available estimation calendar two
years backward, without changing the trailing 252-session rule. Failed outputs
and failure.json retained. Final rerun uses identical rules and no outcome-based
selection. Unit and production checks passed following repair.

Code: `scripts/research/study_ath_capm.py`, `fetch_capm_factors.py`,
`verify_ath_capm.py`, `src/ath_breakout/research/capm_events.py`.
Output: `outputs/research/ath/ath_09_capm_v001/20261016T193755193800Z/`.
Protocol, code, inputs and generated artifacts are hashed in manifest.json.
The separate independent_verification.json records the subsequent verification.
Changes remain local, without a new commit.
