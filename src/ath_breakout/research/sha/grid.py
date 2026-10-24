"""Batch long/cash execution across independent parameter configurations."""

import numpy as np
import pandas as pd

from .backtest import ExecutionConfig
from .indicator import SHAConfig, smoothed_heikin_ashi


def build_signals(prices, max_span=20, warmup_bars=50):
    """Inclusive square EMA grid; no performance-based filtering."""
    if isinstance(max_span, bool) or not isinstance(max_span, int) or max_span < 1:
        raise ValueError("max_span must be a positive integer")
    return pd.DataFrame(
        {
            (before, after): smoothed_heikin_ashi(
                prices, SHAConfig(before, after, warmup_bars)
            ).signal
            for before in range(1, max_span + 1)
            for after in range(1, max_span + 1)
        }
    ).rename_axis(columns=["pre_span", "post_span"])


def simulate_grid(prices, signals, start_bar, config=None):
    """Same accounting as simulate_long_cash, independent columns batched in NumPy.

    Return metrics, daily equity (including cash anchor), close exposure and
    closed/open trades. Prices must have been validated by the indicator and
    source adapter. No borrowing, no forced liquidation, no synthetic fills.
    """
    config = config or ExecutionConfig()
    if not prices.index.equals(signals.index) or not signals.columns.is_unique:
        raise ValueError("Unique configurations and exactly aligned dates required")
    if not 1 <= start_bar < len(prices):
        raise ValueError("Invalid start_bar")
    if not signals.isin([-1, 0, 1]).where(signals.notna(), True).all().all():
        raise ValueError("Invalid signals")
    values = prices[["open", "close", "dividends"]].to_numpy(float)
    if (
        not np.isfinite(values).all()
        or (values[:, :2] <= 0).any()
        or (values[:, 2] < 0).any()
    ):
        raise ValueError("Invalid prices or dividends")
    signal_values = signals.fillna(0).to_numpy(dtype=float)
    k = len(signals.columns)
    cash = np.full(k, config.initial_cash, dtype=float)
    units = np.zeros(k)
    target = np.zeros(k, dtype=bool)
    entry_bar = np.full(k, -1)
    outlay = np.zeros(k)
    dividend_received = np.zeros(k)
    total_dividends, commissions, slippage = (np.zeros(k) for _ in range(3))
    fill_count = np.zeros(k, dtype=int)
    dates = prices.index[start_bar - 1 :]
    equity = np.empty((len(dates), k))
    equity[0] = cash
    exposure = np.zeros((len(dates), k), dtype=bool)
    fee = config.commission_bps / 10000
    slip = config.slippage_bps / 10000
    trades = []

    def trade_record(j, i, status):
        before, after = signals.columns[j]
        return dict(
            pre_span=before,
            post_span=after,
            entry_date=prices.index[entry_bar[j]],
            entry_bar=int(entry_bar[j]),
            initial_outlay=float(outlay[j]),
            dividends_received=float(dividend_received[j]),
            exit_date=prices.index[i] if status == "closed" else pd.NaT,
            exit_bar=i if status == "closed" else np.nan,
            status=status,
            value=float(cash[j] + units[j] * values[i, 1]),
            net_return=float((cash[j] + units[j] * values[i, 1]) / outlay[j] - 1),
            holding_sessions=i - int(entry_bar[j]),
            holding_calendar_days=(prices.index[i] - prices.index[entry_bar[j]]).days,
        )

    for i in range(start_bar, len(prices)):
        current = signal_values[i - 1]
        target[current > 0] = True
        target[current < 0] = False
        opening, closing, dividend = values[i]
        credited = units * dividend
        total_dividends += credited
        dividend_received += credited
        cash += credited
        buy = target & (cash > 1e-8)
        entry = buy & (units == 0)
        entry_bar[entry] = i
        outlay[entry] = cash[entry]
        dividend_received[entry] = 0
        bought = cash[buy] / (opening * (1 + slip) * (1 + fee))
        units[buy] += bought
        commissions[buy] += bought * opening * (1 + slip) * fee
        slippage[buy] += bought * opening * slip
        fill_count[buy] += 1
        cash[buy] = 0
        sell = ~target & (units > 0)
        commissions[sell] += units[sell] * opening * (1 - slip) * fee
        slippage[sell] += units[sell] * opening * slip
        cash[sell] += units[sell] * opening * (1 - slip) * (1 - fee)
        units[sell] = 0
        fill_count[sell] += 1
        for j in np.flatnonzero(sell):
            trades.append(trade_record(j, i, "closed"))
        pos = i - start_bar + 1
        equity[pos] = cash + units * closing
        exposure[pos] = units > 0
    for j in np.flatnonzero(units > 0):
        trades.append(trade_record(j, len(prices) - 1, "open"))
    trades = pd.DataFrame(trades)
    returns = equity[1:] / equity[:-1] - 1
    years = (dates[-1] - dates[0]).total_seconds() / (365.25 * 86400)
    std = returns.std(axis=0, ddof=1)
    sharpe = np.divide(
        returns.mean(axis=0) * np.sqrt(252), std, out=np.full(k, np.nan), where=std > 0
    )
    multiple = equity[-1] / config.initial_cash
    metrics = pd.DataFrame(
        dict(
            initial_equity=config.initial_cash,
            final_equity=equity[-1],
            total_return=multiple - 1,
            cagr=multiple ** (1 / years) - 1,
            sharpe_252=sharpe,
            max_drawdown=(equity / np.maximum.accumulate(equity, axis=0) - 1).min(
                axis=0
            ),
            exposure_fraction=exposure[1:].mean(axis=0),
            fills=fill_count,
            commissions=commissions,
            slippage_cost=slippage,
            dividend_cash=total_dividends,
        ),
        index=signals.columns,
    )
    for before, after in signals.columns:
        subset = (
            trades.loc[trades.pre_span.eq(before) & trades.post_span.eq(after)]
            if not trades.empty
            else trades
        )
        closed = subset.loc[subset.status.eq("closed")] if not subset.empty else subset
        stats = dict(
            completed_trades=len(closed),
            open_trades=int(subset.status.eq("open").sum()) if not subset.empty else 0,
            win_rate=closed.net_return.gt(0).mean() if not closed.empty else np.nan,
            median_holding_sessions=closed.holding_sessions.median()
            if not closed.empty
            else np.nan,
            median_holding_calendar_days=closed.holding_calendar_days.median()
            if not closed.empty
            else np.nan,
            holding_sessions_p10=closed.holding_sessions.quantile(0.1)
            if not closed.empty
            else np.nan,
            holding_sessions_p90=closed.holding_sessions.quantile(0.9)
            if not closed.empty
            else np.nan,
        )
        for field, value in stats.items():
            metrics.loc[(before, after), field] = value
    return (
        metrics.reset_index(),
        pd.DataFrame(equity, index=dates, columns=signals.columns),
        pd.DataFrame(exposure, index=dates, columns=signals.columns),
        trades,
    )


def neighbor_sharpe(metrics):
    """Descriptive 3x3 neighbors, excluding center; not an OOS score."""
    result = metrics.copy()
    for row in metrics.itertuples():
        neighbors = metrics.loc[
            (metrics.pre_span - row.pre_span).abs().le(1)
            & (metrics.post_span - row.post_span).abs().le(1)
            & ~(metrics.pre_span.eq(row.pre_span) & metrics.post_span.eq(row.post_span))
        ]
        result.loc[row.Index, "neighbor_count"] = len(neighbors)
        result.loc[row.Index, "neighbor_mean_sharpe"] = neighbors.sharpe_252.mean()
        result.loc[row.Index, "neighbor_worst_sharpe"] = neighbors.sharpe_252.min()
    return result
