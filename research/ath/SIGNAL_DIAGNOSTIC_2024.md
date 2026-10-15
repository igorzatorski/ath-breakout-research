# ATH signal diagnostic — 2024

Run date: 2026-10-15. Status: diagnostic only; not a completed return study.

## Method

Read raw CRSP partitions from 1993 through 2024 and the stored pre-1993 seed.
Use PERMNO, split-comparable prices, a strictly prior high, historical monthly
membership effective on the signal date, and mean nominal dollar volume of at
least $10m across 21 NYSE sessions including the signal session. No technical
filters, scoring or portfolio selection. Retain repeated events. Look up the
observed opening on the next exchange session, including January 2025.

Reproduce: `.venv/Scripts/python.exe scripts/research/audit_ath_events.py 2024`.

Run: `outputs/research/ath/ath_01_signal_baseline_v001/20261015T204523359762Z/`.
Earlier same-day diagnostic runs are retained; use this final run for this note.

## Results

- 978,429 raw 2024 rows; 8,545 preliminary price breakouts.
- Exclusions: 620 outside effective PIT membership, 971 below liquidity floor,
  99 without complete 21-session liquidity.
- 6,855 retained diagnostic events across 691 PERMNOs.
- 6,164 are additional events in a security already observed earlier in 2024.
- Two lack the next-session observed opening: KRTX 2024-03-15 and NWLI 2024-07-08.
  Do not replace their entry with a later/stale price; the cause was not investigated.
- 14 selected cases across distinct securities agree with independent raw-history
  maximum recomputation. This checks the local formula, not vendor correctness.
- No retained event has current adjusted high below adjusted close.

## Material findings

1. The pre-1993 acquisition query uses MAX(adjusted close), although the stored
   field is named prior_comparable_high. This is not the required maximum high.
   2,481 retained events (36.19%) belong to securities carrying such a seed.
   They are uncertain, not demonstrated false signals. Requery historical highs
   before certifying them; do not change the definition after inspecting returns.
2. 1,612 events have at least one missing/invalid historical high in available
   history. The audit retains and flags them. Quantify the gaps and determine
   whether a valid bound or vendor repair can resolve their ATH.
3. These flags overlap. 3,619 events have neither flag, but this does not certify
   full listing-history coverage, adjustment-factor accuracy or unbiased sampling.
4. Consecutive events are dependent. Event count is not independent sample size.
5. Entry nominal and adjusted prices are separately labelled. Dividends and
   delistings have not yet been accounted for in forward returns because no
   forward returns were calculated.

## Verification and decision

Local readiness passed. Full suite: 280 passed using a fresh workspace-local
pytest temporary directory; default temporary-directory permissions prevented
82 fixture setups on the first attempt. Ruff and Git whitespace checks passed.
Three new tests cover current-day exclusion, missing-high state, pre-period
seeds and split comparability. Final extraction completed after adding explicit
entry-price adjustment fields.

No visual chart inspection was performed. Sample checking was numerical.
No forward returns, benchmark excess returns, costs or alpha were estimated.
Next: resolve high-history provenance/gaps, then implement 5/21/63/126-session
total returns from next-session open with aligned SPY and matched controls.
