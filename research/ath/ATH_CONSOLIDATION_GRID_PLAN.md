# Consolidation length x width: frozen 25-cell exploratory protocol

Question: does a narrow pre-breakout closing-price range improve annual returns among the frozen ATH + 6-1/top20 population?

Lengths: 10, 21, 42, 63, 126 NYSE sessions. Maximum widths: 0.05, 0.10, 0.15, 0.20, 0.30. Exactly 25 cumulative filters, not mutually exclusive bins. Width at signal t is max(adjusted close[t-L:t])/min(adjusted close[t-L:t])-1, excluding t. Require all L scheduled prices finite and positive; no forward fill. Adjusted close = CRSP close / positive price_adjustment_factor. Width <= cutoff passes. This measures range compression, not proof of sideways trading or closeness to ATH.

Primary reference: frozen common-momentum 6-1/top20 ATH annual SPY pairs (23,712 before any new feature-availability exclusions). Show original reference and common all-five-width-observed reference; compare all cells to the latter for identical feature support. No added proximity, volume, entry, exit or portfolio rule. Next-open execution, 252-session endpoint, distributions, terminal cash and original nonoverlap flags remain unchanged. Do not select nonoverlap again within a filter.

Report all 25 counts, stock/SPY/excess means, median excess, loss/underperformance frequency, equal-company and equal-date means, fixed period/annual cuts, nonoverlap sensitivity, exact adjacent width/length contrasts. A gradient is a descriptive pattern, not a fitted causal derivative. Cells below 100 observations are flagged as sparse, not removed or retuned.

Approximate crossed event-company/date circular-block bootstrap: 2,000 draws, seed 20261016, 252/504-session blocks. Preserve joint weights for baseline and all cells. Report pointwise levels/improvements and centered max-absolute-deviation simultaneous bands across all 25 improvements when at least 95% of replicates have all cells observed; otherwise disclose that the full family band is unavailable. Sparse-cell pointwise intervals require 95% valid draws. These are approximate sensitivity bands, not proof of calibrated coverage or corrections for earlier research choices. Primary inferential family is the full-period all-event SPY-excess grid; other cuts are descriptive sensitivities.

All inspected history is exploratory. Preserve every variant, source hashes, missingness and failures. No genuinely untouched validation, transaction costs, factor alpha, or portfolio backtest is supplied by this experiment. Controls are not rematched in this task; comparison is with the unchanged ATH/momentum baseline and same-window SPY.
