"""Descriptive trade and drawdown diagnostics; no parameter selection rules."""

import numpy as np
import pandas as pd


def trade_statistics(metrics, trades):
    """Add closed-trade means; open positions are never counted as wins/losses."""
    result = metrics.copy()
    records = []
    for row in metrics.itertuples():
        closed = trades.loc[
            trades.pre_span.eq(row.pre_span)
            & trades.post_span.eq(row.post_span)
            & trades.status.eq("closed")
        ]
        winners = closed.loc[closed.net_return > 0]
        losers = closed.loc[closed.net_return < 0]
        pnl = closed.value - closed.initial_outlay
        loss = -pnl.loc[pnl < 0].sum()
        gains = pnl.loc[pnl > 0].sum()
        loss_flags = (
            closed.sort_values("exit_date").net_return.lt(0)
            if "exit_date" in closed
            else closed.net_return.lt(0)
        )
        losing_streak = (
            loss_flags.groupby((~loss_flags).cumsum()).sum().max() if len(closed) else 0
        )
        records.append(
            dict(
                pre_span=row.pre_span,
                post_span=row.post_span,
                mean_holding_sessions=closed.holding_sessions.mean(),
                mean_holding_calendar_days=closed.holding_calendar_days.mean(),
                mean_trade_return=closed.net_return.mean(),
                mean_winner_return=winners.net_return.mean(),
                mean_loser_return=losers.net_return.mean(),
                worst_trade_return=closed.net_return.min(),
                best_trade_return=closed.net_return.max(),
                profit_factor_dollars=gains / loss if loss > 0 else np.nan,
                completed_trade_dollar_pnl=pnl.sum(),
                zero_return_trades=int(closed.net_return.eq(0).sum()),
                maximum_losing_streak=int(losing_streak),
            )
        )
    return result.merge(
        pd.DataFrame(records), on=["pre_span", "post_span"], validate="one_to_one"
    )


def drawdown_episode(equity):
    """Maximum close-equity drawdown and last high-water mark preceding it."""
    if (
        equity.empty
        or not equity.index.is_monotonic_increasing
        or not np.isfinite(equity).all()
        or (equity <= 0).any()
    ):
        raise ValueError("Positive finite dated equity required")
    drawdown = equity / equity.cummax() - 1
    trough = drawdown.idxmin()
    before = equity.loc[:trough]
    peak = before.loc[before.eq(before.max())].index[-1]
    recovered = equity.loc[trough:]
    recovered = recovered.loc[recovered >= equity.loc[peak]]
    recovery = recovered.index[0] if len(recovered) else None
    return dict(
        peak_date=str(peak.date()),
        trough_date=str(trough.date()),
        recovery_date=str(recovery.date()) if recovery is not None else None,
        peak_equity=float(equity.loc[peak]),
        trough_equity=float(equity.loc[trough]),
        max_drawdown=float(drawdown.min()),
        peak_to_trough_calendar_days=(trough - peak).days,
        underwater_calendar_days=(recovery - peak).days
        if recovery is not None
        else None,
    )


def annual_comparison(strategy, benchmark):
    """Compounded observed close-to-close daily returns by calendar year."""
    returns = pd.DataFrame(
        dict(strategy=strategy.pct_change(), benchmark=benchmark.pct_change())
    )
    grouped = (1 + returns).groupby(returns.index.year).prod() - 1
    grouped["excess_return"] = grouped.strategy - grouped.benchmark
    grouped.index.name = "year"
    return grouped
