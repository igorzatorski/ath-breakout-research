# Annual ATH baseline: concentration, repeats and coverage

Study: `ath_10_baseline_robustness_v001`.
Run: `20261016T200336849055Z`.
Protocol: [ATH_BASELINE_ROBUSTNESS_PLAN.md](ATH_BASELINE_ROBUSTNESS_PLAN.md).

## Decision

The saved baseline is usable as a conditional, exploratory reference for a small
predeclared feature study. A broad, reliable ATH premium over SPY is NOT established.
Event recurrence, positive-tail concentration and non-neutral sample attrition
are material. A relative CAPM-adjusted association against matched controls remains
interesting under these diagnostics, but is not proven investable or causal alpha.

Retain the original all-event results. The non-overlap variant is a fixed sampling
sensitivity, not a newly selected superior strategy. A separately motivated filter
hypothesis is permissible even without a positive unconditional ATH premium.

## What changed

Nothing in the frozen signal, entry, stock/control returns or historical exclusions.
Read the saved annual, momentum and CAPM outputs; verify their hashes and identity
joins. Group signals by historical PERMCO as well as PERMNO. No WRDS connection,
new download, filter, stop, factor specification or portfolio was introduced.

Select from all 75,884 qualified source signals before observing future validity:
earliest signal per PERMCO, subsequent signal at least 252 NYSE sessions later;
same-date ties use lowest PERMNO/event ID. Skipped signals never reset the clock.
7,463 source signals are retained; 7,074 have valid annual stock/SPY windows.
This removes scheduled same-PERMCO annual-window overlap, not dependence between
companies, different historical company identities, or reused controls.

## Main comparisons

Each row uses its own frozen complete population; the retained subset changes
observation weights and composition. These are gross event means, not portfolios.
CAR is additive over 251 full daily residuals, not the compounded annual return.

| Sample and metric | Baseline events | Baseline excess | Retained events | Retained excess |
| --- | ---: | ---: | ---: | ---: |
| Annual stock minus same-window SPY | 71,961 | +2.5499 pp | 7,074 | +0.9565 pp |
| Common annual stock minus momentum controls | 43,824 | +1.7984 pp | 4,313 | +2.5849 pp |
| Common CAPM CAR minus momentum-control CAR | 39,561 | +2.2407 pp | 3,840 | +2.6523 pp |

Full annual stock/SPY means: baseline +12.6411% / +10.0911%; retained +11.5414% /
+10.5848%. Retained median paired excess is -4.7877 pp. The raw market comparison
weakens after repeat suppression, while relative matched comparisons do not.

## Weighting and periods

| Metric | Baseline equal-PERMNO | Retained equal-PERMNO | Retained equal-PERMCO |
| --- | ---: | ---: | ---: |
| Annual excess SPY | -19.5396 pp | -6.1686 pp | -6.2519 pp |
| Annual excess momentum controls | -4.6838 pp | +1.7537 pp | +1.9014 pp |
| CAPM incremental CAR | -4.3865 pp | +1.1263 pp | +1.2922 pp |

The earlier weighting sign reversal is materially altered by annual repeat
suppression in the narrower matched populations. This does not establish that
one weighting is correct or that selection improves an investable strategy.
Companies with more observed breakouts have higher mean excess in this history:
company event-count/mean-excess Spearman correlation is 0.6085 for annual SPY
excess, 0.3131 for momentum excess and 0.2191 for incremental CAPM CAR.
These are descriptive relationships, not causal explanations.

| Signal period | Baseline annual excess SPY | Retained annual excess SPY |
| --- | ---: | ---: |
| 1994-2009 | +9.2244 pp | +5.1290 pp |
| 2010-2017 | +0.6833 pp | +0.2122 pp |
| 2018 through complete 2025 signals | -2.8113 pp | -3.4696 pp |

Retained annual momentum-control excess by these periods: +5.1643, +1.2751 and
+1.6983 pp. In the recent period its equal-PERMNO counterpart is -0.6860 pp.
Thus even the more favorable matched result is not uniformly robust to weights.
All history is previously inspected; these are stability checks, not fresh OOS.

## Concentration and influence

For each company, contribution = sum of event paired excess / all sample events.
Contributions sum exactly to the event-weighted mean. All original events stay in
the baseline; retrospective deletions below are influence diagnostics only.

For annual excess over SPY:

- Top 10 companies by net contribution: 996 events (1.3841% of the sample),
  contribution +2.0107 pp; the remaining mean is +0.5468 pp.
- Top 20: 1,541 events (2.1414%), contribution +3.1237 pp; remaining mean -0.5863 pp.
- These top 20 account for 18.5681% of all positive event excess, not all gains.
  Their contribution exceeds the overall +2.5499 pp because other contributions
  offset one another. Net-mean sensitivity is not proof that only 20 firms work.
- Largest positive company contributors include historical SDLI, YHOO, AMCC,
  DELL and QCOM. Labels are descriptive historical tickers, not entry features.
  Largest negative contributors include CRUS, Z/ZG, MSTR and KMX.

Concentration is weaker in the narrower controls: removing the top 20 companies
retrospectively leaves +0.3000 pp annual momentum excess and +1.2239 pp incremental
CAPM CAR. These are neither proposed filters nor independent significance tests.
Full positive/negative contributor tables by PERMNO and PERMCO are saved.

## Approximate dependence-aware uncertainty

2,000 draws, seed 20261016. Crossed bootstrap independently resamples historical
event PERMCOs and circular calendar blocks, using joint weights for baseline,
retained and their difference. Exactly the original calendar length is sampled;
the final block is truncated. The new date-only estimates need not exactly match
earlier seeds/last-block conventions. No original intervals were overwritten.

| Metric | Baseline 95% interval | Retained 95% interval | Retained minus baseline interval |
| --- | --- | --- | --- |
| Annual excess SPY | -2.5613 to +9.5140 pp | -4.2080 to +7.5218 pp | -4.2960 to +0.5584 pp |
| Annual excess momentum controls | -0.1669 to +4.2894 pp | -0.0403 to +6.0339 pp | -1.0034 to +2.7361 pp |
| Incremental CAPM CAR | +0.4882 to +3.9916 pp | +0.6493 to +4.7857 pp | -1.1977 to +2.1848 pp |

Above: 252-session blocks. At 504 sessions, SPY intervals still include zero,
baseline momentum excess still includes zero, retained momentum excess has a
slightly positive lower bound (+0.1432 pp), and incremental CAR stays positive.
Do not choose whichever block yields a preferred conclusion. All change intervals
include zero. The narrow momentum result is sensitive around the zero boundary.

These are approximate diagnostic intervals, not fully calibrated inference.
Event-company resampling does not independently capture the complete network of
reused control companies, and beta-estimation uncertainty, sparse crossed cells,
few long calendar blocks and research selection remain. No alpha proof follows.

## Coverage and selection

Replayed the original history gate across every year 1994-2026 using local raw
history, the corrected high seed and PIT memberships. Reconciled all qualified
event identities, eligible-stock-day counts and uncertain candidate counts.

- 75,884 qualified signals; 76,943 additional uncertain-history potential
  candidates. The latter are not certified ATHs; no ATH return claim is made for
  them. Candidate counts cannot establish how many genuine ATHs were missed.
- Annual qualified outcomes: 71,961 valid; 3,505 censored, 243 invalid paths,
  175 missing entries. The 2025 annual cohort has 879 complete events; 2026 has
  none. Do not classify recent right-censoring as historical data failure.
- Uncertain candidates differ from qualified signals: aggregate median vol63
  26.45% versus 31.09%; lower volatility in 31 of 33 individual years.
  Median market cap is larger in 25 of 33 years. The quality gate changes the
  population; it is not demonstrated to be a neutral random exclusion.
- Among valid annual stock/SPY events, 67,803 have complete original controls;
  44,397 have complete momentum controls. Momentum matching excludes 27,564
  otherwise valid stock/SPY events. Median volatility is 26.58% in the matched
  group versus 44.71% in the excluded group. Observed SPY excess is +1.09 versus
  +4.90 pp. This is composition, not the causal effect of momentum adjustment.
- CAPM is available for 67,213 annual events, not 4,748 others. Their median
  volatilities are 29.98% versus 50.81%, and observed annual SPY excess is +2.91
  versus -2.50 pp. CAPM availability also changes the population.
- Common old/new momentum and CAPM comparisons remain 43,824 and 39,561;
  do not silently treat the 44,397 or 67,213 available samples as those common sets.

Coverage tables include yearly funnels, status counts, aggregate feature
quantiles and within-year feature medians. We have not repaired the excluded
histories, independently established every post-1993 listing inception, or
established representativeness for the entire US market.

## Verification and files

15 relevant tests passed (6 new robustness, 6 prior selection and 3 annual-return
tests); Ruff passed. Independent verifier: 88,313 aggregation/selection checks,
all saved artifact hashes, and 50 scalar annual stock-return reconstructions from
raw daily data including the largest positive/negative event outcomes; maximum
absolute return discrepancy 6.6e-14. This is not a fresh full repository suite,
provider-truth audit, or calibration proof for bootstrap coverage.

Code: `scripts/research/audit_ath_baseline.py`, `verify_ath_baseline.py`,
`src/ath_breakout/research/baseline_robustness.py`.
Outputs: `outputs/research/ath/ath_10_baseline_robustness_v001/20261016T200336849055Z/`.
Primary manifest covers the production artifacts. The subsequent
`independent_verification.json` hashes the verifier and additional
`history_features_by_year.csv`. Existing runs are preserved; no new commit.

Next proposed task: freeze one economically motivated feature definition and a
small set of ordered groups, using the all-event annual baseline plus the fixed
non-overlap sensitivity and same-window SPY. Track sample eligibility and paired
controls explicitly. Do not optimize or implement that filter in this study.
