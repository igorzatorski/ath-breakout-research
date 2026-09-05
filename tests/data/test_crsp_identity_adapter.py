from decimal import Decimal

import pandas as pd
import pytest

from ath_breakout.data.adapters.crsp_identity import (
    CRSP_IDENTITY_COLUMNS,
    build_crsp_identity_query,
    download_crsp_identity_history,
    normalize_crsp_identity_history,
)


def identity_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "permno": 12345,
                "permco": 100,
                "secinfostartdt": "2020-01-01",
                "secinfoenddt": "2022-06-08",
                "ticker": "OLD",
                "tradingsymbol": "OLD",
                "securitynm": "EXAMPLE CLASS A",
                "issuernm": "EXAMPLE INC",
                "cusip": "00000010",
                "cusip9": "000000100",
                "primaryexch": "Q",
                "tradingstatusflg": "A",
                "securityactiveflg": "Y",
            },
            {
                "permno": 12345,
                "permco": Decimal("100"),
                "secinfostartdt": "2022-06-09",
                "secinfoenddt": "2026-12-31",
                "ticker": "NEW",
                "tradingsymbol": "NEW",
                "securitynm": "EXAMPLE CLASS A",
                "issuernm": "EXAMPLE INC",
                "cusip": "00000010",
                "cusip9": "000000100",
                "primaryexch": "Q",
                "tradingstatusflg": "A",
                "securityactiveflg": "Y",
            },
        ]
    )


def test_normalizes_ticker_change_under_one_permno() -> None:
    result = normalize_crsp_identity_history(identity_rows())

    assert result.columns.tolist() == CRSP_IDENTITY_COLUMNS
    assert result["security_id"].tolist() == ["12345", "12345"]
    assert result["ticker"].tolist() == ["OLD", "NEW"]
    assert result["effective_from"].dt.strftime("%Y-%m-%d").tolist() == [
        "2020-01-01",
        "2022-06-09",
    ]


def test_rejects_overlapping_identity_intervals() -> None:
    rows = identity_rows()
    rows.loc[1, "secinfostartdt"] = "2022-06-08"

    with pytest.raises(ValueError, match="Overlapping"):
        normalize_crsp_identity_history(rows)


def test_identity_query_is_parameterized() -> None:
    query = build_crsp_identity_query()

    assert "ANY(%(permnos)s)" in query
    assert "%(start_date)s" in query
    assert "%(end_date)s" in query


class FakeConnection:
    def __init__(self) -> None:
        self.params = None

    def raw_sql(self, query, params, date_cols):
        self.params = params
        return identity_rows()


def test_download_deduplicates_permnos_and_passes_bounds() -> None:
    connection = FakeConnection()

    result = download_crsp_identity_history(
        connection,
        permnos=[12345, 12345],
        start_date="2022-01-01",
        end_date="2022-12-31",
    )

    assert len(result) == 2
    assert connection.params == {
        "permnos": [12345],
        "start_date": "2022-01-01",
        "end_date": "2022-12-31",
    }
