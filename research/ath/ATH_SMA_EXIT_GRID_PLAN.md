# ATH35: fixed five-window SMA exit comparison

Authorized windows: 50, 100, 150, 200 and 250 NYSE sessions. One change: exit window. No initial price floor. Signal on a close strictly below the current SMA, execute at the next observed opening, retaining terminal-event handling. An SMA is not a guaranteed maximum loss.

Freeze ATH33 entries: fresh ATH plus market momentum 6-1/top20, MV ranking, maximum 20 companies, 5% entry target; separate drift and monthly-equal policies. Start USD100,000 cash with zero holdings on 2008-01-02, end 2026-06-30. Ten bps per buy/sell, fractional shares, zero cash yield, existing dividends/terminal accounting. SPY on identical dates and entry costs. Older raw split-adjusted prices warm the rolling indicators only; no inherited PnL.

Report all ten variants: CAGR, SPY difference, drawdown, exposure, concentration, turnover and transactions; inspect 2018 onward and 2023 onward without deleting earlier years. Compare the complete gradient, not just its maximum. Existing SMA50 and SMA200 must reproduce ATH33 exactly. Validate raw features, trigger/next-open execution and accounting using existing independent checks. Save protocol, source/code hashes, summaries and ledger artifacts. This is an exploratory comparison on inspected history, not untouched validation or proof of an optimal window.
