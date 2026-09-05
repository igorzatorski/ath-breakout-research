from decimal import Decimal

import pandas as pd
import pytest

from ath_breakout.data.adapters.crsp_delistings import (
    CRSP_DELISTING_COLUMNS,
    build_crsp_delisting_query,
    calculate_delisting_terminal_value,
    download_crsp_delistings,
    normalize_crsp_delistings,
)


def delisting_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "permno": 12345,
                "delistingdt": "2025-06-10",
                "deldtprc": Decimal("10"),
                "deldtprcflg": "TR",
                "delactiontype": "MER",
                "delstatustype": "FPAY",
                "delreasontype": "UNAV",
                "delpaymenttype": "CASH",
                "delpermno": None,
                "delpermco": None,
                "delret": Decimal("-0.25"),
                "delretmisstype": None,
                "delnextdt": "2025-06-11",
                "delnextprc": Decimal("7.5"),
                "delnextprcflg": "TR",
                "delamtdt": "2025-06-11",
                "deldivamt": Decimal("7.5"),
                "deldistype": "CASH",
                "deldlydt": "2025-06-11",
            }
        ]
    )


def test_normalizes_observed_delisting_without_imputation() -> None:
    result = normalize_crsp_delistings(delisting_rows())

    assert result.columns.tolist() == CRSP_DELISTING_COLUMNS
    assert result.loc[0, "security_id"] == "12345"
    assert result.loc[0, "delisting_return"] == pytest.approx(-0.25)
    assert result.loc[0, "daily_return_date"] == pd.Timestamp("2025-06-11")


def test_preserves_missing_delisting_return() -> None:
    rows = delisting_rows()
    rows.loc[0, "delret"] = None

    result = normalize_crsp_delistings(rows)

    assert pd.isna(result.loc[0, "delisting_return"])


def test_rejects_impossible_delisting_return() -> None:
    rows = delisting_rows()
    rows.loc[0, "delret"] = Decimal("-1.01")

    with pytest.raises(ValueError, match="below -100%"):
        normalize_crsp_delistings(rows)


def test_calculates_terminal_value_once() -> None:
    assert calculate_delisting_terminal_value(40.0, -0.25) == pytest.approx(30.0)


def test_refuses_to_invent_missing_terminal_value() -> None:
    with pytest.raises(ValueError, match="return is required"):
        calculate_delisting_terminal_value(40.0, None)


def test_delisting_query_is_parameterized() -> None:
    query = build_crsp_delisting_query()

    assert "ANY(%(permnos)s)" in query
    assert "%(start_date)s" in query
    assert "%(end_date)s" in query


class FakeConnection:
    def __init__(self) -> None:
        self.params = None

    def raw_sql(self, query, params, date_cols):
        self.params = params
        return delisting_rows()


def test_download_deduplicates_permnos_and_passes_bounds() -> None:
    connection = FakeConnection()

    result = download_crsp_delistings(
        connection,
        permnos=[12345, 12345],
        start_date="2025-01-01",
        end_date="2025-12-31",
    )

    assert len(result) == 1
    assert connection.params == {
        "permnos": [12345],
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    }
