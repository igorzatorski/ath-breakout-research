"""Describe event price paths without selecting or simulating exit rules."""
import numpy as np
import pandas as pd


def wealth_path(window: pd.DataFrame):
    """Close wealth from entry open, retaining CIZ terminal return exactly once."""
    wealth = np.full(len(window), np.nan)
    if not len(window):
        return wealth, "empty", -1
    first = window.iloc[0]
    if not np.isfinite(first.open) or first.open <= 0:
        return wealth, "missing_entry_open", -1
    if not np.isfinite(first.close) or first.close <= 0:
        return wealth, "missing_entry_close", -1
    wealth[0] = first.close / first.open
    terminal = -1
    for i, row in enumerate(window.iloc[1:].itertuples(), start=1):
        if not np.isfinite(row.total_return) or row.total_return < -1:
            return wealth, "invalid_return", terminal
        wealth[i] = wealth[i-1] * (1 + row.total_return)
        if row.delisting_flag == "Y":
            wealth[i:] = wealth[i]
            terminal = i
            break
        if not np.isfinite(row.close) or row.close <= 0:
            return wealth, "missing_close_without_terminal", terminal
    return wealth, "ok", terminal


def first_session(mask):
    """One-based first observation; NaN when milestone was never observed."""
    indices = np.flatnonzero(mask)
    return int(indices[0] + 1) if len(indices) else np.nan


def describe_path(window, frozen_level, level_252):
    wealth, status, terminal = wealth_path(window)
    result = {"status": status}
    if status != "ok":
        return result, wealth
    prices = window.close / window.price_adjustment_factor
    entry = window.open.iloc[0] / window.price_adjustment_factor.iloc[0]
    lows = window.low / window.price_adjustment_factor
    highs = window.high / window.price_adjustment_factor
    valid_bar = (np.isfinite(lows) & np.isfinite(highs) & lows.gt(0)
                 & highs.ge(lows) & highs.ge(prices) & lows.le(prices)
                 & np.isfinite(window.price_adjustment_factor) & window.price_adjustment_factor.gt(0))
    observed = len(window) if terminal < 0 else terminal
    intraday_complete = bool(valid_bar.iloc[:observed].all())
    below = prices.lt(frozen_level).to_numpy()
    below252 = prices.lt(level_252).to_numpy()
    first20 = first_session(wealth >= 1.2 - 1e-12)
    before20 = int(first20) if np.isfinite(first20) else len(window)
    prefix_intraday_complete = bool(valid_bar.iloc[:min(observed, before20)].all())
    end = float(wealth[-1] - 1)
    result.update({
        "return_126": end,
        "cohort": "winner20" if end >= .2 - 1e-12 else "loser" if end < 0 else "other",
        "terminal_session": terminal + 1 if terminal >= 0 else np.nan,
        "first_plus20_close": first20,
        "first_minus5_close": first_session(wealth <= .95 + 1e-12),
        "first_minus10_close": first_session(wealth <= .9 + 1e-12),
        "first_below_level": first_session(below),
        "first_below_252": first_session(below252),
        "below_level_by5": bool(below[:5].any()),
        "below_252_by5": bool(below252[:5].any()),
        "below_level_before20": bool(below[:before20].any()) if np.isfinite(first20) else np.nan,
        "below_252_before20": bool(below252[:before20].any()) if np.isfinite(first20) else np.nan,
        "min_close_return": float(min(1, wealth.min()) - 1),
        "max_close_return": float(max(1, wealth.max()) - 1),
        "min_close_before20": float(min(1, wealth[:before20].min()) - 1) if np.isfinite(first20) else np.nan,
        "intraday_complete": intraday_complete,
        "min_price_return": float(min(entry, lows.iloc[:observed].min()) / entry - 1) if intraday_complete else np.nan,
        "max_price_return": float(max(entry, highs.iloc[:observed].max()) / entry - 1) if intraday_complete else np.nan,
        "min_price_before20": float(min(entry, lows.iloc[:min(observed, before20)].min()) / entry - 1)
                              if np.isfinite(first20) and prefix_intraday_complete else np.nan,
        "landmark5_eligible": bool((terminal < 0 or terminal > 4) and np.isfinite(prices.iloc[4]) and prices.iloc[4] > 0),
        "return_after5": float(wealth[-1] / wealth[4] - 1) if wealth[4] > 0 else np.nan,
    })
    return result, wealth
