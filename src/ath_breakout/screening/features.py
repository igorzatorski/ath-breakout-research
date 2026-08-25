"""Calculate transparent screener features for one security."""

from datetime import date

import pandas as pd


def measure_consolidation(
    data: pd.DataFrame,
    prior_ath: float,
    maximum_sessions: int = 60,
    maximum_close_distance: float = 0.10,
) -> tuple[int, float]:
    """Measure the recent base immediately below a prior ATH."""
    if maximum_sessions <= 0:
        raise ValueError("maximum_sessions must be greater than zero")

    if maximum_close_distance <= 0 or maximum_close_distance >= 1:
        raise ValueError("maximum_close_distance must be between zero and one")

    if len(data) == 0 or pd.isna(prior_ath) or prior_ath <= 0:
        return 0, float("nan")

    minimum_close = prior_ath * (1 - maximum_close_distance)
    recent_history = data.tail(maximum_sessions)
    closes_near_ath = (
        recent_history["split_adj_close"] >= minimum_close
    ).to_numpy()
    consolidation_days = 0

    for close_is_near_ath in closes_near_ath[::-1]:
        if close_is_near_ath == False:
            break

        consolidation_days += 1

    if consolidation_days == 0:
        return 0, float("nan")

    consolidation = recent_history.tail(consolidation_days)
    highest_price = float(consolidation["split_adj_high"].max())
    lowest_price = float(consolidation["split_adj_low"].min())

    if highest_price <= 0:
        return consolidation_days, float("nan")

    consolidation_depth_pct = (
        highest_price - lowest_price
    ) / highest_price
    return consolidation_days, consolidation_depth_pct


def build_security_snapshot(
    data: pd.DataFrame,
    scan_date: date,
    benchmark_data: pd.DataFrame | None = None,
    minimum_history: int = 260,
    minimum_price: float = 5.0,
    minimum_dollar_volume: float = 10_000_000.0,
    maximum_overnight_gap: float = 0.20,
    minimum_consolidation_days: int = 20,
    maximum_consolidation_depth: float = 0.15,
    minimum_base_quality_signals: int = 3,
    minimum_ath_age_sessions: int = 20,
    minimum_breakout_cooldown_sessions: int = 20,
    minimum_sessions_above_sma_200: int = 40,
    minimum_sma_200_slope_20_pct: float = 0.005,
    maximum_drawdown_252: float = 0.30,
    maximum_sma_50_extension: float = 0.15,
    minimum_atr_20_pct: float = 0.005,
    maximum_atr_20_pct: float = 0.05,
) -> dict | None:
    """Build one ranking-ready snapshot at a completed session close."""
    history = data.copy()
    history["date"] = pd.to_datetime(history["date"])
    history = history[history["date"].dt.date <= scan_date]
    history = history.sort_values("date").reset_index(drop=True)

    if len(history) == 0:
        return None

    latest = history.iloc[-1]

    if latest["date"].date() != scan_date:
        return None

    close = float(latest["split_adj_close"])
    prior_ath = latest["prior_ath"]
    recent_20 = history.tail(20)
    recent_60 = history.tail(60)

    average_volume_20 = float(recent_20["volume"].mean())
    average_dollar_volume_20 = float(
        (recent_20["split_adj_close"] * recent_20["volume"]).mean()
    )
    volume_ratio_20 = (
        float(latest["volume"]) / average_volume_20
        if average_volume_20 > 0
        else float("nan")
    )
    latest_range = float(latest["split_adj_high"] - latest["split_adj_low"])
    close_location_in_range = (
        (close - float(latest["split_adj_low"])) / latest_range
        if latest_range > 0
        else 0.5
    )

    ath_distance_pct = (
        close / float(prior_ath) - 1
        if pd.notna(prior_ath) and float(prior_ath) > 0
        else float("nan")
    )

    previous_history = history.iloc[:-1]
    if pd.isna(prior_ath) or len(previous_history) == 0:
        prior_ath_date = None
        sessions_since_prior_ath = None
    else:
        prior_ath_rows = previous_history[
            previous_history["split_adj_high"] == float(prior_ath)
        ]
        if len(prior_ath_rows) == 0:
            prior_ath_date = None
            sessions_since_prior_ath = None
        else:
            prior_ath_index = prior_ath_rows.index[-1]
            prior_ath_date = history.loc[prior_ath_index, "date"].date()
            sessions_since_prior_ath = (
                len(history) - 2 - int(prior_ath_index)
            )

    trend_above_sma_50 = pd.notna(latest["sma_50"]) and close > latest["sma_50"]
    trend_above_sma_100 = (
        pd.notna(latest["sma_100"]) and close > latest["sma_100"]
    )
    trend_above_sma_150 = (
        pd.notna(latest["sma_150"]) and close > latest["sma_150"]
    )
    trend_above_sma_200 = (
        pd.notna(latest["sma_200"]) and close > latest["sma_200"]
    )
    trend_sma_ordered = (
        pd.notna(latest["sma_50"])
        and pd.notna(latest["sma_100"])
        and pd.notna(latest["sma_150"])
        and latest["sma_50"] > latest["sma_100"] > latest["sma_150"]
    )
    trend_score = sum(
        [
            trend_above_sma_50,
            trend_above_sma_100,
            trend_above_sma_150,
            trend_above_sma_200,
            trend_sma_ordered,
        ]
    )

    sessions_above_sma_200 = 0
    above_sma_200_history = (
        history["split_adj_close"] > history["sma_200"]
    )
    for session_is_above in above_sma_200_history.iloc[::-1]:
        if bool(session_is_above) == False:
            break
        sessions_above_sma_200 += 1

    share_above_sma_200_100 = float(
        above_sma_200_history.tail(100).mean()
    )
    rolling_peak_252 = history["split_adj_close"].cummax()
    drawdowns_252 = history["split_adj_close"] / rolling_peak_252 - 1
    maximum_drawdown_252_pct = float(drawdowns_252.tail(252).min())

    sma_200_slope_20_pct = (
        float(latest["sma_200"]) / float(history.iloc[-21]["sma_200"]) - 1
        if len(history) >= 220
        and pd.notna(latest["sma_200"])
        and pd.notna(history.iloc[-21]["sma_200"])
        else float("nan")
    )
    extension_from_sma_50_pct = (
        close / float(latest["sma_50"]) - 1
        if pd.notna(latest["sma_50"]) and float(latest["sma_50"]) > 0
        else float("nan")
    )

    recent_61 = history.tail(61)
    previous_close = recent_61["split_adj_close"].shift(1)
    overnight_gaps = recent_61["split_adj_open"] / previous_close - 1
    maximum_abs_gap_60_pct = overnight_gaps.abs().max()

    if pd.isna(maximum_abs_gap_60_pct):
        maximum_abs_gap_60_pct = 0.0

    previous_close = history["split_adj_close"].shift(1)
    true_ranges = pd.concat(
        [
            history["split_adj_high"] - history["split_adj_low"],
            (history["split_adj_high"] - previous_close).abs(),
            (history["split_adj_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_20_pct = float(true_ranges.tail(20).mean()) / close

    new_ath_close_today = bool(latest["breakout"])

    if new_ath_close_today:
        consolidation_history = history.iloc[:-1]
    else:
        consolidation_history = history

    consolidation_days, consolidation_depth_pct = measure_consolidation(
        consolidation_history,
        float(prior_ath) if pd.notna(prior_ath) else float("nan"),
    )

    base_history = consolidation_history.tail(60)
    base_close = float(base_history.iloc[-1]["split_adj_close"])
    base_true_ranges = _true_ranges(base_history)
    atr_20_base_pct = float(base_true_ranges.tail(20).mean()) / base_close
    atr_60_base_pct = float(base_true_ranges.mean()) / base_close
    atr_contraction_ratio = (
        atr_20_base_pct / atr_60_base_pct
        if atr_60_base_pct > 0
        else float("nan")
    )

    recent_range_10_pct = _range_depth(base_history.tail(10))
    previous_range_20_pct = _range_depth(base_history.iloc[-30:-10])
    range_contraction_ratio = (
        recent_range_10_pct / previous_range_20_pct
        if previous_range_20_pct > 0
        else float("nan")
    )

    recent_volume_10 = float(base_history.tail(10)["volume"].mean())
    previous_volume_20 = float(
        base_history.iloc[-30:-10]["volume"].mean()
    )
    volume_dry_up_ratio = (
        recent_volume_10 / previous_volume_20
        if previous_volume_20 > 0
        else float("nan")
    )

    low_trend_history = consolidation_history.tail(
        min(consolidation_days, 40)
    )
    low_slope_pct_per_session, low_trend_r_squared = _linear_price_trend(
        low_trend_history["split_adj_low"]
    )

    passes_atr_contraction_filter = (
        pd.notna(atr_contraction_ratio) and atr_contraction_ratio <= 1.0
    )
    passes_range_contraction_filter = (
        pd.notna(range_contraction_ratio) and range_contraction_ratio <= 1.0
    )
    passes_rising_lows_filter = (
        pd.notna(low_slope_pct_per_session)
        and low_slope_pct_per_session >= 0
    )
    passes_volume_dry_up_filter = (
        pd.notna(volume_dry_up_ratio) and volume_dry_up_ratio <= 1.0
    )
    base_quality_signals = sum(
        [
            passes_atr_contraction_filter,
            passes_range_contraction_filter,
            passes_rising_lows_filter,
            passes_volume_dry_up_filter,
        ]
    )
    passes_base_quality_filter = (
        base_quality_signals >= minimum_base_quality_signals
    )
    passes_ath_age_filter = (
        sessions_since_prior_ath is not None
        and sessions_since_prior_ath >= minimum_ath_age_sessions
    )

    previous_breakouts = history.iloc[:-1]
    previous_breakouts = previous_breakouts[
        previous_breakouts["breakout"] == True
    ]

    if len(previous_breakouts) == 0:
        previous_breakout_date = None
        sessions_since_previous_breakout = None
    else:
        previous_breakout_index = previous_breakouts.index[-1]
        previous_breakout_date = history.loc[
            previous_breakout_index, "date"
        ].date()
        sessions_since_previous_breakout = (
            len(history) - 1 - previous_breakout_index
        )

    passes_breakout_cooldown_filter = (
        sessions_since_previous_breakout is None
        or sessions_since_previous_breakout
        > minimum_breakout_cooldown_sessions
    )

    relative_strength_3m = _relative_strength(
        history, benchmark_data, scan_date, 63
    )
    relative_strength_6m = _relative_strength(
        history, benchmark_data, scan_date, 126
    )
    relative_strength_12m = _relative_strength(
        history, benchmark_data, scan_date, 252
    )

    base_depth_20_pct = _range_depth(recent_20)
    base_depth_60_pct = _range_depth(recent_60)
    passes_history_filter = len(history) >= minimum_history
    passes_price_filter = close >= minimum_price
    passes_liquidity_filter = average_dollar_volume_20 >= minimum_dollar_volume
    passes_trend_filter = trend_score == 5
    passes_gap_filter = maximum_abs_gap_60_pct <= maximum_overnight_gap
    passes_sma_200_slope_filter = (
        pd.notna(sma_200_slope_20_pct)
        and sma_200_slope_20_pct >= minimum_sma_200_slope_20_pct
    )
    passes_trend_persistence_filter = (
        sessions_above_sma_200 >= minimum_sessions_above_sma_200
    )
    passes_drawdown_filter = (
        maximum_drawdown_252_pct >= -maximum_drawdown_252
    )
    passes_extension_filter = (
        pd.notna(extension_from_sma_50_pct)
        and extension_from_sma_50_pct <= maximum_sma_50_extension
    )
    passes_atr_filter = (
        minimum_atr_20_pct <= atr_20_pct <= maximum_atr_20_pct
    )
    passes_base_duration_filter = (
        consolidation_days >= minimum_consolidation_days
    )
    passes_consolidation_depth_filter = (
        pd.notna(consolidation_depth_pct)
        and consolidation_depth_pct <= maximum_consolidation_depth
    )
    passes_base_filter = (
        passes_base_duration_filter
        and passes_consolidation_depth_filter
        and passes_base_quality_filter
        and passes_breakout_cooldown_filter
    )
    passes_all_basic_filters = all(
        [
            passes_history_filter,
            passes_price_filter,
            passes_liquidity_filter,
            passes_trend_filter,
            passes_gap_filter,
            passes_sma_200_slope_filter,
            passes_trend_persistence_filter,
            passes_drawdown_filter,
            passes_extension_filter,
            passes_atr_filter,
        ]
    )
    passes_all_setup_filters = passes_all_basic_filters and passes_base_filter

    fresh_breakout_today = new_ath_close_today and (
        sessions_since_previous_breakout is None
        or sessions_since_previous_breakout
        > minimum_breakout_cooldown_sessions
    )
    ath_continuation_today = new_ath_close_today and not fresh_breakout_today

    if not passes_all_basic_filters:
        setup_state = "not_eligible"
    elif fresh_breakout_today and passes_base_filter:
        setup_state = "fresh_breakout"
    elif ath_continuation_today and passes_base_filter:
        setup_state = "ath_continuation"
    elif (
        pd.notna(ath_distance_pct)
        and -0.05 <= ath_distance_pct <= 0
        and passes_base_filter
    ):
        setup_state = "base_ready"
    elif pd.notna(ath_distance_pct) and -0.05 <= ath_distance_pct <= 0:
        setup_state = "approaching_ath"
    else:
        setup_state = "trend_candidate"

    scores = _calculate_setup_scores(
        consolidation_days=consolidation_days,
        consolidation_depth_pct=consolidation_depth_pct,
        low_slope_pct_per_session=low_slope_pct_per_session,
        low_trend_r_squared=low_trend_r_squared,
        trend_score=trend_score,
        sma_200_slope_20_pct=sma_200_slope_20_pct,
        relative_strength_values=[
            relative_strength_3m,
            relative_strength_6m,
            relative_strength_12m,
        ],
        ath_distance_pct=ath_distance_pct,
        atr_contraction_ratio=atr_contraction_ratio,
        range_contraction_ratio=range_contraction_ratio,
        volume_dry_up_ratio=volume_dry_up_ratio,
        volume_ratio_20=volume_ratio_20,
        close_location_in_range=close_location_in_range,
        is_breakout=new_ath_close_today,
    )

    return {
        "security_id": latest["security_id"],
        "ticker": latest["ticker"],
        "date": latest["date"].date(),
        "close": close,
        "prior_ath": prior_ath,
        "prior_ath_date": prior_ath_date,
        "sessions_since_prior_ath": sessions_since_prior_ath,
        "ath_distance_pct": ath_distance_pct,
        "new_ath_close_today": new_ath_close_today,
        "fresh_breakout_today": fresh_breakout_today,
        "ath_continuation_today": ath_continuation_today,
        "previous_breakout_date": previous_breakout_date,
        "sessions_since_previous_breakout": sessions_since_previous_breakout,
        "sma_50": latest["sma_50"],
        "sma_100": latest["sma_100"],
        "sma_150": latest["sma_150"],
        "sma_200": latest["sma_200"],
        "sma_200_slope_20_pct": sma_200_slope_20_pct,
        "sessions_above_sma_200": sessions_above_sma_200,
        "share_above_sma_200_100": share_above_sma_200_100,
        "maximum_drawdown_252_pct": maximum_drawdown_252_pct,
        "extension_from_sma_50_pct": extension_from_sma_50_pct,
        "trend_above_sma_50": bool(trend_above_sma_50),
        "trend_above_sma_100": bool(trend_above_sma_100),
        "trend_above_sma_150": bool(trend_above_sma_150),
        "trend_above_sma_200": bool(trend_above_sma_200),
        "trend_sma_ordered": bool(trend_sma_ordered),
        "trend_score": int(trend_score),
        "volume": float(latest["volume"]),
        "volume_average_20": average_volume_20,
        "volume_ratio_20": volume_ratio_20,
        "close_location_in_range": close_location_in_range,
        "liquidity_dollar_volume_20": average_dollar_volume_20,
        "base_depth_20_pct": base_depth_20_pct,
        "base_depth_60_pct": base_depth_60_pct,
        "consolidation_days": consolidation_days,
        "consolidation_depth_pct": consolidation_depth_pct,
        "atr_20_base_pct": atr_20_base_pct,
        "atr_60_base_pct": atr_60_base_pct,
        "atr_contraction_ratio": atr_contraction_ratio,
        "recent_range_10_pct": recent_range_10_pct,
        "previous_range_20_pct": previous_range_20_pct,
        "range_contraction_ratio": range_contraction_ratio,
        "volume_dry_up_ratio": volume_dry_up_ratio,
        "low_slope_pct_per_session": low_slope_pct_per_session,
        "low_trend_r_squared": low_trend_r_squared,
        "relative_strength_3m": relative_strength_3m,
        "relative_strength_6m": relative_strength_6m,
        "relative_strength_12m": relative_strength_12m,
        "base_quality_signals": int(base_quality_signals),
        "maximum_abs_gap_60_pct": float(maximum_abs_gap_60_pct),
        "atr_20_pct": atr_20_pct,
        "history_sessions": len(history),
        "passes_history_filter": passes_history_filter,
        "passes_price_filter": passes_price_filter,
        "passes_liquidity_filter": passes_liquidity_filter,
        "passes_trend_filter": passes_trend_filter,
        "passes_gap_filter": passes_gap_filter,
        "passes_sma_200_slope_filter": passes_sma_200_slope_filter,
        "passes_trend_persistence_filter": passes_trend_persistence_filter,
        "passes_drawdown_filter": passes_drawdown_filter,
        "passes_extension_filter": passes_extension_filter,
        "passes_atr_filter": passes_atr_filter,
        "passes_base_duration_filter": passes_base_duration_filter,
        "passes_consolidation_depth_filter": (
            passes_consolidation_depth_filter
        ),
        "passes_atr_contraction_filter": passes_atr_contraction_filter,
        "passes_range_contraction_filter": passes_range_contraction_filter,
        "passes_rising_lows_filter": passes_rising_lows_filter,
        "passes_volume_dry_up_filter": passes_volume_dry_up_filter,
        "passes_base_quality_filter": passes_base_quality_filter,
        "passes_ath_age_filter": passes_ath_age_filter,
        "passes_breakout_cooldown_filter": (
            passes_breakout_cooldown_filter
        ),
        "passes_base_filter": passes_base_filter,
        "passes_all_basic_filters": passes_all_basic_filters,
        "passes_all_setup_filters": passes_all_setup_filters,
        "setup_state": setup_state,
        **scores,
    }


def _true_ranges(data: pd.DataFrame) -> pd.Series:
    """Return daily true ranges for one chronological price table."""
    previous_close = data["split_adj_close"].shift(1)
    return pd.concat(
        [
            data["split_adj_high"] - data["split_adj_low"],
            (data["split_adj_high"] - previous_close).abs(),
            (data["split_adj_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def _linear_price_trend(prices: pd.Series) -> tuple[float, float]:
    """Return normalized linear slope and R-squared for a price series."""
    clean_prices = prices.dropna().reset_index(drop=True)

    if len(clean_prices) < 2 or clean_prices.mean() <= 0:
        return float("nan"), float("nan")

    sessions = pd.Series(range(len(clean_prices)), dtype="float64")
    session_variance = ((sessions - sessions.mean()) ** 2).sum()
    slope = (
        ((sessions - sessions.mean()) * (clean_prices - clean_prices.mean())).sum()
        / session_variance
    )
    correlation = sessions.corr(clean_prices)
    return float(slope / clean_prices.mean()), float(correlation ** 2)


def _relative_strength(
    security_data: pd.DataFrame,
    benchmark_data: pd.DataFrame | None,
    scan_date: date,
    sessions: int,
) -> float:
    """Return security return minus IWV return over the same sessions."""
    if benchmark_data is None:
        return float("nan")

    if len(security_data) <= sessions or len(benchmark_data) <= sessions:
        return float("nan")

    security_return = (
        float(security_data.iloc[-1]["split_adj_close"])
        / float(security_data.iloc[-sessions - 1]["split_adj_close"])
        - 1
    )
    benchmark_return = (
        float(benchmark_data.iloc[-1]["split_adj_close"])
        / float(benchmark_data.iloc[-sessions - 1]["split_adj_close"])
        - 1
    )
    return security_return - benchmark_return


def _bounded_score(value: float, low: float, high: float) -> float:
    """Scale a value linearly to the inclusive zero-one interval."""
    if pd.isna(value) or high <= low:
        return 0.0

    return max(0.0, min(1.0, (float(value) - low) / (high - low)))


def _calculate_setup_scores(**values) -> dict:
    """Build six setup components and a separate breakout-quality score."""
    depth_points = 10 * (
        1 - _bounded_score(values["consolidation_depth_pct"], 0.05, 0.15)
    )
    rising_low_points = 5 * _bounded_score(
        values["low_slope_pct_per_session"], 0.0, 0.002
    )
    straightness_points = 5 * _bounded_score(
        values["low_trend_r_squared"], 0.0, 0.80
    )
    base_shape_points = (
        depth_points + rising_low_points + straightness_points
    )
    base_maturity_points = 10 * _bounded_score(
        values["consolidation_days"], 10, 40
    )

    available_relative_strength = [
        value
        for value in values["relative_strength_values"]
        if pd.notna(value)
    ]
    if len(available_relative_strength) == 0:
        relative_strength_points = 0.0
    else:
        relative_strength_points = 20 * sum(
            _bounded_score(value, -0.10, 0.10)
            for value in available_relative_strength
        ) / len(available_relative_strength)

    trend_points = (
        10 * values["trend_score"] / 5
        + 10 * _bounded_score(values["sma_200_slope_20_pct"], 0.0, 0.05)
    )

    ath_distance = values["ath_distance_pct"]
    if pd.isna(ath_distance):
        ath_readiness_points = 0.0
    elif ath_distance <= 0:
        ath_readiness_points = 15 * _bounded_score(ath_distance, -0.05, 0.0)
    else:
        ath_readiness_points = 15 * (
            1 - _bounded_score(ath_distance, 0.0, 0.05)
        )
    contraction_points = (
        7.5 * (1 - _bounded_score(values["atr_contraction_ratio"], 0.60, 1.20))
        + 7.5
        * (1 - _bounded_score(values["range_contraction_ratio"], 0.50, 1.50))
    )

    setup_score = (
        base_shape_points
        + base_maturity_points
        + trend_points
        + relative_strength_points
        + contraction_points
        + ath_readiness_points
    )

    if values["is_breakout"]:
        breakout_volume_points = 40 * _bounded_score(
            values["volume_ratio_20"], 0.75, 2.0
        )
        breakout_close_points = 35 * _bounded_score(
            values["close_location_in_range"], 0.50, 1.0
        )
        breakout_extension_points = 25 * (
            1 - _bounded_score(max(ath_distance, 0.0), 0.0, 0.05)
        )
        breakout_quality_score = (
            breakout_volume_points
            + breakout_close_points
            + breakout_extension_points
        )
    else:
        breakout_volume_points = float("nan")
        breakout_close_points = float("nan")
        breakout_extension_points = float("nan")
        breakout_quality_score = float("nan")

    return {
        "setup_base_shape_points": round(base_shape_points, 2),
        "setup_base_maturity_points": round(base_maturity_points, 2),
        "setup_trend_points": round(trend_points, 2),
        "setup_relative_strength_points": round(relative_strength_points, 2),
        "setup_contraction_points": round(contraction_points, 2),
        "setup_ath_readiness_points": round(ath_readiness_points, 2),
        "setup_score": round(setup_score, 2),
        "breakout_volume_points": round(breakout_volume_points, 2),
        "breakout_close_points": round(breakout_close_points, 2),
        "breakout_extension_points": round(breakout_extension_points, 2),
        "breakout_quality_score": round(breakout_quality_score, 2),
    }


def _range_depth(data: pd.DataFrame) -> float:
    """Measure the full high-low range as a fraction of its highest price."""
    highest_price = float(data["split_adj_high"].max())
    lowest_price = float(data["split_adj_low"].min())

    if highest_price <= 0:
        return float("nan")

    return (highest_price - lowest_price) / highest_price
