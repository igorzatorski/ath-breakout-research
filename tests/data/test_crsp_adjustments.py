import pandas as pd
import pytest

from ath_breakout.data.crsp_adjustments import add_crsp_comparable_values


def test_applies_crsp_price_and_share_factors_in_documented_directions() -> None:
    data = pd.DataFrame(
        {
            "open": [400.0, 101.0],
            "high": [408.0, 104.0],
            "low": [396.0, 99.0],
            "close": [404.0, 102.0],
            "volume": [25.0, 100.0],
            "shares_outstanding": [4_000.0, 16_000.0],
            "price_adjustment_factor": [4.0, 1.0],
            "share_adjustment_factor": [4.0, 1.0],
        }
    )

    result = add_crsp_comparable_values(data)

    assert result["comparable_open"].tolist() == [100.0, 101.0]
    assert result["comparable_high"].tolist() == [102.0, 104.0]
    assert result["comparable_low"].tolist() == [99.0, 99.0]
    assert result["comparable_close"].tolist() == [101.0, 102.0]
    assert result["comparable_volume"].tolist() == [100.0, 100.0]
    assert result["comparable_shares_outstanding"].tolist() == [16_000.0, 16_000.0]


@pytest.mark.parametrize("factor", [0.0, -1.0, None])
def test_rejects_invalid_price_factor_when_price_exists(factor) -> None:
    data = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.0],
            "volume": [10.0],
            "shares_outstanding": [1_000.0],
            "price_adjustment_factor": [factor],
            "share_adjustment_factor": [1.0],
        }
    )

    with pytest.raises(ValueError, match="price adjustment factor"):
        add_crsp_comparable_values(data)


def test_does_not_modify_source_data() -> None:
    data = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.0],
            "volume": [10.0],
            "shares_outstanding": [1_000.0],
            "price_adjustment_factor": [1.0],
            "share_adjustment_factor": [1.0],
        }
    )

    add_crsp_comparable_values(data)

    assert "comparable_close" not in data.columns
