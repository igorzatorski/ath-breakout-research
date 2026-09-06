from datetime import date

import pandas as pd
import pytest

from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.processing import process_market_data
from ath_breakout.screening.features import (
    build_security_snapshot,
    measure_consolidation,
)


def make_processed_prices() -> pd.DataFrame:
    dates = pd.bdate_range(end="2024-12-03", periods=260)
    trend = [100 * (1.007 ** index) for index in range(220)]
    old_ath = trend[-1] * 1.003
    base = [old_ath * (0.94 + 0.0005 * index) for index in range(39)]
    closes = trend + base + [old_ath * 1.01]
    raw_data = pd.DataFrame(
        {
            "security_id": ["AAPL"] * len(dates),
            "ticker": ["AAPL"] * len(dates),
            "date": dates,
            "open": closes,
            "high": [price * 1.003 for price in closes],
            "low": [price * 0.997 for price in closes],
            "close": closes,
            "volume": [1_000_000] * len(dates),
        }
    )
    return process_market_data(prepare_ohlcv_data(raw_data))


def test_builds_ranking_ready_security_snapshot() -> None:
    data = make_processed_prices()

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["date"] == date(2024, 12, 3)
    assert result["history_sessions"] == 260
    assert result["trend_score"] == 5
    assert result["volume_ratio_20"] == 1.0
    assert result["liquidity_dollar_volume_20"] > 10_000_000
    assert result["passes_all_basic_filters"] == True
    assert result["new_ath_close_today"] == True
    assert result["fresh_breakout_today"] == True
    assert result["ath_continuation_today"] == False


    assert result["sessions_since_prior_ath"] == 39
    assert result["passes_ath_age_filter"] == True
    assert result["setup_state"] == "fresh_breakout"
    assert result["base_quality_signals"] >= 3
    assert 0 <= result["setup_score"] <= 100
    component_total = sum(
        [
            result["setup_base_shape_points"],
            result["setup_base_maturity_points"],
            result["setup_trend_points"],
            result["setup_relative_strength_points"],
            result["setup_contraction_points"],
            result["setup_ath_readiness_points"],
        ]
    )
    assert result["setup_score"] == pytest.approx(component_total, abs=0.02)
    assert 0 <= result["breakout_quality_score"] <= 100


def test_prepared_snapshot_path_matches_standard_path() -> None:
    data = make_processed_prices()
    benchmark = data.copy()

    standard = build_security_snapshot(
        data,
        date(2024, 12, 3),
        benchmark_data=benchmark,
    )
    prepared = build_security_snapshot(
        data,
        date(2024, 12, 3),
        benchmark_data=benchmark,
        data_is_prepared=True,
        benchmark_is_prepared=True,
    )

    pd.testing.assert_series_equal(
        pd.Series(prepared),
        pd.Series(standard),
        check_names=False,
    )


def test_nominal_price_and_liquidity_are_not_adjusted_price_filters():
    data = make_processed_prices()
    data["nominal_close"] = 4.0
    data["nominal_volume"] = 100.0
    result = build_security_snapshot(data, date(2024, 12, 3))
    assert result["passes_all_basic_filters"] == False
    assert result["liquidity_dollar_volume_20"] == 400.0


def test_price_and_liquidity_filters_use_point_in_time_nominal_prices() -> None:
    data = make_processed_prices()
    data["close"] = 50.0
    data["volume"] = 300_000
    data["split_adj_close"] = 1.0

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["passes_price_filter"] == True
    assert result["liquidity_dollar_volume_20"] == 15_000_000


def test_calculates_relative_strength_against_iwv() -> None:
    data = make_processed_prices()
    benchmark = data[["date", "split_adj_close"]].copy()
    benchmark["split_adj_close"] = 100.0

    result = build_security_snapshot(
        data,
        date(2024, 12, 3),
        benchmark_data=benchmark,
    )

    assert result is not None
    assert result["relative_strength_3m"] > 0
    assert result["relative_strength_6m"] > 0
    assert result["setup_relative_strength_points"] > 10


def test_breakout_volume_changes_confirmation_not_setup_score() -> None:
    ordinary_volume = make_processed_prices()
    high_breakout_volume = ordinary_volume.copy()
    high_breakout_volume.loc[high_breakout_volume.index[-1], "volume"] *= 2

    ordinary_result = build_security_snapshot(
        ordinary_volume,
        date(2024, 12, 3),
    )
    high_volume_result = build_security_snapshot(
        high_breakout_volume,
        date(2024, 12, 3),
    )

    assert ordinary_result is not None
    assert high_volume_result is not None
    assert high_volume_result["setup_score"] == ordinary_result["setup_score"]
    assert (
        high_volume_result["breakout_quality_score"]
        > ordinary_result["breakout_quality_score"]
    )


def test_requires_at_least_fifteen_consolidation_sessions() -> None:
    data = make_processed_prices()

    result = build_security_snapshot(
        data,
        date(2024, 12, 3),
        minimum_consolidation_days=60,
    )

    assert result is not None
    assert result["consolidation_days"] < 60
    assert result["passes_base_duration_filter"] == False
    assert result["passes_base_filter"] == False


def test_recent_repeat_breakout_fails_the_base_cooldown() -> None:
    data = make_processed_prices()
    data.loc[data.index[:-1], "breakout"] = False
    data.loc[data.index[-6], "breakout"] = True
    data.loc[data.index[-1], "breakout"] = True

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["fresh_breakout_today"] == False
    assert result["ath_continuation_today"] == True
    assert result["passes_breakout_cooldown_filter"] == False
    assert result["setup_state"] == "trend_candidate"


def test_does_not_reject_setup_only_for_a_recent_intraday_ath() -> None:
    data = make_processed_prices()
    recent_ath_index = data.index[-2]
    recent_ath = float(data.loc[data.index[-1], "prior_ath"]) * 1.01
    data.loc[recent_ath_index, "split_adj_high"] = recent_ath
    data.loc[data.index[-1], "prior_ath"] = recent_ath

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["sessions_since_prior_ath"] == 0
    assert result["passes_ath_age_filter"] == False
    assert result["passes_base_filter"] == True


def test_rejects_trend_without_enough_time_above_sma_200() -> None:
    data = make_processed_prices()

    result = build_security_snapshot(
        data,
        date(2024, 12, 3),
        minimum_sessions_above_sma_200=100,
    )

    assert result is not None
    assert result["passes_trend_persistence_filter"] == False
    assert result["passes_all_basic_filters"] == False


def test_rejects_excessive_yearly_drawdown() -> None:
    data = make_processed_prices()

    result = build_security_snapshot(
        data,
        date(2024, 12, 3),
        maximum_drawdown_252=0.01,
    )

    assert result is not None
    assert result["passes_drawdown_filter"] == False
    assert result["passes_all_basic_filters"] == False


def test_rejects_monster_gap_from_basic_setup_filters() -> None:
    data = make_processed_prices()
    gap_index = data.index[-20]
    previous_close = data.loc[gap_index - 1, "split_adj_close"]
    data.loc[gap_index, "split_adj_open"] = previous_close * 1.50

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["maximum_abs_gap_60_pct"] == pytest.approx(0.50)
    assert result["passes_gap_filter"] == False
    assert result["passes_all_basic_filters"] == False
    assert result["setup_state"] == "not_eligible"


def test_rejects_overnight_gap_above_twenty_percent() -> None:
    data = make_processed_prices()
    gap_index = data.index[-20]
    previous_close = data.loc[gap_index - 1, "split_adj_close"]
    data.loc[gap_index, "split_adj_open"] = previous_close * 1.21

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["maximum_abs_gap_60_pct"] == pytest.approx(0.21)
    assert result["passes_gap_filter"] == False


def test_rejects_price_more_than_fifteen_percent_above_sma_50() -> None:
    data = make_processed_prices()
    latest_index = data.index[-1]
    close = float(data.loc[latest_index, "split_adj_close"])
    data.loc[latest_index, "sma_50"] = close / 1.16
    data.loc[latest_index, "sma_100"] = close / 1.20
    data.loc[latest_index, "sma_150"] = close / 1.25

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["extension_from_sma_50_pct"] == pytest.approx(0.16)
    assert result["passes_extension_filter"] == False


def test_rejects_atr_above_five_percent() -> None:
    data = make_processed_prices()
    recent_indices = data.index[-20:]
    data.loc[recent_indices, "split_adj_high"] = (
        data.loc[recent_indices, "split_adj_close"] * 1.04
    )
    data.loc[recent_indices, "split_adj_low"] = (
        data.loc[recent_indices, "split_adj_close"] * 0.96
    )

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["atr_20_pct"] > 0.05
    assert result["passes_atr_filter"] == False


def test_does_not_require_sma_150_above_sma_200() -> None:
    data = make_processed_prices()
    latest_index = data.index[-1]
    data.loc[latest_index, "sma_200"] = (
        data.loc[latest_index, "sma_150"] + 1.0
    )

    result = build_security_snapshot(data, date(2024, 12, 3))

    assert result is not None
    assert result["trend_above_sma_200"] == True
    assert result["passes_trend_filter"] == True


def test_measures_consecutive_base_below_prior_ath() -> None:
    old_history = pd.DataFrame(
        {
            "split_adj_close": [80.0],
            "split_adj_high": [82.0],
            "split_adj_low": [79.0],
        }
    )
    base = pd.DataFrame(
        {
            "split_adj_close": [96.0] * 15,
            "split_adj_high": [102.0] * 15,
            "split_adj_low": [95.0] * 15,
        }
    )
    data = pd.concat([old_history, base], ignore_index=True)

    days, depth = measure_consolidation(data, prior_ath=100.0)

    assert days == 15
    assert depth == pytest.approx((102.0 - 95.0) / 102.0)


def test_snapshot_excludes_breakout_day_from_consolidation_depth() -> None:
    data = make_processed_prices()
    scan_date = data.iloc[-1]["date"].date()
    data.loc[data.index[-1], "split_adj_high"] *= 2
    data.loc[data.index[-1], "breakout"] = True

    result = build_security_snapshot(data, scan_date)

    assert result is not None
    assert result["consolidation_depth_pct"] < 0.20
    assert result["consolidation_days"] <= 60


def test_rejects_consolidation_deeper_than_fifteen_percent() -> None:
    data = make_processed_prices()
    scan_date = data.iloc[-1]["date"].date()
    deep_low_index = data.index[-10]
    data.loc[deep_low_index, "split_adj_low"] = (
        data.loc[deep_low_index, "split_adj_high"] * 0.80
    )

    result = build_security_snapshot(data, scan_date)

    assert result is not None
    assert result["consolidation_depth_pct"] > 0.15
    assert result["passes_base_duration_filter"] == True
    assert result["passes_consolidation_depth_filter"] == False
    assert result["passes_base_filter"] == False
    assert result["setup_state"] == "trend_candidate"


def test_rejects_security_without_the_scan_date() -> None:
    data = make_processed_prices()

    result = build_security_snapshot(data, date(2024, 12, 4))

    assert result is None


def test_skips_breakout_without_prior_base_history() -> None:
    data = make_processed_prices().iloc[[0]].copy()
    data["breakout"] = True

    result = build_security_snapshot(data, data.iloc[0]["date"].date())

    assert result is None


def test_historical_score_ignores_future_benchmark_rows() -> None:
    data = make_processed_prices()
    scan_date = data.iloc[-1]["date"].date()
    benchmark = data[["date", "split_adj_close"]].copy()
    future = pd.DataFrame(
        {
            "date": [pd.Timestamp(scan_date) + pd.Timedelta(days=1)],
            "split_adj_close": [benchmark.iloc[-1]["split_adj_close"] * 10],
        }
    )

    point_in_time = build_security_snapshot(data, scan_date, benchmark)
    with_future = build_security_snapshot(
        data,
        scan_date,
        pd.concat([benchmark, future], ignore_index=True),
    )

    assert point_in_time is not None
    assert with_future is not None
    assert with_future["relative_strength_12m"] == pytest.approx(
        point_in_time["relative_strength_12m"]
    )
    assert with_future["setup_score"] == point_in_time["setup_score"]
