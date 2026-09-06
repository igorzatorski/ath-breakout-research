import pandas as pd

from ath_breakout.data.crsp_processing import prepare_crsp_strategy_data


def crsp_rows(periods: int = 205) -> pd.DataFrame:
    dates = pd.bdate_range("1993-01-04", periods=periods)
    close = pd.Series(range(100, 100 + periods), dtype=float)
    return pd.DataFrame({
        "security_id": ["14593"] * periods,
        "permno": [14593] * periods,
        "ticker": ["AAPL"] * periods,
        "date": dates,
        "open": close,
        "high": close + 1,
        "low": close - 1,
        "close": close,
        "volume": [1_000.0] * periods,
        "total_return": [0.01] * periods,
        "ordinary_dividend": [0.0] * periods,
        "nonordinary_dividend": [0.0] * periods,
        "price_adjustment_factor": [2.0] * periods,
        "share_adjustment_factor": [2.0] * periods,
        "shares_outstanding": [500.0] * periods,
        "delisting_flag": ["N"] * periods,
        "source": ["CRSP CIZ quarterly"] * periods,
    })


def test_converts_crsp_factors_and_builds_strategy_features() -> None:
    result, report = prepare_crsp_strategy_data(crsp_rows())

    assert report.input_rows == 205
    assert report.output_rows == 205
    assert result.loc[0, "split_adj_close"] == 50.0
    assert result.loc[0, "volume"] == 2_000.0
    assert pd.notna(result.loc[199, "sma_200"])
    assert result["total_return"].iloc[0] == 0.01
    assert result["data_source"].unique().tolist() == ["CRSP CIZ quarterly"]


def test_uses_preperiod_seed_for_prior_ath() -> None:
    seed = pd.DataFrame({"permno": [14593], "prior_comparable_high": [200.0]})

    result, _ = prepare_crsp_strategy_data(crsp_rows(2), seed)

    assert result["prior_ath"].tolist() == [200.0, 200.0]
    assert result["breakout"].tolist() == [False, False]


def test_drops_nontradable_and_inconsistent_rows_with_counts() -> None:
    data = crsp_rows(4)
    data.loc[0, "close"] = None
    data.loc[1, "volume"] = -1
    data.loc[2, "high"] = data.loc[2, "close"] - 1

    result, report = prepare_crsp_strategy_data(data)

    assert len(result) == 1
    assert report.incomplete_ohlcv_rows == 1
    assert report.invalid_volume_rows == 1
    assert report.inconsistent_ohlc_rows == 1


def test_preserves_ticker_history_and_fills_display_gaps() -> None:
    data = crsp_rows(3)
    data["ticker"] = ["OLD", None, "NEW"]

    result, _ = prepare_crsp_strategy_data(data)

    assert result["crsp_ticker"].isna().sum() == 1
    assert result["ticker"].tolist() == ["OLD", "OLD", "NEW"]
