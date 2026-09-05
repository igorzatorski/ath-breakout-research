import pandas as pd
import pytest

from ath_breakout.data.crsp_returns import validate_crsp_return_components


def test_validates_no_distribution_ordinary_and_nonordinary_rows() -> None:
    data = pd.DataFrame(
        {
            "total_return": [0.01, 0.02, -0.10],
            "return_ex_distributions": [0.01, 0.01, -0.10],
            "income_return": [0.0, 0.01, 0.0],
            "ordinary_dividend": [0.0, 0.25, 0.0],
            "nonordinary_dividend": [0.0, 0.0, 1.5],
            "period_price_factor": [0.0, 0.0, -0.1],
            "distribution_return_flag": ["NO", "C1", "P1"],
        }
    )
    result = validate_crsp_return_components(data)

    assert result.no_distribution_rows == 1
    assert result.ordinary_distribution_rows == 1
    assert result.nonordinary_distribution_rows == 1
    assert result.return_identity_rows == 3


def test_rejects_return_difference_without_distribution() -> None:
    data = pd.DataFrame(
        {
            "total_return": [0.02],
            "return_ex_distributions": [0.01],
            "income_return": [0.0],
            "ordinary_dividend": [0.0],
            "nonordinary_dividend": [0.0],
            "period_price_factor": [0.0],
            "distribution_return_flag": ["NO"],
        }
    )

    with pytest.raises(ValueError, match="without a distribution"):
        validate_crsp_return_components(data)


def test_rejects_missing_distribution_flag() -> None:
    data = pd.DataFrame(
        {
            "total_return": [0.02],
            "return_ex_distributions": [0.01],
            "income_return": [0.01],
            "ordinary_dividend": [0.25],
            "nonordinary_dividend": [0.0],
            "period_price_factor": [0.0],
            "distribution_return_flag": [None],
        }
    )

    with pytest.raises(ValueError, match="missing its impact flag"):
        validate_crsp_return_components(data)
