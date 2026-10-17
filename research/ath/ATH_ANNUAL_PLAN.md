# Annual ATH extension: 252 sessions

Study: `ath_06_annual_v001`. Declared before annual results, 2026-10-15.
User-requested descriptive extension, not a replacement for the predesignated
21-session primary test and not a search for an optimal holding period.

Reuse all qualified events and fixed controls from `ath_04_signal_matched_v002`,
run `20261015T214148297829Z`. No changes in signal, history quality, liquidity,
entry, total-return accounting or benchmark. No WRDS connection/download.

Measure entry at next NYSE observed open through close of holding session 252.
SPY uses those exact dates and a dividend-reinvestment proxy. Keep terminal
returns once then zero-interest cash; missing observations are not zero returns.
Censor horizons beyond CRSP coverage 2026-06-30. A 252-session year is a trading
horizon, not necessarily exactly twelve calendar months.

Read enough local history across year boundaries, including a second January
if the intervening calendar year contains fewer than 252 trading sessions.
Reuse the original five control IDs and require all five valid annual outcomes
for control comparisons. Do not rematch after seeing future availability.

Primary presentation: arithmetic annual mean for ATH events and matched-date SPY,
their paired difference and counts. Also show original matched controls and the
previously frozen 21-session cooldown subset as labelled sensitivities, without
changing that cooldown to 252 or selecting the better result.

Compare 5/21/63/126/252-session returns on the SAME stock/SPY-valid event IDs.
Also retain available-sample annual coverage and explain horizon attrition.
Three unchanged chronological periods; equal-security/date sensitivity. Annual
uncertainty: circular signal-date blocks 252 sessions, with 504 sensitivity,
2,000 draws, seed 20261015. Events/controls remain dependent, and this is known
quality-selected history, not untouched OOS, causal alpha or portfolio CAGR.
