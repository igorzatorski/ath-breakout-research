# ATH repeated-event sensitivity: 21-session exclusion

Study: `ath_05_cooldown21_v001`. Defined before results, 2026-10-15.

Question: does the primary 21-session excess persist when repeated signals in
the same security are suppressed? No portfolio, exit or parameter optimization.

- Reuse frozen `ath_04_signal_matched_v002/20261015T214148297829Z` observations,
  signals 1994-01-03 through 2026-06-30, the same quality-qualified population,
  return accounting, SPY and five preselected matched controls.
- Compare all original events with a single 21-session exclusion variant.
- For each PERMNO, keep the first qualified signal chronologically, skip signals
  in the FOLLOWING 21 NYSE sessions, and allow the next signal from session 22.
  A skipped event does not reset the exclusion clock. State crosses year ends.
- Apply the rule to ALL original qualified signal events before observing next
  openings, match availability, missing returns or censoring. A non-executable
  first entry still starts the clock. This avoids future-availability selection.
- Keep original event IDs and control selections. Do not reselect controls or
  require controls themselves to obey the event cooldown.
- Primary return horizon stays 21 sessions. Use complete stock/SPY/control
  windows for the matched comparison and separately show all valid SPY windows.
- Show counts, means/medians, excess to both benchmarks, equal-date/security
  sensitivity, and the same three chronological subperiods.
- Circular signal-date bootstrap: 126 and 252 sessions, 2,000 draws, seed 20261015.
  For the difference of means, resample common date blocks jointly for both
  samples, not two independent intervals.
- This is a sampling sensitivity, not a claim of a better trading filter.
  Reducing same-security overlap does not create independent observations:
  different securities, recurring companies and reused controls remain dependent.
- Earlier history-quality exclusions still apply. No full-market, causal,
  untouched out-of-sample or risk-adjusted alpha claim.
