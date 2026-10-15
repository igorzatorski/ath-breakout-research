"""Event definitions and open-to-close holding returns for high-breakout research."""
import numpy as np
import pandas as pd


def prior_252_high(high: pd.Series) -> pd.Series:
    """Input must be reindexed to exchange sessions; require 252 valid prior highs."""
    return high.shift(1).rolling(252, min_periods=252).max()


def holding_return(history: pd.DataFrame, entry: int, horizon: int):
    """Entry-session open through close of the Hth session, entry counted as one.

    CRSP CIZ Y rows already contain the terminal return. Apply it once and
    hold terminal proceeds at zero interest to the horizon. Never carry stale
    stock prices or replace a missing return with zero. Entry ex-date dividends
    are excluded because the investor buys after the ex-date open.
    """
    if entry + horizon > len(history):
        return np.nan, "censored", False
    window = history.iloc[entry:entry + horizon]
    first = window.iloc[0]
    if not np.isfinite(first.open) or first.open <= 0:
        return np.nan, "missing_entry_open", False
    if not np.isfinite(first.close) or first.close <= 0:
        return np.nan, "missing_entry_close", False
    if first.delisting_flag == "Y":
        return np.nan, "terminal_on_entry", False
    wealth = float(first.close / first.open)
    for row in window.iloc[1:].itertuples():
        if not np.isfinite(row.total_return) or row.total_return < -1:
            return np.nan, "missing_or_invalid_return", False
        wealth *= 1 + row.total_return
        if row.delisting_flag == "Y":
            return wealth - 1, "ok_terminal_cash", True
        if not np.isfinite(row.close) or row.close <= 0:
            return np.nan, "missing_close_without_terminal", False
    return wealth - 1, "ok", False


def spy_holding_return(spy: pd.DataFrame, entry: int, horizon: int):
    """Same entry convention; future dividend reinvestment via adjusted close."""
    if entry + horizon > len(spy):
        return np.nan
    window = spy.iloc[entry:entry + horizon]
    first = window.iloc[0]
    if (not np.isfinite(window.adj_close).all() or (window.adj_close <= 0).any()
            or not np.isfinite(first.open) or first.open <= 0
            or not np.isfinite(first.close) or first.close <= 0):
        return np.nan
    return float(first.close / first.open * window.adj_close.iloc[-1] / first.adj_close - 1)
