# Candidate filter overlap and combinations — full exploratory results

Study: `ath_26_filter_combinations_v001`, completed2026-10-17.
Run: `outputs/research/ath/ath_26_filter_combinations_v001/20261017T133039984401Z`.
Protocol: `research/ath/ATH_FILTER_COMBINATIONS_PLAN.md`.

## Main finding

Combining previously inspected candidates changes average annual outcomes, but adding more filters does not automatically improve selection. Volume plus breakout strength gives +11.90 pp SPY excess versus +5.58 pp base, with more large winners and more losses. Adding the main63-session contraction filter lowers this pair to+9.47 pp. A fixed42-session neighbor plus high volume has the highest mean among configurations meeting the prespecified overall support flag: +14.67 pp on1,311 events, but its recent excess is-0.67 pp and repetition sensitivity lowers its mean. The absolute highest81-grid mean is+26.05 pp on only64 events and is not a defensible optimum.

All81 configurations,16 main combinations,404 mean contrasts, source overlap, distribution, historical periods, repeat and concentration diagnostics were saved. None of the main all-event pointwise improvement/addition/neighbor intervals excludes zero positively at either block length. No simultaneous family confirms a benefit. This does not erase positive historical associations; it limits the conclusion that they provide durable independent return information.

## Fixed foundation and configuration decoder

Foundation is original ATH + common6-1 market momentum/top20, not unfiltered ATH. Same25,250 source events and all23,712 annual stock/SPY pairs; every needed feature is available, so there are no common-support exclusions. Frozen next-open entry,252-session outcomes including distributions/terminal cash and original company nonoverlap are unchanged. Gross event means are not portfolio CAGR, net returns or CAPM alpha. No price download or WRDS connection was made.

Each code CxVyAzBw uses four fixed dimensions:

| Letter | 0 | 1: fixed neighbor | 2: main setting |
| --- | --- | --- | --- |
| C | Off | 42+42 sessions; later/earlier closing range <=0.75 | 63+63 sessions; later/earlier closing range <=0.75 |
| V | Off | Signal volume >=1.5x prior63 mean | Signal volume >=2x prior63 mean |
| A | Off | Prior ATH creation age >=126 sessions | Prior ATH creation age >=252 sessions |
| B | Off | ATH close overshoot >=0.5 priorATR20 | ATH close overshoot >=1.0 priorATR20 |


Main16 use only0 or2. The full fixed neighborhood uses0/1/2 in each dimension:81, including the reference. Existing candidate definitions were chosen after prior studies, not as untouched hypotheses or proven optima. There was no search over every historical parameter combination and no change to the neighborhood after outcomes.

## All16 main combinations

Stock/SPY percentages use exactly matched event windows. Excess and improvement are percentage points. Limited support was prespecified as fewer than200 events or50 companies, a reporting caution rather than a proof threshold.

| Configuration | Events | Companies | Stock % | SPY % | Excess pp | Improvement pp | Limited support |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C0V0A0B0 | 23712 | 1857 | 15.47 | 9.89 | 5.58 | +0.00 | False |
| C0V0A0B2 | 3391 | 1234 | 21.17 | 10.89 | 10.28 | +4.70 | False |
| C0V0A2B0 | 405 | 363 | 19.05 | 11.32 | 7.72 | +2.14 | False |
| C0V0A2B2 | 118 | 116 | 26.78 | 13.17 | 13.60 | +8.02 | True |
| C0V2A0B0 | 4309 | 1371 | 18.62 | 9.69 | 8.94 | +3.36 | False |
| C0V2A0B2 | 1834 | 957 | 22.37 | 10.47 | 11.90 | +6.32 | False |
| C0V2A2B0 | 199 | 190 | 21.03 | 12.07 | 8.96 | +3.38 | True |
| C0V2A2B2 | 104 | 102 | 28.32 | 13.39 | 14.93 | +9.35 | True |
| C2V0A0B0 | 6537 | 1275 | 18.49 | 10.30 | 8.18 | +2.61 | False |
| C2V0A0B2 | 1008 | 637 | 23.22 | 11.31 | 11.91 | +6.33 | False |
| C2V0A2B0 | 124 | 120 | 16.05 | 10.59 | 5.46 | -0.12 | True |
| C2V0A2B2 | 45 | 45 | 23.15 | 10.56 | 12.59 | +7.01 | True |
| C2V2A0B0 | 1278 | 729 | 19.42 | 10.29 | 9.13 | +3.55 | False |
| C2V2A0B2 | 562 | 423 | 20.51 | 11.05 | 9.47 | +3.89 | False |
| C2V2A2B0 | 74 | 74 | 18.28 | 10.22 | 8.06 | +2.48 | True |
| C2V2A2B2 | 44 | 44 | 22.75 | 10.20 | 12.56 | +6.98 | True |


All four main conditions retain only44 events. Their+12.56 pp mean does not justify a four-filter strategy: it has fewer than50 companies and only5 final>=100% winners, retaining0.31% of the reference's1,598 winners. Strong selection can discard almost the entire useful tail.

## Fixed neighbors: highest means with adequate overall support

These rows are selected for discussion after seeing the complete81-grid. They are not independently validated winners. Overall support does not guarantee adequate period or nonoverlap sample sizes.

| Configuration | Events | Companies | Stock % | SPY % | Excess pp | Improvement pp | Limited support |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1V2A0B0 | 1311 | 747 | 24.50 | 9.83 | 14.67 | +9.09 | False |
| C1V1A0B2 | 824 | 552 | 24.23 | 11.06 | 13.17 | +7.59 | False |
| C1V2A0B2 | 638 | 465 | 23.95 | 11.07 | 12.88 | +7.30 | False |
| C1V0A0B2 | 1147 | 683 | 24.23 | 11.42 | 12.81 | +7.23 | False |
| C2V0A0B2 | 1008 | 637 | 23.22 | 11.31 | 11.91 | +6.33 | False |
| C0V2A0B2 | 1834 | 957 | 22.37 | 10.47 | 11.90 | +6.32 | False |
| C0V1A0B2 | 2478 | 1087 | 22.19 | 10.62 | 11.57 | +5.99 | False |
| C1V1A0B0 | 2279 | 986 | 21.35 | 9.80 | 11.54 | +5.97 | False |


48 of81 configurations are flagged limited support. The highest mean over all81 is C1V2A1B2:64 events,62 companies, excess+26.05 pp, improvement+20.47 pp with pointwise interval-6.56 to+54.84 pp. It should not be ranked as the best investable rule. The difference between C42 andC63 is a material parameter sensitivity rather than a smooth gradient.

## What the overlap says

Main volume V2 and strength B2 have the strongest positive association among the main indicators: phi0.380 and Jaccard31.26%;1,834 events pass both. Of strong breakouts,54.08% have >=2x volume. Other main pairs have phi roughly0.009-0.106; they select different subsets but this does not establish independent predictive information. MainC42 andC63 contraction neighbors overlap on only25.25% of their union, so they are not equivalent selections or nested filters.

Overlap is assessed without returns. Conditional outcome contrasts are needed separately; low indicator correlation is not evidence that combining the indicators adds alpha.

## Conditional additions: the main practical result

On the same observations, B2 alone gives+10.28 pp excess. Adding V2 raises it to+11.90 pp, conditional gain+1.62 pp; interval-4.51 to+9.59 pp. Adding C2 toB2 instead gives+11.91 pp, conditional+1.64 pp; interval-10.16 to+20.01 pp. Adding C2 on top of V2+B2 reduces+11.90 to+9.47 pp, conditional-2.43 pp; interval-17.18 to+12.92 pp. Standalone filter gains therefore cannot be added together.

Age restrictions are genuinely selective and many selected signals are already nonoverlapping. Their combinations often contain fewer than200 events. This is insufficient support for an optimum even when means look attractive. All216 addition contrasts and108 fixed-neighbor replacements are retained, including negative changes.

## Time and repetition sensitivity

Rows below are descriptive results on already inspected history. Early=1994-2009, middle=2010-2017, recent=2018-partial2025. The recent period is not a fresh holdout.

| Weighting | Period | Configuration | Events | Excess pp | Improvement pp |
| --- | --- | --- | --- | --- | --- |
| all | all | C0V0A0B0 | 23712 | 5.58 | +0.00 |
| all | all | C0V0A0B2 | 3391 | 10.28 | +4.70 |
| all | all | C0V2A0B2 | 1834 | 11.90 | +6.32 |
| all | all | C1V1A0B2 | 824 | 13.17 | +7.59 |
| all | all | C1V2A0B0 | 1311 | 14.67 | +9.09 |
| all | all | C2V0A0B2 | 1008 | 11.91 | +6.33 |
| all | all | C2V2A0B2 | 562 | 9.47 | +3.89 |
| all | all | C2V2A2B2 | 44 | 12.56 | +6.98 |
| all | early | C0V0A0B0 | 8462 | 17.11 | +0.00 |
| all | early | C0V0A0B2 | 1504 | 23.22 | +6.11 |
| all | early | C0V2A0B2 | 778 | 27.36 | +10.25 |
| all | early | C1V1A0B2 | 329 | 32.76 | +15.65 |
| all | early | C1V2A0B0 | 552 | 33.67 | +16.56 |
| all | early | C2V0A0B2 | 405 | 32.24 | +15.13 |
| all | early | C2V2A0B2 | 212 | 30.18 | +13.07 |
| all | early | C2V2A2B2 | 12 | 35.40 | +18.29 |
| all | middle | C0V0A0B0 | 6892 | 0.90 | +0.00 |
| all | middle | C0V0A0B2 | 830 | 1.15 | +0.26 |
| all | middle | C0V2A0B2 | 477 | 0.47 | -0.43 |
| all | middle | C1V1A0B2 | 233 | -1.01 | -1.90 |
| all | middle | C1V2A0B0 | 384 | 2.34 | +1.44 |
| all | middle | C2V0A0B2 | 281 | -0.49 | -1.38 |
| all | middle | C2V2A0B2 | 166 | -3.57 | -4.47 |
| all | middle | C2V2A2B2 | 12 | -14.13 | -15.03 |
| all | recent | C0V0A0B0 | 8358 | -2.23 | +0.00 |
| all | recent | C0V0A0B2 | 1057 | -0.97 | +1.26 |
| all | recent | C0V2A0B2 | 579 | 0.53 | +2.77 |
| all | recent | C1V1A0B2 | 262 | 1.19 | +3.42 |
| all | recent | C1V2A0B0 | 375 | -0.67 | +1.57 |
| all | recent | C2V0A0B2 | 322 | -2.84 | -0.60 |
| all | recent | C2V2A0B2 | 184 | -2.63 | -0.39 |
| all | recent | C2V2A2B2 | 20 | 14.86 | +17.10 |
| nonoverlap | all | C0V0A0B0 | 1725 | 3.64 | +0.00 |
| nonoverlap | all | C0V0A0B2 | 347 | 9.10 | +5.46 |
| nonoverlap | all | C0V2A0B2 | 282 | 10.81 | +7.17 |
| nonoverlap | all | C1V1A0B2 | 123 | 10.36 | +6.72 |
| nonoverlap | all | C1V2A0B0 | 230 | 6.69 | +3.04 |
| nonoverlap | all | C2V0A0B2 | 114 | 14.71 | +11.07 |
| nonoverlap | all | C2V2A0B2 | 93 | 10.64 | +7.00 |
| nonoverlap | all | C2V2A2B2 | 44 | 12.56 | +8.91 |
| nonoverlap | early | C0V0A0B0 | 610 | 10.91 | +0.00 |
| nonoverlap | early | C0V0A0B2 | 123 | 20.86 | +9.96 |
| nonoverlap | early | C0V2A0B2 | 97 | 30.73 | +19.83 |
| nonoverlap | early | C1V1A0B2 | 37 | 14.92 | +4.01 |
| nonoverlap | early | C1V2A0B0 | 89 | 10.58 | -0.33 |
| nonoverlap | early | C2V0A0B2 | 40 | 30.92 | +20.01 |
| nonoverlap | early | C2V2A0B2 | 33 | 34.77 | +23.87 |
| nonoverlap | early | C2V2A2B2 | 12 | 35.40 | +24.50 |
| nonoverlap | middle | C0V0A0B0 | 494 | -0.39 | +0.00 |
| nonoverlap | middle | C0V0A0B2 | 108 | 5.45 | +5.84 |
| nonoverlap | middle | C0V2A0B2 | 90 | 2.47 | +2.86 |
| nonoverlap | middle | C1V1A0B2 | 46 | 8.01 | +8.39 |
| nonoverlap | middle | C1V2A0B0 | 71 | 9.30 | +9.69 |
| nonoverlap | middle | C2V0A0B2 | 33 | 0.16 | +0.54 |
| nonoverlap | middle | C2V2A0B2 | 25 | -16.68 | -16.29 |
| nonoverlap | middle | C2V2A2B2 | 12 | -14.13 | -13.75 |
| nonoverlap | recent | C0V0A0B0 | 621 | -0.29 | +0.00 |
| nonoverlap | recent | C0V0A0B2 | 116 | 0.03 | +0.32 |
| nonoverlap | recent | C0V2A0B2 | 95 | -1.62 | -1.33 |
| nonoverlap | recent | C1V1A0B2 | 40 | 8.85 | +9.14 |
| nonoverlap | recent | C1V2A0B0 | 70 | -0.92 | -0.63 |
| nonoverlap | recent | C2V0A0B2 | 41 | 10.61 | +10.90 |
| nonoverlap | recent | C2V2A0B2 | 35 | 7.40 | +7.69 |
| nonoverlap | recent | C2V2A2B2 | 20 | 14.86 | +15.15 |


C1V2A0B0 (42-session contraction plus high volume) gives full mean+14.67 pp, early+33.67 pp, middle+2.34 pp and recent-0.67 pp. Its original nonoverlap mean is+6.69 pp versus+3.64 pp reference; recent nonoverlap-0.92 pp versus-0.29 pp. Strong earlier cohorts remain influential.

V2+B2 gives full+11.90 pp, early+27.36 pp, middle+0.47 pp and recent+0.53 pp. Original nonoverlap gives+10.81 pp versus+3.64 pp reference, but recent nonoverlap-1.62 pp versus-0.29 pp on only95 events. This sample/period sensitivity prevents a claim of a robust current edge.

Some neighbor combinations have more favorable repeat descriptions. C1V1A0B2 has+13.17 pp full mean, recent+1.19 pp and nonoverlap+10.36 pp; its recent nonoverlap+8.85 pp is based on only40 events. These remain candidates for review, not evidence to switch the main methodology after results.

## Distribution and concentration

The high-mean supported C1V2A0B0 cell has median stock return5.25% versus3.66% base, losses43.40% versus44.60%, final>=100% frequency10.07% versus6.74%, and skew4.87 versus4.36. However, it retains only132 of1,598 doublers (8.26%). Five companies account for63.25% of its net excess contribution; removing them as a hindsight stress test lowers excess to+5.50 pp. This removal is not a proposed entry or exit rule.

V2+B2 has median1.25%, losses47.60%, final>=100% frequency10.69% and retains196 doublers (12.27%). Higher mean and winner frequency therefore come with a worse typical outcome. Its five largest positive-contributing companies account for61.72% of net excess, versus51.94% in the base. No loss-cutting rule was tested.

All-four main C2V2A2B2 has top-five positive contribution greater than its net total (131.09%, possible because losers offset gains). Removing those five companies yields-4.40 pp excess. Its apparent strength is highly concentrated. Leave-one-company/year ranges, company/date weights and tail contribution files are retained for all81.

## Uncertainty and research search

Stored joint bootstrap draws:2,000 each for all/nonoverlap at252/504-session blocks, seed20261017. All404 contrast definitions reuse the same draws:80 versus baseline,216 additions,108 neighbor replacements. Simultaneous15-main,80-grid,32-main-addition and404-full-contrast sensitivities are saved. Sparse cells make family bands very wide; do not drop them retrospectively to obtain significance. The bootstrap is approximate and these corrections cannot undo the retrospective candidate choice or entire earlier research search.

There is one isolated positive pointwise lower bound among secondary nonoverlap504 addition contrasts: adding A1 toC1V2A0B2 gives+16.28 pp with interval+0.09 to+39.39 pp. It does not repeat at252 blocks and fails simultaneous correction (full404 lower-33.53 pp). All-event primary contrasts have no positive lower bound at either block length. This isolated result is retained, not presented as confirmation.

## Verification and saved artifacts

Independent audit passed 128,304 summary/tail checks, 1,296 concentration checks, 25,856 stored-draw interval/family checks and 972 directly reconstructed bootstrap estimates. Raw prior feature artifacts and hashes reconcile; all intersections, source identities/outcomes, overlap, signatures, count partitions and conditional edge definitions reconcile. Ten focused combination/prior-feature tests passed; Ruff passed for new code/test files. This is not a full repository test-suite claim.

Protocol, runner, verifier, module and tests:
- `research/ath/ATH_FILTER_COMBINATIONS_PLAN.md`
- `scripts/research/study_ath_filter_combinations.py`
- `scripts/research/verify_ath_filter_combinations.py`
- `src/ath_breakout/research/filter_combinations.py`
- `tests/research/test_filter_combinations.py`

Artifacts: events.parquet, coverage.csv, overlap.csv, exclusive_signatures.csv, pass_counts.csv, contrast_definitions.csv, summary.csv, concentration.csv, uncertainty.csv, four draws_*.npz files, manifest.json and independent_verification.json. No sources or prior studies were overwritten.

## Decision

There are descriptive leads, particularly volume/strength and42-session contraction combinations, but no single stable optimum or validated current edge. Avoid mandatory four-filter stacking. Preserve a small set of economically distinct candidates and their simpler parents; do not continue expanding the grid to seek a positive interval. The next decision is which fixed candidates merit a separately specified validation/backtest stage, after the user's review of these event results. All inspected history remains known data; a frozen rule needs uninspected validation and eventual costs/execution/portfolio assessment. Those stages were not executed here.

## Appendix: all81 configurations

| Configuration | Events | Companies | Stock % | SPY % | Excess pp | Improvement pp | Limited support |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C0V0A0B0 | 23712 | 1857 | 15.47 | 9.89 | 5.58 | +0.00 | False |
| C0V0A0B1 | 8920 | 1617 | 18.54 | 10.23 | 8.30 | +2.72 | False |
| C0V0A0B2 | 3391 | 1234 | 21.17 | 10.89 | 10.28 | +4.70 | False |
| C0V0A1B0 | 487 | 423 | 18.09 | 10.95 | 7.14 | +1.56 | False |
| C0V0A1B1 | 230 | 222 | 20.61 | 11.32 | 9.29 | +3.71 | False |
| C0V0A1B2 | 137 | 133 | 26.05 | 12.84 | 13.21 | +7.64 | True |
| C0V0A2B0 | 405 | 363 | 19.05 | 11.32 | 7.72 | +2.14 | False |
| C0V0A2B1 | 193 | 189 | 20.15 | 11.64 | 8.50 | +2.93 | True |
| C0V0A2B2 | 118 | 116 | 26.78 | 13.17 | 13.60 | +8.02 | True |
| C0V1A0B0 | 7669 | 1583 | 17.95 | 9.52 | 8.43 | +2.85 | False |
| C0V1A0B1 | 4569 | 1386 | 20.00 | 9.98 | 10.02 | +4.44 | False |
| C0V1A0B2 | 2478 | 1087 | 22.19 | 10.62 | 11.57 | +5.99 | False |
| C0V1A1B0 | 303 | 283 | 21.54 | 11.33 | 10.21 | +4.63 | False |
| C0V1A1B1 | 189 | 184 | 22.00 | 11.75 | 10.25 | +4.67 | True |
| C0V1A1B2 | 128 | 125 | 27.55 | 13.22 | 14.33 | +8.75 | True |
| C0V1A2B0 | 254 | 239 | 23.37 | 11.98 | 11.39 | +5.81 | False |
| C0V1A2B1 | 157 | 154 | 22.67 | 12.62 | 10.05 | +4.47 | True |
| C0V1A2B2 | 109 | 107 | 28.60 | 13.66 | 14.94 | +9.36 | True |
| C0V2A0B0 | 4309 | 1371 | 18.62 | 9.69 | 8.94 | +3.36 | False |
| C0V2A0B1 | 2899 | 1203 | 20.03 | 9.97 | 10.05 | +4.48 | False |
| C0V2A0B2 | 1834 | 957 | 22.37 | 10.47 | 11.90 | +6.32 | False |
| C0V2A1B0 | 237 | 225 | 19.58 | 11.05 | 8.53 | +2.95 | False |
| C0V2A1B1 | 166 | 161 | 22.68 | 11.33 | 11.36 | +5.78 | True |
| C0V2A1B2 | 122 | 119 | 27.00 | 12.96 | 14.04 | +8.47 | True |
| C0V2A2B0 | 199 | 190 | 21.03 | 12.07 | 8.96 | +3.38 | True |
| C0V2A2B1 | 138 | 135 | 24.22 | 12.63 | 11.59 | +6.01 | True |
| C0V2A2B2 | 104 | 102 | 28.32 | 13.39 | 14.93 | +9.35 | True |
| C1V0A0B0 | 7298 | 1350 | 18.03 | 10.45 | 7.58 | +2.00 | False |
| C1V0A0B1 | 2825 | 1069 | 20.38 | 10.75 | 9.64 | +4.06 | False |
| C1V0A0B2 | 1147 | 683 | 24.23 | 11.42 | 12.81 | +7.23 | False |
| C1V0A1B0 | 182 | 174 | 22.40 | 9.71 | 12.69 | +7.11 | True |
| C1V0A1B1 | 99 | 97 | 27.79 | 9.42 | 18.37 | +12.79 | True |
| C1V0A1B2 | 66 | 64 | 35.84 | 10.85 | 24.99 | +19.41 | True |
| C1V0A2B0 | 146 | 141 | 24.00 | 9.69 | 14.31 | +8.73 | True |
| C1V0A2B1 | 78 | 76 | 30.36 | 10.01 | 20.35 | +14.77 | True |
| C1V0A2B2 | 55 | 53 | 35.45 | 11.13 | 24.32 | +18.74 | True |
| C1V1A0B0 | 2279 | 986 | 21.35 | 9.80 | 11.54 | +5.97 | False |
| C1V1A0B1 | 1449 | 798 | 20.36 | 10.10 | 10.26 | +4.68 | False |
| C1V1A0B2 | 824 | 552 | 24.23 | 11.06 | 13.17 | +7.59 | False |
| C1V1A1B0 | 130 | 127 | 28.89 | 10.46 | 18.43 | +12.85 | True |
| C1V1A1B1 | 91 | 89 | 30.26 | 9.57 | 20.68 | +15.10 | True |
| C1V1A1B2 | 65 | 63 | 36.17 | 10.92 | 25.25 | +19.67 | True |
| C1V1A2B0 | 105 | 102 | 31.02 | 10.72 | 20.30 | +14.72 | True |
| C1V1A2B1 | 72 | 70 | 33.12 | 10.55 | 22.57 | +16.99 | True |
| C1V1A2B2 | 54 | 52 | 35.83 | 11.21 | 24.63 | +19.05 | True |
| C1V2A0B0 | 1311 | 747 | 24.50 | 9.83 | 14.67 | +9.09 | False |
| C1V2A0B1 | 947 | 621 | 20.91 | 10.03 | 10.88 | +5.30 | False |
| C1V2A0B2 | 638 | 465 | 23.95 | 11.07 | 12.88 | +7.30 | False |
| C1V2A1B0 | 110 | 107 | 30.60 | 9.99 | 20.61 | +15.03 | True |
| C1V2A1B1 | 84 | 82 | 31.32 | 9.84 | 21.48 | +15.90 | True |
| C1V2A1B2 | 64 | 62 | 36.86 | 10.81 | 26.05 | +20.47 | True |
| C1V2A2B0 | 87 | 84 | 33.83 | 10.52 | 23.31 | +17.73 | True |
| C1V2A2B1 | 66 | 64 | 34.05 | 11.06 | 22.99 | +17.41 | True |
| C1V2A2B2 | 53 | 51 | 36.67 | 11.09 | 25.58 | +20.00 | True |
| C2V0A0B0 | 6537 | 1275 | 18.49 | 10.30 | 8.18 | +2.61 | False |
| C2V0A0B1 | 2517 | 1011 | 21.53 | 10.64 | 10.90 | +5.32 | False |
| C2V0A0B2 | 1008 | 637 | 23.22 | 11.31 | 11.91 | +6.33 | False |
| C2V0A1B0 | 144 | 139 | 17.75 | 10.66 | 7.09 | +1.51 | True |
| C2V0A1B1 | 82 | 82 | 21.69 | 9.72 | 11.97 | +6.39 | True |
| C2V0A1B2 | 49 | 49 | 28.38 | 10.60 | 17.78 | +12.20 | True |
| C2V0A2B0 | 124 | 120 | 16.05 | 10.59 | 5.46 | -0.12 | True |
| C2V0A2B1 | 71 | 71 | 18.95 | 9.67 | 9.28 | +3.70 | True |
| C2V0A2B2 | 45 | 45 | 23.15 | 10.56 | 12.59 | +7.01 | True |
| C2V1A0B0 | 2271 | 974 | 19.34 | 9.69 | 9.65 | +4.08 | False |
| C2V1A0B1 | 1372 | 765 | 20.14 | 10.17 | 9.97 | +4.39 | False |
| C2V1A0B2 | 758 | 512 | 22.16 | 10.99 | 11.18 | +5.60 | False |
| C2V1A1B0 | 99 | 98 | 21.65 | 10.84 | 10.81 | +5.23 | True |
| C2V1A1B1 | 72 | 72 | 25.01 | 9.99 | 15.02 | +9.44 | True |
| C2V1A1B2 | 49 | 49 | 28.38 | 10.60 | 17.78 | +12.20 | True |
| C2V1A2B0 | 85 | 84 | 19.18 | 10.95 | 8.22 | +2.64 | True |
| C2V1A2B1 | 62 | 62 | 22.27 | 10.08 | 12.18 | +6.60 | True |
| C2V1A2B2 | 45 | 45 | 23.15 | 10.56 | 12.59 | +7.01 | True |
| C2V2A0B0 | 1278 | 729 | 19.42 | 10.29 | 9.13 | +3.55 | False |
| C2V2A0B1 | 878 | 578 | 19.36 | 10.57 | 8.78 | +3.20 | False |
| C2V2A0B2 | 562 | 423 | 20.51 | 11.05 | 9.47 | +3.89 | False |
| C2V2A1B0 | 83 | 83 | 21.78 | 9.91 | 11.87 | +6.30 | True |
| C2V2A1B1 | 65 | 65 | 23.35 | 9.35 | 13.99 | +8.41 | True |
| C2V2A1B2 | 47 | 47 | 27.45 | 10.15 | 17.29 | +11.71 | True |
| C2V2A2B0 | 74 | 74 | 18.28 | 10.22 | 8.06 | +2.48 | True |
| C2V2A2B1 | 58 | 58 | 19.76 | 9.92 | 9.84 | +4.26 | True |
| C2V2A2B2 | 44 | 44 | 22.75 | 10.20 | 12.56 | +6.98 | True |
