# High-breakout pilot protocol

Study: `high_01_52w_vs_ath_pilot_v001`. Defined on 2026-10-15.
This extends the ATH diagnostic without replacing the original ATH definition.

- Signal sample: 2024, selected for continuity with the numerical signal audit,
  not because of its returns. This year was previously inspected; it is not OOS.
- Signal: split-comparable close strictly above the maximum high in the previous
  252 NYSE sessions, excluding the signal session. Require all 252 valid highs.
  Include late 2022 for a complete window at the start of January 2024.
- Monthly historical liquidity population effective on the signal date; formation
  precedes the signal date. Require complete 21-session average nominal dollar
  volume of at least USD 10m including signal close. No ranking/technical filters.
- Retain repeated events and PERMNO identity. Report event/securities counts.
- Disjoint groups: `52w_only` (below/equal known historical high),
  `ath_local_history` (above available high with neither identified history flag),
  `ath_uncertain` (candidate ATH with pre-1993 close seed or invalid/missing highs).
  Local-history ATH is not independently certified listing-inception ATH.
- Entry: next exchange session observed nominal open. No price fallback.
- Horizon H: through close of Hth holding session, with entry as session one.
  H = 5, 21 (primary), 63, 126. Future observations extend into 2025.
- Return: entry close/open followed by compounded CRSP CIZ daily total returns.
  Do not credit the entry-day ex-date dividend. On a CIZ Y row compound its
  terminal return once, then hold marked terminal proceeds as zero-interest cash.
  Missing regular returns/closes invalidate that horizon. No separate duplicate
  delisting-return multiplication. This is an event convention, not settlement
  simulation; exotic intraday entry distributions are not separately modeled.
- SPY: same dates and horizon; entry close/open times adjusted-close growth from
  entry close to exit close. Local Yahoo reinvestment proxy, separate vendor.
- Show gross and stock-cost sensitivity at 10 bps per side versus gross SPY.
- Show event-weighted, equal-security and equal-signal-date average excess returns.
  Any month-block bootstrap intervals are exploratory; 12 signal-month blocks
  cannot establish robust significance, especially for overlapping long horizons.
- No filter/exit tuning. No portfolio CAGR/Sharpe or alpha claims. No winner from
  this pilot: groups differ in characteristics and no matched controls are built.

CRSP semantics reference:
https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-guide-flat-file-format-2-0/

Next after this pilot: review data/accounting exceptions, resolve ATH history,
then compare across longer predefined periods with suitable controls and
dependence-aware uncertainty. Preserve every run and unsuccessful trial.
