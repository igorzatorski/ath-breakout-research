# ATH after matching on prior momentum

Study `ath_08_momentum_control_v001`; run `20261015T224210801657Z`.
Protocol: [ATH_MOMENTUM_CONTROL_PLAN.md](ATH_MOMENTUM_CONTROL_PLAN.md).

## Finding

Matching on one fixed prior-momentum measure did not erase the positive
event-weighted annual ATH-minus-control mean. It reduced the estimate by
0.49 percentage points on the same 43,824 events (1,813 securities).
That reduction's date-block interval includes zero. This is not proof that
momentum explains the ATH effect, or that ATH has persistent causal alpha.

| Same events; 252 sessions | Mean return |
| --- | ---: |
| ATH stocks | 11.2457% |
| Same-window SPY | 10.1981% |
| Original size/volatility controls | 8.9525% |
| New size/volatility/momentum controls | 9.4473% |
| ATH minus original controls | +2.2932 pp |
| ATH minus new controls | +1.7984 pp |
| Change in excess | -0.4948 pp |

Gross arithmetic event means, not portfolio returns or risk-adjusted alpha.
The +1.80 pp comparison is against matched stocks; excess over SPY on these
same events is +1.05 pp. Do not label +1.80 pp as excess over the S&P 500.

## Uncertainty and stability

Circular signal-date bootstrap, 2,000 draws, fixed seed; 252-session blocks:
new excess interval +0.4829 to +3.5737 pp. With 504-session blocks:
+0.3995 to +3.5300 pp. Change versus original controls: -1.1861 to +0.3790 pp
(252 blocks), -1.1975 to +0.3239 pp (504 blocks).

Positive date-block intervals are qualified by repeated company dependence,
retrospective selection of the annual horizon, and weighting instability.
Equal-security new excess is **-4.6838 pp**, whereas equal-date new excess is
+2.6984 pp. Equal-security first averages within each PERMNO, then across
PERMNOs; this is not an equal-weight investable portfolio. The sign reversal
prevents treating the event-weighted interval as broadly robust evidence.

| Signal period; common events | Events | Old excess | New excess |
| --- | ---: | ---: | ---: |
| 1994-2009 | 11,251 | +2.9383 pp | +3.5583 pp |
| 2010-2017 | 16,014 | +1.9165 pp | +1.0381 pp |
| 2018 through complete 2025 signals | 16,559 | +2.2193 pp | +1.3379 pp |

Frozen cooldown21 sensitivity: 13,380 common events; new excess +1.8091 pp;
252-block interval +0.5051 to +3.6046 pp. Equal-security excess still negative
(-2.3534 pp). No cooldown or momentum parameters were tuned.

## Matching and coverage

Momentum compounds 231 scheduled daily CRSP returns ending 21 sessions before
signal close. Maximum control/event difference: 10 pp; original size and vol
calipers remain, five distinct PERMCOs excluding the event company.

Within common events, mean absolute pairwise momentum gap fell from 32.55 pp
to 4.75 pp. Mean signed control-minus-event gap fell from -13.24 pp to -0.75 pp.
Original controls have 6,553 missing momentum values among 219,120 pairs;
old gap statistics therefore use 212,567 finite pairs. All 219,120 new pairs
have observed momentum. Event momentum averages 38.72%, new controls 37.97%.
Finite calipers do not establish perfect feature balance or causal isolation.

75,884 frozen events were reconstructed. 44,397 have valid new stock/SPY/control
annual outcomes; 43,824 also have complete original control outcomes. No controls
were replaced after seeing future validity. The original full annual matched
sample had 67,803 events and +3.4753 pp control excess. The drop to +2.2932 pp
before adding momentum is a sample-composition change, not a momentum effect.
Inference applies to matchable events, not the excluded extreme-momentum/young
stocks or all US equities. 2025 is partial through June 27; data end June 2026.

## Verification and reproducibility

All years' frozen event identities, size/vol/ADV/prior-high features and original
control selections were reproduced and checked. Original input SHA256 values
and frozen annual artifact hashes matched. Three new unit tests and ten related
tests passed; Ruff passed. Production control-return scalar/vector checks are
recorded in manifest.json. Independent verification passed artifact hashes,
paired arithmetic, sampled basket/caliper/company checks and 40 direct
production momentum products. No WRDS connection or download was used.

The independent verifier initially compared control differences on missing-stock
rows; its check was corrected to preserve those undefined event differences.
No study outcomes were changed by this verification correction.

Run `.venv/Scripts/python.exe scripts/research/control_ath_momentum.py`.
Verify with `scripts/research/verify_ath_momentum.py` and the output directory.
Artifacts: `outputs/research/ath/ath_08_momentum_control_v001/20261015T224210801657Z/`.
Includes event returns, fixed match IDs/diagnostics, calendar-year summaries,
coverage, balance, uncertainty and hash manifest. Changes remain local.

Conclusion: the tested momentum definition alone does not explain away the
event-weighted ATH association. Its economic reliability remains unresolved,
especially company weighting and dependence. Do not start parameter searches
or a portfolio from this finding alone.
