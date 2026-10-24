"""Daily long/cash simulation with lagged targets and explicit dividend cash."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExecutionConfig:
    initial_cash: float = 100_000.0
    commission_bps: float = 10.0
    slippage_bps: float = 5.0

    def __post_init__(self):
        if not np.isfinite(self.initial_cash) or self.initial_cash <= 0:
            raise ValueError("Positive finite initial cash required")
        for value in (self.commission_bps, self.slippage_bps):
            if not np.isfinite(value) or not 0 <= value < 10_000:
                raise ValueError("Costs must be finite and in [0, 10000) bps")


def simulate_long_cash(prices, signals, start_bar, config=None):
    """Execute yesterday's -1/+1 target at today's open; zero retains target.

    An anchor at start_bar - 1 close precedes evaluation. signals must use
    identical dates. Input prices must be real, split-adjusted single-instrument
    OHLC with ex-date dividends in the same per-share units and no splits.
    This function never fills at synthetic indicator prices.
    """
    config = config or ExecutionConfig()
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("DatetimeIndex required")
    if (
        prices.index.hasnans
        or not prices.index.is_unique
        or not prices.index.is_monotonic_increasing
    ):
        raise ValueError("Unique increasing valid timestamps required")
    if not prices.index.equals(signals.index):
        raise ValueError("Signals must align exactly with prices")
    if not isinstance(start_bar, int) or not 1 <= start_bar < len(prices):
        raise ValueError("start_bar needs an earlier anchor and an execution bar")
    required = prices[["open", "close", "dividends"]].to_numpy(float)
    if (
        not np.isfinite(required).all()
        or (required[:, :2] <= 0).any()
        or (required[:, 2] < 0).any()
    ):
        raise ValueError("Finite positive prices and nonnegative dividends required")
    if not signals.dropna().isin([-1, 0, 1]).all():
        raise ValueError("Signals must be -1, 0, +1 or missing")
    fee_rate = config.commission_bps / 10_000
    slip_rate = config.slippage_bps / 10_000
    cash, units, target = config.initial_cash, 0.0, False
    fills, trades, daily = [], [], []
    active = None
    anchor = prices.index[start_bar - 1]
    daily.append(
        dict(
            date=anchor,
            cash=cash,
            units=0.0,
            equity=cash,
            dividend_cash=0.0,
            target_long=False,
            exposed=False,
            is_anchor=True,
        )
    )

    for i in range(start_bar, len(prices)):
        date = prices.index[i]
        row = prices.iloc[i]
        signal = signals.iloc[i - 1]
        if pd.notna(signal) and signal != 0:
            target = signal > 0
        dividend = units * float(row.dividends)
        cash += dividend
        if active is not None:
            active["dividends_received"] += dividend

        if target and cash > 1e-8:
            entering = units == 0
            budget = cash
            fill_price = float(row.open) * (1 + slip_rate)
            bought = budget / (fill_price * (1 + fee_rate))
            notional = bought * fill_price
            fee = notional * fee_rate
            units += bought
            cash = 0.0
            fills.append(
                dict(
                    date=date,
                    signal_date=prices.index[i - 1],
                    side="buy",
                    reason="entry" if entering else "dividend_reinvestment",
                    units=bought,
                    reference_open=float(row.open),
                    fill_price=fill_price,
                    commission=fee,
                    slippage_cost=bought * float(row.open) * slip_rate,
                    cash_flow=-budget,
                )
            )
            if entering:
                active = dict(
                    entry_date=date,
                    entry_bar=i,
                    initial_outlay=budget,
                    dividends_received=0.0,
                )
        elif not target and units > 0:
            fill_price = float(row.open) * (1 - slip_rate)
            fee = units * fill_price * fee_rate
            proceeds = units * fill_price - fee
            fills.append(
                dict(
                    date=date,
                    signal_date=prices.index[i - 1],
                    side="sell",
                    reason="exit",
                    units=units,
                    reference_open=float(row.open),
                    fill_price=fill_price,
                    commission=fee,
                    slippage_cost=units * float(row.open) * slip_rate,
                    cash_flow=proceeds,
                )
            )
            cash += proceeds
            trades.append(
                dict(
                    **active,
                    exit_date=date,
                    exit_bar=i,
                    status="closed",
                    value=cash,
                    net_return=cash / active["initial_outlay"] - 1,
                    holding_sessions=i - active["entry_bar"],
                    holding_calendar_days=(date - active["entry_date"]).days,
                )
            )
            units, active = 0.0, None
        equity = cash + units * float(row.close)
        daily.append(
            dict(
                date=date,
                cash=cash,
                units=units,
                equity=equity,
                dividend_cash=dividend,
                target_long=target,
                exposed=units > 0,
                is_anchor=False,
            )
        )
    if active is not None:
        trades.append(
            dict(
                **active,
                exit_date=pd.NaT,
                exit_bar=np.nan,
                status="open",
                value=equity,
                net_return=equity / active["initial_outlay"] - 1,
                holding_sessions=len(prices) - 1 - active["entry_bar"],
                holding_calendar_days=(prices.index[-1] - active["entry_date"]).days,
            )
        )
    ledger = pd.DataFrame(daily).set_index("date")
    ledger["daily_return"] = ledger.equity.pct_change().fillna(0.0)
    ledger["drawdown"] = ledger.equity / ledger.equity.cummax() - 1
    return ledger, pd.DataFrame(fills), pd.DataFrame(trades)


def summarize(ledger, fills, trades):
    """Sharpe uses 252 observations/year, zero risk-free rate and sample std."""
    returns = ledger.daily_return.iloc[1:]
    years = (ledger.index[-1] - ledger.index[0]).total_seconds() / (365.25 * 86400)
    multiple = ledger.equity.iloc[-1] / ledger.equity.iloc[0]
    std = returns.std(ddof=1)
    closed = trades.loc[trades.status.eq("closed")] if not trades.empty else trades
    return dict(
        initial_equity=float(ledger.equity.iloc[0]),
        final_equity=float(ledger.equity.iloc[-1]),
        total_return=float(multiple - 1),
        cagr=float(multiple ** (1 / years) - 1) if years > 0 else None,
        sharpe_252=float(returns.mean() / std * np.sqrt(252)) if std > 0 else None,
        max_drawdown=float(ledger.drawdown.min()),
        exposure_fraction=float(ledger.exposed.iloc[1:].mean()),
        fills=len(fills),
        completed_trades=len(closed),
        open_trades=int(trades.status.eq("open").sum()) if not trades.empty else 0,
        win_rate=float(closed.net_return.gt(0).mean()) if not closed.empty else None,
        median_holding_sessions=float(closed.holding_sessions.median())
        if not closed.empty
        else None,
        median_holding_calendar_days=float(closed.holding_calendar_days.median())
        if not closed.empty
        else None,
        holding_sessions_p10=float(closed.holding_sessions.quantile(0.1))
        if not closed.empty
        else None,
        holding_sessions_p90=float(closed.holding_sessions.quantile(0.9))
        if not closed.empty
        else None,
        commissions=float(fills.commission.sum()) if not fills.empty else 0.0,
        slippage_cost=float(fills.slippage_cost.sum()) if not fills.empty else 0.0,
        dividend_cash=float(ledger.dividend_cash.sum()),
    )
