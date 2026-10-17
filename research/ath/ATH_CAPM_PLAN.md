# Fixed pre-signal CAPM event study

Study `ath_09_capm_v001`, registered before CAPM outcomes are inspected.
Question: is post-ATH performance unexplained by a pre-estimated market beta,
and is it higher than that of the frozen non-ATH controls?

Frozen ath_04 v002 signals; ath_06 annual outcomes and old control IDs; ath_08
momentum-control IDs. No entry, exit, horizon, universe or matching changes.
Download and preserve the official Kenneth French daily research factors ZIP,
its SHA256, retrieval time and URL. Use Mkt-RF and RF in decimal units; no WRDS.
Market factor covers a broad US CRSP market, not SPY. Full data end 2026-06-30.

Beta: OLS with intercept, trailing 252 NYSE sessions strictly BEFORE signal
session (t-252..t-1); require >=200 valid paired daily observations, positive
factor variance. No future returns or signal-day return in estimation; no beta
clipping or shrinkage. Save beta, estimation count and intercept; do not
subtract the pre-signal intercept from the CAPM expected return.

Daily abnormal return is stock return minus RF minus beta*(Mkt-RF). Sum daily
abnormal returns (CAR), never compound abnormal returns. CAR is an additive
model diagnostic, NOT a buy-and-hold excess return or portfolio Jensen alpha.

Official factors are close-to-close. Preserve the next-open entry and original
252-session gross-return validity checks, but omit entry-day partial return
from CAPM calculation: start entry close, then 251 full daily returns through
the original exit close. Explicitly disclose this difference. No intraday
factor is fabricated. Original CRSP total returns include terminal Y once;
after Y hold zero-interest cash, set market exposure to zero and residual to
-RF. Count terminal day as active exposure. Missing nonterminal returns are
invalid, incomplete 252-session horizons censored. No replacement controls.

Primary incremental comparison: require valid beta and CAR for ATH, all five
old controls and all five momentum controls, on the SAME events; compare ATH
CAR, old-control CAR, momentum-control CAR and both paired differences. Also
show standalone available ATH CAR, old-pair and momentum-pair availability,
coverage, mean/median beta, periods, years, equal-date/equal-PERMNO weights and
fixed cooldown21 sensitivity. Do not mix samples with earlier gross means.

Uncertainty: circular signal-date block bootstrap, 252 and 504 sessions, 2000
draws, seed 20261015. Persistent firm dependence, beta estimation uncertainty,
retrospective horizon choice, revisions in modern historical factor files and
other omitted risks remain limitations. CAPM adjustment alone is not causal
attribution to ATH or momentum-factor adjustment. No portfolio/parameter search.

Check OLS against direct least squares and CAR against direct session sums,
terminal handling, cutoff, lag, observed factor coverage, frozen hashes and
existing annual return results. Record failures and repairs honestly.
