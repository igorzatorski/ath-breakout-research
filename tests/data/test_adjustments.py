import pandas as pd

from ath_breakout.data.adjustments import add_split_adjusted_prices


def make_prices(
    closes: list[float],
    split_ratios: list[float],
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "security_id": ["TEST"] * len(closes),
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "stock_splits": split_ratios,
            "prices_split_adjusted": [False] * len(closes),
        }
    )


def test_leaves_prices_unchanged_without_a_split() -> None:
    data = make_prices([100.0, 105.0], [0.0, 0.0])

    result = add_split_adjusted_prices(data)

    assert result["split_adj_close"].tolist() == [100.0, 105.0]


def test_adjusts_prices_before_two_for_one_split() -> None:
    data = make_prices([100.0, 52.0, 55.0], [0.0, 2.0, 0.0])

    result = add_split_adjusted_prices(data)

    assert result["split_adj_close"].tolist() == [50.0, 52.0, 55.0]


def test_adjusts_prices_before_reverse_split() -> None:
    data = make_prices([10.0, 51.0], [0.0, 0.2])

    result = add_split_adjusted_prices(data)

    assert result["split_adj_close"].tolist() == [50.0, 51.0]


def test_combines_multiple_later_splits() -> None:
    data = make_prices(
        [120.0, 62.0, 32.0],
        [0.0, 2.0, 2.0],
    )

    result = add_split_adjusted_prices(data)

    assert result["split_adj_close"].tolist() == [30.0, 31.0, 32.0]


def test_does_not_change_raw_prices() -> None:
    data = make_prices([100.0, 52.0], [0.0, 2.0])

    result = add_split_adjusted_prices(data)

    assert result["close"].tolist() == [100.0, 52.0]
    assert "split_adj_close" not in data.columns


def test_does_not_adjust_yahoo_prices_twice() -> None:
    data = make_prices([50.0, 52.0], [0.0, 2.0])
    data["prices_split_adjusted"] = True

    result = add_split_adjusted_prices(data)

    assert result["split_adj_close"].tolist() == [50.0, 52.0]
