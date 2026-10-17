# Two- and three-year ATH extension

Study: `ath_07_long_horizons_v001`. Declared before these results, 2026-10-15.
User-requested 504/756-session descriptive extension. The original 21-session
primary remains unchanged; no best-horizon selection or new trading rule.

Reuse all frozen quality-qualified ATH events, original five controls and entry
convention from `ath_04_signal_matched_v002`. Use local CRSP observations only,
through 2026-06-30. No WRDS or vendor refresh. Preserve previous artifacts.

Measure next-session observed opening through closes of holding sessions 504
and 756 (approximately two and three trading years). Report cumulative total
returns, not per-year returns or portfolio CAGR. Include later distributions,
CIZ terminal return once then zero-interest cash; no stale/missing-price fills.
Read through a fourth following January where needed for 756 trading sessions.
Censor incomplete horizons, including all late signals lacking 2/3 years.

Report ATH and identical-date SPY gross arithmetic means/medians, excess and
counts, original fixed controls and unchanged 21-session cooldown sensitivities.
Also compare 252/504/756 and shorter horizons on the SAME valid stock/SPY IDs.
Retain available-sample figures and the same chronological stability periods.

To distinguish positive endpoint from a smooth trend, describe each stock's
closing-total-return wealth path: worst loss from entry and maximum drawdown
from an earlier closing wealth peak, including initial wealth 1. Compute same
closing-path drawdown for SPY over identical dates. This is not intraday risk or
a stop simulation. Reconcile path endpoints with the vector event-return engine.

Use circular signal-date bootstrap blocks 756 and 1512 sessions, 2,000 draws,
fixed seed 20261015. These long windows overlap heavily; few effective long
blocks and persistent company effects limit inference. Check fixed subperiods
and company/date weighting, not only event-weighted means. Historical-quality
selection and omitted momentum/sector controls remain. No causal, alpha,
untouched OOS or portfolio claim. Do not extrapolate 3-year returns to 5 years.
