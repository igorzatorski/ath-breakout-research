"""Prepare market data from any source for strategy calculations."""

import pandas as pd

from ath_breakout.data.validation import validate_high_prices
from ath_breakout.data.validation import validate_low_prices
from ath_breakout.data.validation import validate_missing_values
from ath_breakout.data.validation import validate_non_negative_volume
from ath_breakout.data.validation import validate_numeric_columns
from ath_breakout.data.validation import validate_positive_prices
from ath_breakout.data.validation import validate_required_columns
from ath_breakout.data.validation import validate_unique_security_dates
from ath_breakout.data.validation import validate_corporate_actions


def add_corporate_action_defaults(data: pd.DataFrame) -> pd.DataFrame:
    """Add neutral values when a source does not supply corporate actions."""
    result = data.copy()

    if "adj_close" not in result.columns:
        result["adj_close"] = result["close"]

    if "dividends" not in result.columns:
        result["dividends"] = 0.0

    if "stock_splits" not in result.columns:
        result["stock_splits"] = 0.0

    if "repaired" not in result.columns:
        result["repaired"] = False

    # Yahoo already supplies split-adjusted historical OHLC. Older project
    # files came from Yahoo, so True is also the safe migration default.
    if "prices_split_adjusted" not in result.columns:
        result["prices_split_adjusted"] = True

    return result


def prepare_ohlcv_data(data: pd.DataFrame) -> pd.DataFrame:
    """Validate, date-convert, sort, and reindex canonical OHLCV data."""
    result = data.copy()

    validate_required_columns(result)
    result = add_corporate_action_defaults(result)
    validate_missing_values(result)
    validate_numeric_columns(result)
    validate_positive_prices(result)
    validate_non_negative_volume(result)
    validate_high_prices(result)
    validate_low_prices(result)
    validate_corporate_actions(result)

    result["date"] = pd.to_datetime(result["date"], format="%Y-%m-%d")

    validate_unique_security_dates(result)

    result = result.sort_values(["security_id", "date"])
    result = result.reset_index(drop=True)
    return result
