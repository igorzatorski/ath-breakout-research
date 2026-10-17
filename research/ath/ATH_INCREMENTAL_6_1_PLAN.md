# Incremental ATH information conditional on 6-1 momentum

Exploratory protocol fixed before this run. The focus was selected after inspecting earlier results; there is no untouched holdout.

Compare frozen ATH events with five same-date non-ATH companies from the original eligible, certified-history universe. Primary population: original common-momentum ATH events in the top 20% of 6-1 momentum. Secondary: all common-momentum ATH events. Select matches before observing outcomes, without requiring future return availability or controls' future non-ATH status.

Reuse the original deterministic matcher: log size ratio within 2, volatility ratio within 1.5, absolute 6-1 total-return momentum gap within 0.10; standardized Euclidean distance, PERMNO tie break; five distinct historical PERMCOs excluding the event company. Controls need not themselves clear the top20 boundary: the question conditions on continuous momentum. Report balance and support; no widening calipers after seeing results.

Reconstruct vol63 with 63 scheduled daily total returns including signal close; 6-1 momentum is the frozen t-125 through t-21 product. No event outcomes or frozen nonoverlap flags change. Primary endpoint: 252-session stock return minus equal-weight five-control return, with the original next-open execution, distributions, terminal cash and censoring rules. Require all five controls and the event/SPY pair to be valid; disclose resulting selection.

Report stock/control/SPY means on identical event IDs, median paired difference, positive fraction, equal-company/equal-date weighting, fixed nonoverlap sensitivity, existing early/middle/recent periods and annual cohorts. Approximate 2000-draw crossed event-company/date-block intervals at 252 and 504 sessions. Shared controls and overlapping forward windows remain limitations; these intervals are not calibrated causal or portfolio-alpha tests. Inspect control reuse and matching balance. No new momentum windows, thresholds, filters or portfolio optimization.
