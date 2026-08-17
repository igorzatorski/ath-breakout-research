# ATH Breakout Strategy Specification

## 1. Document status

This is the first working specification of the strategy. It separates agreed
rules from parameters that still require a decision or further research. This
document should serve as the source of truth for the future screener, Portfolio
Manager, and backtesting engine.

## 2. Strategy objective

The strategy aims to identify liquid stocks trading near their all-time highs,
preferably after a long and tight consolidation. A position is opened after an
ATH breakout and held for as long as the price remains above the active moving
average.

The intended mechanism is payoff asymmetry: numerous controlled losses and
small gains should be offset by less frequent, exceptionally large winning
positions. No specific win rate or positive profitability is assumed in
advance; both must be measured through a methodologically sound backtest.

## 3. Universe and data

### Target version

- US equities that belonged to the point-in-time Russell 3000 universe on each
  historical date;
- historical index membership changes and delisted securities included;
- Norgate Data or another source providing suitable historical coverage;
- no survivorship bias or look-ahead bias.

### MVP

- one or more securities stored in local CSV files;
- optionally, Yahoo Finance for development and technical validation;
- MVP results must not be presented as a reliable historical Russell 3000
  backtest.

Each daily data record should contain at least:

- trading date;
- `open`, `high`, `low`, `close`, and `volume`;
- information required to account for stock splits and other corporate actions;
- a security identifier that does not rely exclusively on the current ticker.

Raw OHLC prices and adjusted prices should be stored separately or remain
independently reproducible. The precise adjustment method used to determine ATH
levels must be approved before the full backtest.

## 4. Entry rules

### 4.1. ATH definition

For session `t`, the prior ATH is the maximum price across all available history
strictly before that session:

```text
prior_ath[t] = max(price[s] for every s < t)
```

The current session must not contribute to the level that it is being tested
against. ATH does not mean a rolling 252-day high or a two-year high.

### 4.2. Breakout signal

The working signal rule is:

```text
close[t] > prior_ath[t]
```

The signal becomes known only after session `t` closes. The trade may be
executed no earlier than the following session. The default assumption for the
first backtest is:

```text
entry_price = open[t + 1]
```

If the next session or its opening price is unavailable, the trade must not be
artificially executed using the last known price.

### 4.3. Consolidation and ranking

Preference should be given to stocks emerging from a long and tight
consolidation, but its exact definition has not yet been agreed. A future
version should consider:

- consolidation length in trading sessions;
- price-range width;
- ATR or another volatility measure;
- distance from the prior ATH;
- volume behaviour;
- the trend preceding the consolidation;
- minimum price and liquidity requirements.

Until these parameters are approved, consolidation is not a mandatory coded
entry filter. Its definition must not be selected solely because it produces
the strongest historical result.

## 5. Position size and exposure

- target initial position value: 3% of current portfolio equity;
- approximately 33 full positions at most, representing roughly 99% equity
  exposure;
- unused capital remains in cash or, in a later version, in short-term
  risk-free instruments;
- a position is not automatically rebalanced back to 3% after its price changes;
- no pyramiding or partial selling is used at this stage.

Example: ten positions at 3% each represent approximately 30% equity exposure
and 70% uninvested capital.

The procedure for handling more simultaneous candidates than available
portfolio slots requires a future ranking rule.

## 6. Open-position management

Profit thresholds are measured relative to the actual entry execution price.
The highest level reached is permanent: once the strategy switches to a faster
moving average, a subsequent price decline does not restore a slower average.

| Highest profit reached since entry | Active exit average |
|---|---:|
| below 50% | SMA150 |
| at least 50% but below 100% | SMA100 |
| at least 100% | SMA50 |

The working assumption is that a threshold is reached based on the closing
price. Using the daily `high` instead of `close` remains an open decision.

## 7. Exit rules

A sell signal is generated when:

```text
close[t] < active_sma[t]
```

The moving average for session `t` may include that session's closing price
because the decision is made only after the session has ended. The entire
position may be sold no earlier than the following session. The default
assumption for the first backtest is:

```text
exit_price = open[t + 1]
```

No partial exits are used. Price gaps may produce a loss larger than implied by
the moving-average level, so the backtest must use an actually available
execution price.

## 8. Bias-control rules

- signals may use only information available by the end of the relevant
  session;
- a close-based signal cannot be executed at the same closing price;
- the ATH level for session `t` cannot include the price from session `t`;
- universe membership must be correct for each historical date;
- delisted securities must not be removed from the test history;
- strategy parameters should be evaluated out of sample or through walk-forward
  analysis;
- costs, slippage, price gaps, and liquidity constraints must be included before
  results are considered realistic.

## 9. Open decisions

The following items must be defined unambiguously before the full backtest:

1. The price series used to calculate ATH and the treatment of corporate
   actions.
2. Exact consolidation parameters.
3. Minimum price, liquidity, and listing-history requirements.
4. Candidate ranking when the number of signals exceeds available slots.
5. Whether the +50% and +100% thresholds are activated by `close` or daily
   `high`.
6. Share-quantity rounding and the treatment of residual cash.
7. Transaction costs, slippage, and the short-term risk-free return model.
8. Treatment of trading suspensions, delistings, and missing data.
9. Benchmark selection and the strategy evaluation metrics.

## 10. First implementation scope

The first technical step should be restricted to one stock and one local CSV
file:

1. load and validate daily OHLCV data;
2. calculate the prior ATH without look-ahead bias;
3. identify breakout sessions;
4. save or display the resulting table for manual verification.

This stage does not yet include full-market screening, the Portfolio Manager,
Streamlit, or any claims about strategy performance.
