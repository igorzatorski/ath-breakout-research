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


def prepare_ohlcv_data(data: pd.DataFrame) -> pd.DataFrame:
    """Validate, date-convert, sort, and reindex canonical OHLCV data."""
    result = data.copy()

    validate_required_columns(result)
    validate_missing_values(result)
    validate_numeric_columns(result)
    validate_positive_prices(result)
    validate_non_negative_volume(result)
    validate_high_prices(result)
    validate_low_prices(result)

    result["date"] = pd.to_datetime(result["date"], format="%Y-%m-%d")

    validate_unique_security_dates(result)

    result = result.sort_values(["security_id", "date"])
    result = result.reset_index(drop=True)
    return result
