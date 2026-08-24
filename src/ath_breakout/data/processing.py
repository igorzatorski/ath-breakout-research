"""Transform validated raw prices into strategy-ready features."""

import pandas as pd

from ath_breakout.data.adjustments import add_split_adjusted_prices
from ath_breakout.strategy.ath import add_breakout_signal, add_prior_ath
from ath_breakout.strategy.indicators import add_moving_averages


def process_market_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Recalculate every feature derived from raw daily market data."""
    adjusted_data = add_split_adjusted_prices(raw_data)
    data_with_averages = add_moving_averages(adjusted_data)
    data_with_ath = add_prior_ath(data_with_averages)
    return add_breakout_signal(data_with_ath)
