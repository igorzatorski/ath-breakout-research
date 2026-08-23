import pandas as pd
import pytest

from ath_breakout.data.preparation import prepare_ohlcv_data


def make_valid_data() -> pd.DataFrame:
    """Create the smallest valid multi-security OHLCV table for these tests."""
    return pd.DataFrame(
        {
            "security_id": ["MSFT", "AAPL", "AAPL"],
            "ticker": ["MSFT", "AAPL", "AAPL"],
            "date": ["2024-01-02", "2024-01-03", "2024-01-02"],
            "open": [200, 102, 100],
            "high": [204, 105, 103],
            "low": [198, 101, 99],
            "close": [203, 104, 102],
            "volume": [900000, 1350000, 1200000],
        }
    )


def test_prepares_dates_order_and_index() -> None:
    result = prepare_ohlcv_data(make_valid_data())

    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result["security_id"].tolist() == ["AAPL", "AAPL", "MSFT"]
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-02",
        "2024-01-03",
        "2024-01-02",
    ]
    assert result.index.tolist() == [0, 1, 2]


def test_does_not_change_original_data() -> None:
    original = make_valid_data()

    prepare_ohlcv_data(original)

    assert original["date"].dtype == object
    assert original["security_id"].tolist() == ["MSFT", "AAPL", "AAPL"]


def test_rejects_invalid_date() -> None:
    data = make_valid_data()
    data.loc[0, "date"] = "not-a-date"

    with pytest.raises(ValueError):
        prepare_ohlcv_data(data)


def test_rejects_duplicate_security_date_after_date_conversion() -> None:
    data = make_valid_data()
    data.loc[1, "date"] = "2024-01-02"

    with pytest.raises(
        ValueError,
        match="Duplicate security_id and date combinations found",
    ):
        prepare_ohlcv_data(data)
