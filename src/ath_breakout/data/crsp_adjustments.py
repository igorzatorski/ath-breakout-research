"""Create comparable CRSP price, share, and volume series."""

import pandas as pd


RAW_PRICE_COLUMNS = ("open", "high", "low", "close")
COMPARABLE_PRICE_COLUMNS = (
    "comparable_open",
    "comparable_high",
    "comparable_low",
    "comparable_close",
)


def add_crsp_comparable_values(data: pd.DataFrame) -> pd.DataFrame:
    """Apply CRSP cumulative adjustment factors on their documented basis."""
    required = {
        *RAW_PRICE_COLUMNS,
        "volume",
        "shares_outstanding",
        "price_adjustment_factor",
        "share_adjustment_factor",
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing CRSP adjustment columns: {', '.join(missing)}")

    result = data.copy()
    price_factor = pd.to_numeric(result["price_adjustment_factor"], errors="coerce")
    share_factor = pd.to_numeric(result["share_adjustment_factor"], errors="coerce")

    price_rows = result[list(RAW_PRICE_COLUMNS)].notna().any(axis=1)
    if (price_factor[price_rows].isna() | (price_factor[price_rows] <= 0)).any():
        raise ValueError("CRSP price adjustment factor must be positive for price rows")

    share_rows = result[["volume", "shares_outstanding"]].notna().any(axis=1)
    if (share_factor[share_rows].isna() | (share_factor[share_rows] <= 0)).any():
        raise ValueError("CRSP share adjustment factor must be positive for share rows")

    for raw_column, comparable_column in zip(
        RAW_PRICE_COLUMNS,
        COMPARABLE_PRICE_COLUMNS,
    ):
        result[comparable_column] = result[raw_column] / price_factor

    result["comparable_volume"] = result["volume"] * share_factor
    result["comparable_shares_outstanding"] = (
        result["shares_outstanding"] * share_factor
    )
    return result
