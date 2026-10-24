# SHA EMA(10,10): frozen first backtest

Written before computing performance on 2026-10-24. This is one exploratory
historical run, not parameter selection or independent out-of-sample validation.
The 20 x 20 grid is deferred.

- Instrument: SPY, an ETF proxy for S&P 500, not the cash index.
- Source: existing local `data/raw/yfinance/SPY.parquet`; no download/refresh.
- Full available daily history; fingerprint and exact dates saved at execution.
- Indicator: existing EMA(10) -> HA -> EMA(10), on split-adjusted real OHLC,
  excluding dividend adjustment from the signal. First 50 bars are warm-up.
- A completed green signal sets target long; red sets target cash; neutral
  retains the previous target. Initial target is cash. First eligible green
  permits entry without requiring a prior red transition.
- Execute at the next observed session's real open. Last close signal cannot
  cause an order without another bar. Starting equity is recorded on the close
  immediately preceding the first eligible execution session.
- Initial capital USD 100,000; fractional shares; no leverage or shorts.
- Commission 10 bps of executed notional and adverse slippage 5 bps per side.
  Both apply to dividend reinvestment as well. All-in buy sizes include fees.
- Cash earns 0%; no taxes, financing or interest. SPY's fund expenses are already
  reflected in its price; no additional management fee.
- Dividend entitlement uses shares held at the previous close. Dividends are
  credited on ex-date before opening orders. If the target is long, available
  dividend cash is reinvested at that open with costs; if selling that day it
  stays in cash. Ex-date credit is an approximation to payable-date timing.
- Snapshot must be split-adjusted and have no nonzero splits for this initial
  SPY runner; reject unsupported split handling rather than silently ignore it.
- Buy-and-hold starts on the identical first execution open with identical
  capital, fees, slippage and dividend handling.
- Terminal holdings marked to last real close, without forced liquidation;
  final open trade is reported separately from completed trades.
- Metrics: total return, actual-calendar-time CAGR, 252-session annualized
  daily Sharpe (zero risk-free rate), maximum close-to-close drawdown, exposure,
  executions and costs, completed trade count/win rate and holding duration.
  Daily returns include the initial cash anchor and first execution day.
- Save indicator, daily ledger, executions, completed/open trades, metrics,
  configuration, source SHA256 and code fingerprints; committed report uses
  those artifacts. Check hand-calculated accounting and timing before the run.

No PyneSys numerical-parity claim; only the implemented EMA configuration is
tested. Full-history results are exploratory and cannot establish standalone
alpha. Any future grid must retain all 400 variants and define selection and
validation rules before running.
