"""Fixed closing-trigger exit families with next-session opening execution."""
import numpy as np
import pandas as pd


def signal_atr(data, window=20):
    """Simple mean true range; data must be indexed to exchange sessions."""
    factor = data.price_adjustment_factor.where(
        np.isfinite(data.price_adjustment_factor) & data.price_adjustment_factor.gt(0))
    high, low, close = data.high / factor, data.low / factor, data.close / factor
    previous = close.shift(1)
    valid = (np.isfinite(high) & np.isfinite(low) & np.isfinite(close)
             & np.isfinite(previous) & low.gt(0) & high.ge(low)
             & high.ge(close) & low.le(close) & previous.gt(0))
    tr = pd.concat([high-low, (high-previous).abs(), (low-previous).abs()], axis=1).max(axis=1).where(valid)
    return tr.rolling(window, min_periods=window).mean()


def simulate_exit(window, rule, prior_ath, atr):
    """126 or fewer prescribed sessions; one entry and one exit, no reinvestment."""
    if rule not in {"hold_126", "failed_breakout", "atr_trend"}:
        raise ValueError("Unknown fixed exit rule")
    if not len(window):
        return {"status": "empty"}
    first = window.iloc[0]
    if not np.isfinite(first.open) or first.open <= 0:
        return {"status": "missing_entry_open"}
    if not np.isfinite(first.price_adjustment_factor) or first.price_adjustment_factor <= 0:
        return {"status": "invalid_entry_factor"}
    if rule == "atr_trend" and (not np.isfinite(atr) or atr <= 0):
        return {"status": "invalid_signal_atr"}
    entry = first.open / first.price_adjustment_factor
    initial = max(0, entry - 2 * atr) if np.isfinite(atr) else np.nan
    peak = entry
    wealth = 1.0
    previous_close = np.nan
    pending = False
    trigger_session = np.nan
    worst_close = 1.0
    for i, row in enumerate(window.itertuples()):
        if i and row.delisting_flag == "Y":
            if not np.isfinite(row.total_return) or row.total_return < -1:
                return {"status": "missing_terminal_return"}
            wealth *= 1 + row.total_return
            return _result(wealth, i, "terminal_cash", trigger_session, worst_close)
        factor = row.price_adjustment_factor
        if not np.isfinite(factor) or factor <= 0:
            return {"status": "invalid_price_basis"}
        if pending:
            if not np.isfinite(row.open) or row.open <= 0:
                return {"status": "missing_scheduled_exit_open", "trigger_session": trigger_session}
            dividends = row.ordinary_dividend + row.nonordinary_dividend
            if not np.isfinite(dividends) or dividends < 0:
                return {"status": "invalid_exit_distributions"}
            wealth *= ((row.open + dividends) / factor) / previous_close
            return _result(wealth, i, "trigger_next_open", trigger_session, worst_close)
        if not np.isfinite(row.close) or row.close <= 0:
            return {"status": "missing_regular_close"}
        if i:
            if not np.isfinite(row.total_return) or row.total_return < -1:
                return {"status": "missing_regular_return"}
            wealth *= 1 + row.total_return
        else:
            wealth = row.close / row.open
        worst_close = min(worst_close, wealth)
        current = row.close / factor
        if i == len(window) - 1:
            return _result(wealth, i, "horizon_close", trigger_session, worst_close)
        peak = max(peak, current)
        level = prior_ath if rule == "failed_breakout" else max(initial, peak-3*atr) if rule == "atr_trend" else -np.inf
        if current < level:
            pending = True
            trigger_session = i + 1
        previous_close = current
    raise AssertionError("Unreachable empty exit")


def _result(wealth, exit_index, reason, trigger_session, worst_close):
    return {"status": "ok", "gross_return": float(wealth-1),
            "net_return": float(wealth * .999 / 1.001 - 1),
            "exit_index": exit_index, "exit_reason": reason,
            "holding_sessions": exit_index if reason == "trigger_next_open" else exit_index+1,
            "trigger_session": trigger_session,
            "worst_observed_close_return": min(worst_close, wealth)-1}


def matched_spy_return(window, exit_index, exit_reason):
    """Gross SPY over identical opening entry and opening/closing exit times."""
    first = window.iloc[0]
    if exit_reason != "trigger_next_open":
        last = window.iloc[exit_index]
        return float(first.close / first.open * last.adj_close / first.adj_close - 1)
    if exit_index == 0:
        return 0.0
    previous = window.iloc[exit_index-1]
    current = window.iloc[exit_index]
    previous_wealth = first.close / first.open * previous.adj_close / first.adj_close
    return float(previous_wealth * (current.open+current.dividends) / previous.close - 1)
