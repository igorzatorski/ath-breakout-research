from decimal import Decimal

import pandas as pd
import pytest

from ath_breakout.data.adapters.crsp_universe import (
    CRSP_UNIVERSE_COLUMNS,
    build_crsp_liquidity_universe_query,
    build_crsp_universe_history_query,
    download_crsp_liquidity_universe,
    download_crsp_universe_history_batch,
    normalize_crsp_liquidity_universe,
    normalize_crsp_universe_history,
)


def universe_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "permno": 2,
                "ticker": "SECOND",
                "median_dollar_volume": Decimal("2000000"),
                "observation_count": 60,
                "last_price": Decimal("20"),
                "market_cap": Decimal("500000"),
                "primary_exchange": "Q",
            },
            {
                "permno": 1,
                "ticker": "FIRST",
                "median_dollar_volume": Decimal("3000000"),
                "observation_count": 61,
                "last_price": Decimal("30"),
                "market_cap": Decimal("700000"),
                "primary_exchange": "N",
            },
        ]
    )


def test_normalizes_ranked_point_in_time_universe() -> None:
    result = normalize_crsp_liquidity_universe(
        universe_rows(),
        formation_date="2025-09-30",
        effective_date="2025-10-01",
        maximum_size=3_000,
    )

    assert result.columns.tolist() == CRSP_UNIVERSE_COLUMNS
    assert result["permno"].tolist() == [1, 2]
    assert result["rank"].tolist() == [1, 2]
    assert result["security_id"].tolist() == ["1", "2"]


def test_rejects_same_day_effective_membership() -> None:
    with pytest.raises(ValueError, match="effective after formation"):
        normalize_crsp_liquidity_universe(
            universe_rows(),
            formation_date="2025-09-30",
            effective_date="2025-09-30",
            maximum_size=3_000,
        )


def test_query_filters_common_stocks_and_aggregates_on_server() -> None:
    query = build_crsp_liquidity_universe_query()

    assert "PERCENTILE_CONT(0.5)" in query
    assert "securitysubtype = 'COM'" in query
    assert "sharetype = 'NS'" in query
    assert "LIMIT %(universe_size)s" in query


class FakeConnection:
    def __init__(self) -> None:
        self.params = None

    def raw_sql(self, query, params):
        self.params = params
        return universe_rows()


def test_download_passes_bounded_ranking_parameters() -> None:
    connection = FakeConnection()

    result = download_crsp_liquidity_universe(
        connection,
        lookback_start="2025-07-01",
        formation_date="2025-09-30",
        effective_date="2025-10-01",
    )

    assert len(result) == 2
    assert connection.params == {
        "lookback_start": "2025-07-01",
        "formation_date": "2025-09-30",
        "minimum_observations": 40,
        "minimum_price": 5.0,
        "universe_size": 3_000,
    }


def test_normalizes_multiple_monthly_snapshots() -> None:
    first = universe_rows()
    first["formation_date"] = "2025-08-29"
    first["effective_date"] = "2025-09-02"
    first["rank"] = [2, 1]
    second = universe_rows()
    second["formation_date"] = "2025-09-30"
    second["effective_date"] = "2025-10-01"
    second["rank"] = [2, 1]

    result = normalize_crsp_universe_history(
        pd.concat([first, second], ignore_index=True), maximum_size=3_000
    )

    assert result["formation_date"].nunique() == 2
    assert result.groupby("formation_date")["rank"].apply(list).tolist() == [
        [1, 2],
        [1, 2],
    ]


def test_history_query_forms_monthly_rankings_on_server() -> None:
    query = build_crsp_universe_history_query()

    assert "GROUP BY DATE_TRUNC('month', dlycaldt)" in query
    assert "PARTITION BY formation_date" in query
    assert "rank <= %(universe_size)s" in query


class FakeHistoryConnection:
    def __init__(self) -> None:
        self.params = None
        self.date_cols = None

    def raw_sql(self, query, params, date_cols):
        self.params = params
        self.date_cols = date_cols
        rows = universe_rows()
        rows["formation_date"] = "2025-09-30"
        rows["effective_date"] = "2025-10-01"
        rows["rank"] = [2, 1]
        return rows


def test_downloads_yearly_history_batch_with_bounds() -> None:
    connection = FakeHistoryConnection()

    result = download_crsp_universe_history_batch(
        connection,
        lookback_start="2024-10-01",
        formation_start="2025-01-01",
        formation_end="2025-12-31",
    )

    assert len(result) == 2
    assert connection.params["formation_start"] == "2025-01-01"
    assert connection.params["formation_end"] == "2025-12-31"
    assert connection.date_cols == ["formation_date", "effective_date"]
