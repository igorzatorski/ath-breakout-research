"""Calculate all-time-high levels without look-ahead bias."""

import pandas as pd


def add_prior_ath(data: pd.DataFrame) -> pd.DataFrame:
    """Add each security's highest price observed before each session."""
    result = data.copy()
    previous_high = result.groupby("security_id")["split_adj_high"].shift(1)
    result["prior_ath"] = previous_high.groupby(result["security_id"]).cummax()
    return result


def add_breakout_signal(data: pd.DataFrame) -> pd.DataFrame:
    """Mark sessions that close strictly above the prior ATH."""
    result = data.copy()
    result["breakout"] = result["split_adj_close"] > result["prior_ath"]
    return result
