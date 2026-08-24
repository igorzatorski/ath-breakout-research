"""Create price series used for strategy calculations."""

import pandas as pd


SPLIT_ADJUSTED_PRICE_COLUMNS = (
    "split_adj_open",
    "split_adj_high",
    "split_adj_low",
    "split_adj_close",
)


def add_split_adjusted_prices(data: pd.DataFrame) -> pd.DataFrame:
    """Return split-adjusted OHLC without adjusting for dividends."""
    result = data.copy()
    split_ratios = result["stock_splits"].where(
        result["stock_splits"] > 0,
        1.0,
    )

    future_split_factor = split_ratios.groupby(result["security_id"]).transform(
        lambda values: (
            values.iloc[::-1].cumprod().iloc[::-1] / values
        )
    )
    adjustment_factor = future_split_factor.where(
        result["prices_split_adjusted"] == False,
        1.0,
    )

    source_columns = ("open", "high", "low", "close")

    for source_column, adjusted_column in zip(
        source_columns,
        SPLIT_ADJUSTED_PRICE_COLUMNS,
    ):
        result[adjusted_column] = result[source_column] / adjustment_factor

    return result
