from decimal import Decimal

import pandas as pd
import pytest

from ath_breakout.data.adapters.crsp import (
    CRSP_DAILY_COLUMNS,
    CRSP_DAILY_SOURCE_COLUMNS,
    build_crsp_daily_query,
    download_crsp_daily,
    normalize_crsp_daily,
)


def sample_crsp_rows() -> pd.DataFrame:
    rows = []
    for date, close in [("2025-01-03", "243.36"), ("2025-01-02", "243.85")]:
        row = {column: None for column in CRSP_DAILY_SOURCE_COLUMNS}
        row.update(
            {
                "permno": 14593,
                "permco": 7,
                "ticker": "AAPL",
                "dlycaldt": date,
                "dlyopen": Decimal("242.00"),
                "dlyhigh": Decimal("244.00"),
                "dlylow": Decimal("241.00"),
                "dlyclose": Decimal(close),
                "dlyvol": Decimal("50000000"),
                "dlyret": Decimal("0.001"),
                "dlyretx": Decimal("0.001"),
                "dlyorddivamt": Decimal("0"),
                "dlynonorddivamt": Decimal("0"),
                "dlyfacprc": Decimal("0"),
                "dlydistretflg": "NO",
                "dlycumfacpr": Decimal("1"),
                "dlycumfacshr": Decimal("1"),
                "dlycap": Decimal("3500000000"),
                "shrout": 15000000,
                "primaryexch": "Q",
                "conditionaltype": "RW",
                "tradingstatusflg": "A",
                "sharetype": "NS",
                "securitytype": "EQTY",
                "securitysubtype": "COM",
                "usincflg": "Y",
                "issuertype": "CORP",
                "dlydelflg": "N",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def test_normalizes_crsp_daily_rows_to_stable_contract() -> None:
    result = normalize_crsp_daily(sample_crsp_rows())

    assert result.columns.tolist() == CRSP_DAILY_COLUMNS
    assert result["security_id"].tolist() == ["14593", "14593"]
    assert result["ticker"].tolist() == ["AAPL", "AAPL"]
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2025-01-02",
        "2025-01-03",
    ]
    assert result["close"].tolist() == [243.85, 243.36]
    assert result["source"].unique().tolist() == ["CRSP CIZ quarterly"]


def test_rejects_missing_source_columns() -> None:
    with pytest.raises(ValueError, match="Missing CRSP daily columns: dlyhigh"):
        normalize_crsp_daily(sample_crsp_rows().drop(columns="dlyhigh"))


def test_rejects_duplicate_permno_dates() -> None:
    duplicated = pd.concat(
        [sample_crsp_rows().iloc[[0]], sample_crsp_rows().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate CRSP PERMNO"):
        normalize_crsp_daily(duplicated)


class RecordingConnection:
    def __init__(self, result: pd.DataFrame):
        self.result = result
        self.query = None
        self.parameters = None

    def raw_sql(self, query, params, date_cols):
        self.query = query
        self.parameters = params
        assert date_cols == ["dlycaldt"]
        return self.result


def test_download_uses_bounded_parameterized_query() -> None:
    connection = RecordingConnection(sample_crsp_rows())

    result = download_crsp_daily(
        connection,
        permnos=[14593, 14593],
        start_date="2025-01-01",
        end_date="2025-12-31",
    )

    assert "FROM crsp_q_stock.dsf_v2" in connection.query
    assert "ANY(%(permnos)s)" in connection.query
    assert connection.parameters == {
        "permnos": [14593],
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    }
    assert len(result) == 2


@pytest.mark.parametrize("permnos", [[], [0], [-1], ["14593"]])
def test_download_rejects_invalid_permnos(permnos) -> None:
    with pytest.raises(ValueError):
        download_crsp_daily(
            RecordingConnection(sample_crsp_rows()),
            permnos=permnos,
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
