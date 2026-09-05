"""Query and normalize CRSP CIZ delisting outcomes."""

from datetime import date

import pandas as pd


CRSP_DELISTING_SOURCE_COLUMNS = [
    "permno",
    "delistingdt",
    "deldtprc",
    "deldtprcflg",
    "delactiontype",
    "delstatustype",
    "delreasontype",
    "delpaymenttype",
    "delpermno",
    "delpermco",
    "delret",
    "delretmisstype",
    "delnextdt",
    "delnextprc",
    "delnextprcflg",
    "delamtdt",
    "deldivamt",
    "deldistype",
    "deldlydt",
]

CRSP_DELISTING_COLUMNS = [
    "security_id",
    "permno",
    "delisting_date",
    "delisting_date_price",
    "delisting_date_price_flag",
    "action_type",
    "status_type",
    "reason_type",
    "payment_type",
    "successor_permno",
    "successor_permco",
    "delisting_return",
    "return_missing_type",
    "next_price_date",
    "next_price",
    "next_price_flag",
    "amount_date",
    "distribution_amount",
    "distribution_type",
    "daily_return_date",
    "source",
]

DATE_COLUMNS = [
    "delisting_date",
    "next_price_date",
    "amount_date",
    "daily_return_date",
]

NUMERIC_COLUMNS = [
    "delisting_date_price",
    "delisting_return",
    "next_price",
    "distribution_amount",
]


def build_crsp_delisting_query() -> str:
    """Return a parameterized query for delistings in a bounded date range."""
    selected_columns = ",\n            ".join(CRSP_DELISTING_SOURCE_COLUMNS)
    return f"""
        SELECT
            {selected_columns}
        FROM crsp_q_stock.stkdelists
        WHERE delistingdt BETWEEN %(start_date)s AND %(end_date)s
          AND permno = ANY(%(permnos)s)
        ORDER BY permno, delistingdt
    """


def download_crsp_delistings(
    connection,
    permnos: list[int],
    start_date: date | str,
    end_date: date | str,
) -> pd.DataFrame:
    """Download normalized delisting outcomes for selected securities."""
    if not permnos:
        raise ValueError("At least one PERMNO is required")
    if any(not isinstance(permno, int) or permno <= 0 for permno in permnos):
        raise ValueError("Every PERMNO must be a positive integer")

    raw_data = connection.raw_sql(
        build_crsp_delisting_query(),
        params={
            "permnos": sorted(set(permnos)),
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
        date_cols=["delistingdt", "delnextdt", "delamtdt", "deldlydt"],
    )
    return normalize_crsp_delistings(raw_data)


def normalize_crsp_delistings(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Map CRSP delisting fields without imputing missing outcomes."""
    missing = sorted(set(CRSP_DELISTING_SOURCE_COLUMNS) - set(raw_data.columns))
    if missing:
        raise ValueError(f"Missing CRSP delisting columns: {', '.join(missing)}")

    data = raw_data[CRSP_DELISTING_SOURCE_COLUMNS].copy()
    data = data.rename(
        columns={
            "delistingdt": "delisting_date",
            "deldtprc": "delisting_date_price",
            "deldtprcflg": "delisting_date_price_flag",
            "delactiontype": "action_type",
            "delstatustype": "status_type",
            "delreasontype": "reason_type",
            "delpaymenttype": "payment_type",
            "delpermno": "successor_permno",
            "delpermco": "successor_permco",
            "delret": "delisting_return",
            "delretmisstype": "return_missing_type",
            "delnextdt": "next_price_date",
            "delnextprc": "next_price",
            "delnextprcflg": "next_price_flag",
            "delamtdt": "amount_date",
            "deldivamt": "distribution_amount",
            "deldistype": "distribution_type",
            "deldlydt": "daily_return_date",
        }
    )
    data["permno"] = pd.to_numeric(data["permno"], errors="raise").astype("Int64")
    for column in ("successor_permno", "successor_permco"):
        data[column] = pd.to_numeric(data[column], errors="coerce").astype("Int64")
    for column in DATE_COLUMNS:
        data[column] = pd.to_datetime(data[column])
    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["security_id"] = data["permno"].astype(str)
    data["source"] = "CRSP CIZ quarterly"
    data = data[CRSP_DELISTING_COLUMNS].sort_values(
        ["permno", "delisting_date"]
    ).reset_index(drop=True)
    validate_crsp_delistings(data)
    return data


def validate_crsp_delistings(data: pd.DataFrame) -> None:
    """Reject ambiguous dates and economically impossible observed returns."""
    if data.duplicated(["permno", "delisting_date"]).any():
        raise ValueError("Duplicate CRSP PERMNO and delisting date combinations found")
    if (data["delisting_return"].dropna() < -1.0).any():
        raise ValueError("CRSP delisting return cannot be below -100%")
    dated_returns = data["daily_return_date"].notna()
    if (
        data.loc[dated_returns, "daily_return_date"]
        <= data.loc[dated_returns, "delisting_date"]
    ).any():
        raise ValueError("CRSP daily delisting return date must follow delisting date")


def calculate_delisting_terminal_value(
    last_mark: float,
    delisting_return: float | None,
) -> float:
    """Apply one observed CRSP delisting return to the last tradable mark."""
    if last_mark <= 0:
        raise ValueError("Last tradable mark must be positive")
    if delisting_return is None or pd.isna(delisting_return):
        raise ValueError("Observed CRSP delisting return is required")
    if delisting_return < -1.0:
        raise ValueError("CRSP delisting return cannot be below -100%")
    return float(last_mark) * (1.0 + float(delisting_return))
