"""Causal monthly futures risk allocation with explicit unit P&L and roll costs."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Config:
    capital: float = 10_000_000.0
    lookback_months: int = 12
    risk_sessions: int = 60
    target_volatility: float = 0.10
    covariance_shrinkage: float = 0.25
    market_notional_cap: float = 0.50
    class_notional_cap: float = 1.50
    gross_notional_cap: float = 4.0
    annual_vol_floor: float = 0.01
    margin_proxy_rate: float = 0.10
    margin_proxy_limit: float = 0.50
    margin_proxy_reduction: float = 0.45

    def __post_init__(self):
        if self.capital <= 0 or not np.isfinite(self.capital):
            raise ValueError("Positive finite capital required")
        if self.risk_sessions < 2 or self.lookback_months < 1:
            raise ValueError("Insufficient lookback")
        if not 0 <= self.covariance_shrinkage <= 1 or self.target_volatility <= 0:
            raise ValueError("Invalid risk parameters")


def targets(changes, raw_notional, median_notional, directions, groups, nav, config):
    """Contract/source-unit targets; covariance is in USD P&L per unit."""
    cov = changes.tail(config.risk_sessions).cov().to_numpy()
    median = np.maximum(np.asarray(median_notional, dtype=float), 1e-8)
    diagonal = np.maximum(
        np.diag(cov), (median * config.annual_vol_floor / np.sqrt(252)) ** 2
    )
    cov = (
        1 - config.covariance_shrinkage
    ) * cov + config.covariance_shrinkage * np.diag(np.diag(cov))
    cov += np.diag(diagonal - np.diag(cov))
    if not np.isfinite(cov).all() or nav <= 0:
        raise ValueError("Finite risk history and positive NAV required")
    group_array = np.asarray(groups)
    group_names = list(dict.fromkeys(groups))
    budgets = np.array(
        [1 / len(group_names) / np.sum(group_array == g) for g in groups]
    )
    q = (
        nav
        * config.target_volatility
        * budgets
        * np.asarray(directions)
        / np.sqrt(diagonal * 252)
    )
    predicted = np.sqrt(max(float(q @ cov @ q) * 252, 0))
    if predicted > 0:
        q *= nav * config.target_volatility / predicted
    notionals = np.maximum(np.abs(raw_notional), 0.1 * median)
    q = np.clip(
        q,
        -config.market_notional_cap * nav / notionals,
        config.market_notional_cap * nav / notionals,
    )
    for group in group_names:
        mask = group_array == group
        exposure = np.sum(np.abs(q[mask]) * notionals[mask])
        if exposure > config.class_notional_cap * nav:
            q[mask] *= config.class_notional_cap * nav / exposure
    gross = np.sum(np.abs(q) * notionals)
    if gross > config.gross_notional_cap * nav:
        q *= config.gross_notional_cap * nav / gross
    predicted = np.sqrt(max(float(q @ cov @ q) * 252, 0))
    if predicted > nav * config.target_volatility:
        q *= nav * config.target_volatility / predicted
        predicted = nav * config.target_volatility
    return q, predicted / nav


def eligible_month_ends(adjusted, config):
    dates = adjusted.index
    ends = dates.to_series().groupby(dates.to_period("M")).last()
    return [
        date
        for date in ends
        if date >= dates[0] + pd.DateOffset(months=config.lookback_months)
        and dates.get_loc(date) >= config.risk_sessions
    ]


def simulate(
    adjusted,
    raw_prices,
    roll_events,
    point_values,
    unit_costs,
    groups,
    config=None,
    always_long=False,
):
    """Monthly decisions at D close execute at D+1 close; earn changes from D+2.

    Cash is collateral. Only P&L and costs change NAV; notional is not deducted.
    Fractional source units and proxy margin are research approximations.
    """
    config = config or Config()
    if not adjusted.index.equals(raw_prices.index) or not adjusted.columns.equals(
        raw_prices.columns
    ):
        raise ValueError("Raw and adjusted panels must match")
    if not adjusted.index.equals(roll_events.index) or not adjusted.columns.equals(
        roll_events.columns
    ):
        raise ValueError("Roll panel must match")
    if not adjusted.index.is_unique or not adjusted.index.is_monotonic_increasing:
        raise ValueError("Unique increasing timestamps required")
    if (
        not np.isfinite(adjusted.to_numpy()).all()
        or not np.isfinite(raw_prices.to_numpy()).all()
    ):
        raise ValueError("Finite marks required; negative prices are permitted")
    if (np.asarray(point_values) <= 0).any() or (np.asarray(unit_costs) < 0).any():
        raise ValueError("Invalid multipliers or costs")
    month_ends = eligible_month_ends(adjusted, config)
    if not month_ends:
        raise ValueError("No full signal lookback available")
    anchor = month_ends[0]
    start = adjusted.index.get_loc(anchor)
    dates = adjusted.index
    columns = adjusted.columns
    point = np.asarray(point_values)
    cost = np.asarray(unit_costs)
    dollar_changes = adjusted.diff().mul(point, axis=1)
    notional = raw_prices.mul(point, axis=1)
    median_notional = notional.abs().rolling(config.risk_sessions).median()
    q = np.zeros(len(columns))
    nav = config.capital
    pending = None
    records, positions, decisions, pnl_rows, cost_rows = [], [], [], [], []
    decision_dates = set(month_ends)
    for i in range(start, len(dates)):
        date = dates[i]
        held = q.copy()
        pnl = held * dollar_changes.iloc[i].to_numpy()
        roll_cost = 2 * np.abs(held) * roll_events.iloc[i].to_numpy() * cost
        nav_before = nav
        nav += pnl.sum() - roll_cost.sum()
        execution_cost = np.zeros(len(q))
        executed = False
        if pending is not None:
            q = pending.copy()
            execution_cost = np.abs(q - held) * cost
            nav -= execution_cost.sum()
            executed = True
            pending = None
        if nav <= 0:
            raise ValueError("NAV depleted; no negative-capital continuation")
        notionals = np.maximum(
            np.abs(notional.iloc[i].to_numpy()),
            0.1 * median_notional.iloc[i].to_numpy(),
        )
        gross = float(np.sum(np.abs(q) * notionals) / nav)
        margin = config.margin_proxy_rate * gross
        records.append(
            dict(
                date=date,
                equity=nav,
                gross_pnl=float(pnl.sum()),
                rebalance_cost=float(execution_cost.sum()),
                roll_cost=float(roll_cost.sum()),
                gross_notional_ratio=gross,
                margin_proxy_ratio=margin,
                executed=executed,
                long_markets=int((q > 0).sum()),
                short_markets=int((q < 0).sum()),
                daily_return=nav / nav_before - 1,
            )
        )
        positions.append(q.copy())
        pnl_rows.append(pnl)
        cost_rows.append(execution_cost + roll_cost)
        if date in decision_dates and i < len(dates) - 1:
            past = (
                dates.searchsorted(
                    date - pd.DateOffset(months=config.lookback_months), side="right"
                )
                - 1
            )
            if past < 0:
                raise ValueError("Lookback history unavailable")
            direction = (
                np.ones(len(q))
                if always_long
                else np.sign(
                    adjusted.iloc[i].to_numpy() - adjusted.iloc[past].to_numpy()
                )
            )
            pending, risk = targets(
                dollar_changes.iloc[: i + 1],
                notional.iloc[i].to_numpy(),
                median_notional.iloc[i].to_numpy(),
                direction,
                groups,
                nav,
                config,
            )
            decisions.append(
                dict(
                    signal_date=date,
                    execution_date=dates[i + 1],
                    reason="monthly",
                    predicted_volatility=risk,
                    planned_gross=float(np.sum(np.abs(pending) * notionals) / nav),
                )
            )
        if margin > config.margin_proxy_limit and i < len(dates) - 1:
            pending = q * config.margin_proxy_reduction / margin
            decisions.append(
                dict(
                    signal_date=date,
                    execution_date=dates[i + 1],
                    reason="margin_proxy_reduction",
                    predicted_volatility=np.nan,
                    planned_gross=config.margin_proxy_reduction
                    / config.margin_proxy_rate,
                )
            )
    ledger = pd.DataFrame(records).set_index("date")
    ledger["drawdown"] = ledger.equity / ledger.equity.cummax() - 1
    positions = pd.DataFrame(positions, index=ledger.index, columns=columns)
    pnl = pd.DataFrame(pnl_rows, index=ledger.index, columns=columns)
    costs = pd.DataFrame(cost_rows, index=ledger.index, columns=columns)
    np.testing.assert_allclose(
        ledger.equity.to_numpy(),
        config.capital + (pnl - costs).sum(axis=1).cumsum().to_numpy(),
        rtol=1e-10,
        atol=1e-6,
    )
    return ledger, positions, pd.DataFrame(decisions), pnl, costs


def equity_metrics(equity):
    returns = equity.pct_change().iloc[1:]
    std = returns.std(ddof=1)
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    return dict(
        cagr=float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1),
        annualized_volatility=float(std * np.sqrt(252)),
        sharpe=float(returns.mean() / std * np.sqrt(252)) if std > 0 else None,
        max_drawdown=float((equity / equity.cummax() - 1).min()),
        final_equity=float(equity.iloc[-1]),
        total_return=float(equity.iloc[-1] / equity.iloc[0] - 1),
    )


def spy_benchmark(
    adjusted_close,
    anchor,
    capital,
    target_volatility=None,
    risk_sessions=60,
    execution_bps=1.0,
):
    """Total-return-unit SPY accounting; next-close orders, cash yield zero."""
    dates = adjusted_close.index
    end_month = set(dates.to_series().groupby(dates.to_period("M")).last())
    returns = adjusted_close.pct_change()
    rolling_vol = returns.rolling(risk_sessions).std() * np.sqrt(252)
    start = dates.get_loc(anchor)
    cash, units, pending = float(capital), 0.0, None
    records = []
    for i in range(start, len(dates)):
        price = adjusted_close.iloc[i]
        fee = 0.0
        if pending is not None:
            nav = cash + units * price
            weight = pending
            # Exact fee-inclusive target value, with no negative cash on buys.
            rate = execution_bps / 10000
            old_value = units * price
            buying = weight * nav >= old_value
            sign = 1 if buying else -1
            target_value = (weight * nav + sign * weight * rate * old_value) / (
                1 + sign * weight * rate
            )
            desired_units = target_value / price
            fee = abs(target_value - old_value) * rate
            cash = nav - desired_units * price - fee
            units = desired_units
            pending = None
        nav = cash + units * price
        if cash < -1e-6:
            raise AssertionError("SPY comparator borrowed cash")
        records.append(
            dict(
                date=dates[i],
                equity=nav,
                cash=cash,
                total_return_units=units,
                execution_cost=fee,
            )
        )
        if i < len(dates) - 1 and (
            dates[i] == anchor
            or target_volatility is not None
            and dates[i] in end_month
        ):
            pending = (
                1.0
                if target_volatility is None
                else min(1.0, target_volatility / rolling_vol.iloc[i])
            )
    ledger = pd.DataFrame(records).set_index("date")
    ledger["daily_return"] = ledger.equity.pct_change().fillna(0.0)
    return ledger
