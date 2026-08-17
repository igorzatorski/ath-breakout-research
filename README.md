# ATH Breakout Systematic

A modular Python platform for systematic equity research, stock screening,
portfolio management, and backtesting of an ATH breakout/momentum strategy in
the US equity market.

## Project objective

The final system should use a point-in-time Russell 3000 universe, include
delisted securities, and support research without survivorship bias or
look-ahead bias. During the MVP stage, data may come from local CSV files or
Yahoo Finance. Results obtained from the current index constituents and Yahoo
Finance data must not be treated as a reliable historical Russell 3000
backtest.

The core strategy rules and open decisions are documented in
[STRATEGY_SPEC.md](STRATEGY_SPEC.md).

## Development roadmap

1. Data layer and data/universe validation
2. Screener and candidate ranking
3. Simple backtest
4. Portfolio Manager
5. Full point-in-time backtest
6. Position sizing and research
7. Dashboard

## Status

The project is currently at the strategy definition stage. No production-ready
screener or verified backtest results are available yet.
