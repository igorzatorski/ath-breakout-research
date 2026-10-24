# SHA EMA grid: 20 x 20

Predeclared before computing grid performance, 2026-10-24.

## Fixed experiment

Exactly 400 configurations: pre-HA EMA span 1..20 crossed with post-HA EMA
span 1..20, both inclusive. Span 1 is the identity EMA (no smoothing at that
stage). No other MA types, filters, stops, shorts or sizing variants.

Reuse the full SPY snapshot, SHA initialization, 50-bar warm-up, initial cash,
next-open execution, neutral-state handling, dividend treatment, fees, slippage,
zero cash yield and final-close valuation from BASELINE_10_10_PLAN.md.
All variants share the same evaluation dates and warm-up, not a span-dependent
start. The baseline source fingerprint must match before running.

## Outputs and comparisons

Save every configuration's metrics, daily equity and signals, and every
completed/open trade. Save source/code fingerprints and execution settings.
Reproduce baseline 10/10 and benchmark and compare them with the saved baseline.
Verify the batched simulator against the ledger simulator on synthetic data for
all 400 pairs, plus full-history reference checks for 10/10 and the top CAGR
and top Sharpe configurations. No speed shortcut may change order timing.

Show sequential-scale heatmaps for CAGR and Sharpe, with parameter axes and
explicit units. Identify full-sample leaders in CAGR and Sharpe, but do not
label them optimal for future trading. Also retain max drawdown, exposure,
trade count, win rate and holding durations. Count variants beating buy-and-hold
in CAGR/Sharpe and the number with positive CAGR. Report grid median and range.

As a descriptive neighborhood diagnostic, save the mean and worst Sharpe of
immediate adjacent parameter pairs (3 x 3 window, excluding the center, clipped
at boundaries), and neighbor count. Do not treat neighboring settings as
independent statistical evidence or automatically select a strategy from this.

## Inference boundary

This is exploratory full-history sensitivity, not a train/test exercise.
The full-period baseline has already been inspected. Testing 400 configurations
creates selection bias; the maximum is a hindsight-selected statistic.
No independent OOS claim, significance claim, or automatic final parameter
choice. Future validation must acknowledge this history was inspected.
