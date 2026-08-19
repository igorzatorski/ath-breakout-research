import pandas as pd
import pytest

from ath_breakout.data.validation import validate_required_columns, validate_unique_dates


def test_accepts_all_required_columns() -> None:
    data = pd.DataFrame(
        columns=["date", "open", "high", "low", "close", "volume"]
    )

    validate_required_columns(data)


def test_rejects_missing_columns() -> None:
    data = pd.DataFrame(columns=["date", "open", "high", "low", "close"])

    with pytest.raises(ValueError, match="Missing required columns: volume"):
        validate_required_columns(data)


def test_accepts_unique_dates() -> None:
    data = pd.DataFrame({"date": ["2024-01-02", "2024-01-03"]})

    validate_unique_dates(data)


def test_rejects_duplicate_dates() -> None:
    data = pd.DataFrame({"date": ["2024-01-02", "2024-01-02"]})

    with pytest.raises(ValueError, match="Duplicate trading dates found"):
        validate_unique_dates(data)
