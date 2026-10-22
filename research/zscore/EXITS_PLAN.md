# Exit and sizing study v004

Declared before execution, 2026-10-22. Use v003 common signal dates.
Three fixed entries: QQQ Z30<=-2 with 5/10-session caps; SPY RSI2<=10 with
5-session cap. No entry optimization. Next-open entry, one position at a time.
Variants: time only; fixed stops 1/2/3/5%; take profit 2/4%; signal recovery
(QQQ Z>=0, SPY RSI>=50) at NEXT open, capped at original time exit;
stop2% plus TP4%. Stop gaps fill at open, regular touches at barrier.
If stop and target touched on same bar, use stop first and count ambiguity.
Re-entry may occur next session after exit if a new close signal qualifies.

Account exposures at entry: 0.25/1/5/10 times current total equity. Fixed units
within trade, no daily leverage reset. Exposure differs from broker leverage.
Stylized CFD financing: 6% annual on entry notional over calendar nights;
sensitivity 0/3/9%. Costs 10bps of entry notional on entry and 10bps of exit
notional on exit, including forced exits. No idle cash interest.
Assume broker initial margin 5% of entry notional (20:1 contract leverage),
account closeout at half initial required margin, allowing exit-cost reserve.
This is an explicit scenario, not a broker-specific CFD or futures backtest.
Negative equity after gaps is reported then floored at zero for account curve
(negative balance protection assumption); no further trades after insolvency.
Adjusted ETF OHLC proxy cannot reproduce overnight CFD quotes, futures rolls,
intraday financing triggers or actual liquidity. Stop slippage beyond open
gaps is not modeled. No claim of guaranteed loss caps.

Report net CAGR, close-marked max drawdown, account trade return, net hit rate,
trade count, margin exits, gap-stop fills, ambiguous bars, worst trade,
subperiods and financing sensitivity. Save daily equity and trade ledgers.
All comparisons exploratory, no winner declared independently validated.
