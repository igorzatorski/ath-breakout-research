"""Query and normalize point-in-time CRSP security identity history."""

from datetime import date

import pandas as pd


CRSP_IDENTITY_SOURCE_COLUMNS = [
    "permno",
    "permco",
    "secinfostartdt",
    "secinfoenddt",
    "ticker",
    "tradingsymbol",
    "securitynm",
    "issuernm",
    "cusip",
    "cusip9",
    "primaryexch",
    "tradingstatusflg",
    "securityactiveflg",
]

CRSP_IDENTITY_COLUMNS = [
    "security_id",
    "permno",
    "permco",
    "effective_from",
    "effective_to",
    "ticker",
    "trading_symbol",
    "security_name",
    "issuer_name",
    "cusip",
    "cusip9",
    "primary_exchange",
    "trading_status",
    "security_active_flag",
    "source",
]


def build_crsp_identity_query() -> str:
    """Return a parameterized query for overlapping identity records."""
    selected_columns = ",\n            ".join(CRSP_IDENTITY_SOURCE_COLUMNS)
    return f"""
        SELECT
            {selected_columns}
        FROM crsp_q_stock.stksecurityinfohist
        WHERE permno = ANY(%(permnos)s)
          AND secinfostartdt <= %(end_date)s
          AND secinfoenddt >= %(start_date)s
        ORDER BY permno, secinfostartdt, secinfoenddt
    """


def download_crsp_identity_history(
    connection,
    permnos: list[int],
    start_date: date | str,
    end_date: date | str,
) -> pd.DataFrame:
    """Download normalized identity records overlapping a requested window."""
    if not permnos:
        raise ValueError("At least one PERMNO is required")
    if any(not isinstance(permno, int) or permno <= 0 for permno in permnos):
        raise ValueError("Every PERMNO must be a positive integer")

    raw_data = connection.raw_sql(
        build_crsp_identity_query(),
        params={
            "permnos": sorted(set(permnos)),
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
        date_cols=["secinfostartdt", "secinfoenddt"],
    )
    return normalize_crsp_identity_history(raw_data)


def normalize_crsp_identity_history(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Map CRSP identity history to stable point-in-time field names."""
    missing = sorted(set(CRSP_IDENTITY_SOURCE_COLUMNS) - set(raw_data.columns))
    if missing:
        raise ValueError(f"Missing CRSP identity columns: {', '.join(missing)}")

    data = raw_data[CRSP_IDENTITY_SOURCE_COLUMNS].copy()
    data = data.rename(
        columns={
            "secinfostartdt": "effective_from",
            "secinfoenddt": "effective_to",
            "tradingsymbol": "trading_symbol",
            "securitynm": "security_name",
            "issuernm": "issuer_name",
            "primaryexch": "primary_exchange",
            "tradingstatusflg": "trading_status",
            "securityactiveflg": "security_active_flag",
        }
    )
    data["effective_from"] = pd.to_datetime(data["effective_from"])
    data["effective_to"] = pd.to_datetime(data["effective_to"])
    data["permno"] = pd.to_numeric(data["permno"], errors="raise").astype("Int64")
    data["permco"] = pd.to_numeric(data["permco"], errors="coerce").astype("Int64")
    data["security_id"] = data["permno"].astype(str)
    for column in (
        "ticker",
        "trading_symbol",
        "security_name",
        "issuer_name",
        "cusip",
        "cusip9",
        "primary_exchange",
        "trading_status",
        "security_active_flag",
    ):
        data[column] = data[column].astype("string")
    data["source"] = "CRSP CIZ quarterly"
    data = data[CRSP_IDENTITY_COLUMNS].sort_values(
        ["permno", "effective_from", "effective_to"]
    ).reset_index(drop=True)
    validate_crsp_identity_history(data)
    return data


def validate_crsp_identity_history(data: pd.DataFrame) -> None:
    """Reject invalid or overlapping effective identity intervals."""
    if data.empty:
        return
    if (data["effective_from"] > data["effective_to"]).any():
        raise ValueError("CRSP identity interval starts after it ends")
    if data.duplicated(["permno", "effective_from", "effective_to"]).any():
        raise ValueError("Duplicate CRSP identity intervals found")

    ordered = data.sort_values(["permno", "effective_from", "effective_to"])
    previous_end = ordered.groupby("permno")["effective_to"].shift(1)
    if (ordered["effective_from"] <= previous_end).fillna(False).any():
        raise ValueError("Overlapping CRSP identity intervals found")
