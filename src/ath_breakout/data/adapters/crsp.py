"""Query and normalize CRSP Stock Version 2 daily data."""

from datetime import date

import pandas as pd


CRSP_DAILY_SOURCE_COLUMNS = [
    "permno",
    "permco",
    "ticker",
    "dlycaldt",
    "dlyopen",
    "dlyhigh",
    "dlylow",
    "dlyclose",
    "dlyvol",
    "dlyret",
    "dlyretx",
    "dlyorddivamt",
    "dlynonorddivamt",
    "dlycumfacpr",
    "dlycumfacshr",
    "dlycap",
    "shrout",
    "primaryexch",
    "conditionaltype",
    "tradingstatusflg",
    "sharetype",
    "securitytype",
    "securitysubtype",
    "usincflg",
    "issuertype",
    "dlydelflg",
]

CRSP_DAILY_COLUMNS = [
    "security_id",
    "permno",
    "permco",
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "total_return",
    "return_ex_distributions",
    "ordinary_dividend",
    "nonordinary_dividend",
    "price_adjustment_factor",
    "share_adjustment_factor",
    "market_cap",
    "shares_outstanding",
    "primary_exchange",
    "conditional_type",
    "trading_status",
    "share_type",
    "security_type",
    "security_subtype",
    "us_incorporation_flag",
    "issuer_type",
    "delisting_flag",
    "source",
]

NUMERIC_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "total_return",
    "return_ex_distributions",
    "ordinary_dividend",
    "nonordinary_dividend",
    "price_adjustment_factor",
    "share_adjustment_factor",
    "market_cap",
    "shares_outstanding",
]


def build_crsp_daily_query() -> str:
    """Return the parameterized query for CRSP quarterly daily stock rows."""
    selected_columns = ",\n            ".join(CRSP_DAILY_SOURCE_COLUMNS)
    return f"""
        SELECT
            {selected_columns}
        FROM crsp_q_stock.dsf_v2
        WHERE permno = ANY(%(permnos)s)
          AND dlycaldt BETWEEN %(start_date)s AND %(end_date)s
        ORDER BY permno, dlycaldt
    """


def download_crsp_daily(
    connection,
    permnos: list[int],
    start_date: date | str,
    end_date: date | str,
) -> pd.DataFrame:
    """Download and normalize a bounded set of CRSP daily stock rows."""
    if len(permnos) == 0:
        raise ValueError("At least one PERMNO is required")
    if any(not isinstance(permno, int) or permno <= 0 for permno in permnos):
        raise ValueError("Every PERMNO must be a positive integer")

    raw_data = connection.raw_sql(
        build_crsp_daily_query(),
        params={
            "permnos": sorted(set(permnos)),
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
        date_cols=["dlycaldt"],
    )
    return normalize_crsp_daily(raw_data)


def normalize_crsp_daily(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Convert CRSP CIZ daily rows into the source-neutral raw contract."""
    missing = sorted(set(CRSP_DAILY_SOURCE_COLUMNS) - set(raw_data.columns))
    if missing:
        raise ValueError(f"Missing CRSP daily columns: {', '.join(missing)}")

    data = raw_data[CRSP_DAILY_SOURCE_COLUMNS].copy()
    data = data.rename(
        columns={
            "dlycaldt": "date",
            "dlyopen": "open",
            "dlyhigh": "high",
            "dlylow": "low",
            "dlyclose": "close",
            "dlyvol": "volume",
            "dlyret": "total_return",
            "dlyretx": "return_ex_distributions",
            "dlyorddivamt": "ordinary_dividend",
            "dlynonorddivamt": "nonordinary_dividend",
            "dlycumfacpr": "price_adjustment_factor",
            "dlycumfacshr": "share_adjustment_factor",
            "dlycap": "market_cap",
            "shrout": "shares_outstanding",
            "primaryexch": "primary_exchange",
            "conditionaltype": "conditional_type",
            "tradingstatusflg": "trading_status",
            "sharetype": "share_type",
            "securitytype": "security_type",
            "securitysubtype": "security_subtype",
            "usincflg": "us_incorporation_flag",
            "issuertype": "issuer_type",
            "dlydelflg": "delisting_flag",
        }
    )
    data["date"] = pd.to_datetime(data["date"])
    data["security_id"] = data["permno"].astype("Int64").astype(str)
    data["ticker"] = data["ticker"].astype("string")
    data["source"] = "CRSP CIZ quarterly"

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data[CRSP_DAILY_COLUMNS]
    data = data.sort_values(["permno", "date"]).reset_index(drop=True)
    if data.duplicated(["permno", "date"]).any():
        raise ValueError("Duplicate CRSP PERMNO and date combinations found")
    return data
