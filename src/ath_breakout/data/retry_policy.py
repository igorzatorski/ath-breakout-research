"""Remember download failures and decide when a ticker should be retried."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd


RETRY_COLUMNS = [
    "download_state",
    "failure_count",
    "last_failure_date",
    "next_retry_date",
    "error_type",
]


def load_previous_manifest(manifest_file: str | Path) -> pd.DataFrame:
    """Load the last status of each security, including older manifests."""
    manifest_path = Path(manifest_file)

    if not manifest_path.exists():
        return pd.DataFrame(columns=["security_id"] + RETRY_COLUMNS)

    manifest = pd.read_csv(manifest_path)

    for column in RETRY_COLUMNS:
        if column not in manifest.columns:
            manifest[column] = None

    return manifest.drop_duplicates("security_id", keep="last")


def previous_row_for_security(
    previous_manifest: pd.DataFrame,
    security_id: str,
) -> pd.Series | None:
    """Return the previous manifest row for one security when available."""
    matching_rows = previous_manifest[
        previous_manifest["security_id"] == security_id
    ]

    if len(matching_rows) == 0:
        return None

    return matching_rows.iloc[-1]


def retry_is_due(previous_row: pd.Series | None, current_date: date) -> bool:
    """Return True when a security may be downloaded today."""
    if previous_row is None:
        return True

    next_retry = previous_row.get("next_retry_date")

    if pd.isna(next_retry) or next_retry in (None, ""):
        return True

    return current_date >= pd.to_datetime(next_retry).date()


def successful_retry_state() -> dict:
    """Clear all failure information after a successful download."""
    return {
        "download_state": "active",
        "failure_count": 0,
        "last_failure_date": None,
        "next_retry_date": None,
        "error_type": None,
    }


def failed_retry_state(
    previous_row: pd.Series | None,
    current_date: date,
    error_type: str,
) -> dict:
    """Increment failures and choose daily or weekly retry frequency."""
    previous_count = 0

    if previous_row is not None and not pd.isna(previous_row.get("failure_count")):
        previous_count = int(previous_row["failure_count"])

    failure_count = previous_count + 1
    retry_delay_days = 1 if failure_count < 3 else 7
    download_state = "retry_pending" if failure_count < 3 else "weekly_retry"

    return {
        "download_state": download_state,
        "failure_count": failure_count,
        "last_failure_date": current_date,
        "next_retry_date": current_date + timedelta(days=retry_delay_days),
        "error_type": error_type,
    }


def classify_download_error(error: Exception, raw_file_exists: bool) -> str:
    """Assign a small, honest category to a failed update."""
    message = str(error).lower()

    if "no valid data" in message:
        if raw_file_exists:
            return "update_unavailable"
        return "no_data"

    if "missing values" in message or "required columns" in message:
        return "invalid_data"

    return "processing_error"
