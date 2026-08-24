"""Calculate indicators used by the ATH strategy."""

import pandas as pd


MOVING_AVERAGE_WINDOWS = (50, 100, 150)


def add_moving_averages(data: pd.DataFrame) -> pd.DataFrame:
    """Add full-window moving averages for each security."""
    result = data.copy()

    for window in MOVING_AVERAGE_WINDOWS:
        result[f"sma_{window}"] = result.groupby("security_id")[
            "split_adj_close"
        ].transform(
            lambda prices: prices.rolling(
                window=window,
                min_periods=window,
            ).mean()
        )

    return result
