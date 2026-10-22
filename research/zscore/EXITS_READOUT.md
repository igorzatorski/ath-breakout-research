# Exit, stop and account-exposure findings

216 predefined scenario runs, not 216 independently validated strategies.
Period: v003 common dates, April 2000 through October 2026. Entries: QQQ
Z30 <= -2, capped at 5 or 10 sessions; SPY RSI2 <= 10, capped at 5 sessions.
Primary assumptions: 10bps each side; 6% annual financing on entry notional
over calendar nights; zero interest on idle cash. Position units fixed inside
each trade. Full methodology: EXITS_PLAN.md; all tables: EXITS_RESULTS.md.

## Findings at account exposure 1x

| Entry / cap | Exit | Net CAGR | Close-marked max drawdown | Net win rate |
|---|---|---:|---:|---:|
| QQQ / 5 | Time | 2.84% | -26.95% | 56.5% |
| QQQ / 5 | Stop 1% | -2.65% | -66.44% | 20.2% |
| QQQ / 5 | Stop 2% | -0.72% | -56.49% | 36.8% |
| QQQ / 5 | Stop 3% | 0.36% | -45.03% | 44.9% |
| QQQ / 5 | Stop 5% | -0.60% | -39.17% | 52.1% |
| QQQ / 5 | TP 4% | 2.99% | -20.87% | 62.6% |
| QQQ / 10 | Time | 3.72% | -37.61% | 57.1% |
| QQQ / 10 | TP 2% | 2.98% | -20.61% | 79.5% |
| QQQ / 10 | TP 4% | 3.32% | -24.19% | 66.1% |
| SPY RSI / 5 | Time | 1.59% | -37.83% | 54.8% |
| SPY RSI / 5 | Stop 2% | -1.23% | -52.23% | 44.6% |
| SPY RSI / 5 | RSI recovery | 1.00% | -30.50% | 60.4% |

Stops allow renewed qualifying entries the following day. Thus the stop
comparison includes different trade counts, repeated losses and costs; it
does not isolate the impact of a stop on an unchanged set of trades. Do not
generalize this result to every stop rule or cooldown policy. Gap fills may
exceed the intended stop loss (QQQ 2% stop worst account trade about -7.41%).
Stop+target same-bar ambiguity is resolved adversely and counted in the ledger.

## Account exposure is different from contract leverage

QQQ 10-session time exit, including modeled financing:

| Entry notional / total account equity | CAGR | Max drawdown |
|---|---:|---:|
| 0.25x | 1.06% | -10.12% |
| 1x | 3.72% | -37.61% |
| 5x | -14.50% | -99.94% |
| 10x | Account depleted | -100% |

All 5x scenarios at 6% funding have negative CAGR; 10x scenarios either
deplete the account or suffer nearly total drawdowns. Margin closeouts and
negative balance protection are explicit model assumptions, not verified
broker-specific rules. A position with notional 25% of account equity can be
implemented with a margined contract without having 5x or 10x account exposure.
Example: allocating 5% of account as margin to a 10:1 contract creates 0.5x
account exposure, not 10x. No 0.5x result is claimed here.

## Financing and inference

At QQQ 10-session time exit and 1x exposure, CAGR is 4.68% / 4.20% / 3.72% /
3.25% at 0% / 3% / 6% / 9% annual financing. These are constant scenarios,
not historical broker financing rates. QQQ TP4/5 has only a modest apparent
improvement over time exit and has not been shown statistically superior.
Higher win rate with TP2/10 still includes a worst trade around -15.46%.

ETF adjusted OHLC is a total-return price-path proxy, not a CFD/futures quote
history. Funding, margin, overnight price paths, dividends and contract rolls
need instrument-specific data before execution claims. Daily marked drawdowns
do not measure worst intraday account loss. No new out-of-sample validation.

## Verification and references

13 tests passed across the study modules. Dedicated cases cover stop gaps,
adverse same-bar stop/target ordering, next-open recovery exits, fixed units,
calendar-night funding, margin exit and gap insolvency. All 216 final account
equities reconcile to compounded trade outcomes with zero floor after depletion.

- FCA CFD protections: https://www.fca.org.uk/firms/contract-for-differences
- SEC order execution: https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders

Reproduce: `.venv/Scripts/python.exe -m scripts.research.study_exits`.
