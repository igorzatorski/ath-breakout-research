"""Incrementally update market data for every known security."""

from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from ath_breakout.data.adapters.yfinance import download_yfinance_ohlcv
from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.processing import process_market_data
from ath_breakout.data.retry_policy import (
    classify_download_error,
    failed_retry_state,
    load_previous_manifest,
    previous_row_for_security,
    retry_is_due,
    successful_retry_state,
)
from ath_breakout.data.storage import (
    load_security_data,
    save_security_data,
    security_file_path,
)
from ath_breakout.data.universe import validate_universe


FULL_HISTORY_START = "1900-01-01"
CORPORATE_ACTION_COLUMNS = {
    "adj_close",
    "dividends",
    "stock_splits",
    "repaired",
}


def print_update_progress(
    completed_batches: int,
    total_batches: int,
    successful: int,
    failed: int,
    total_securities: int | None = None,
) -> None:
    """Print one timestamped progress line for the market-data update."""
    bar_width = 30
    if total_batches == 0:
        completed_width = bar_width
        percentage = 100.0
    else:
        completed_width = int(bar_width * completed_batches / total_batches)
        percentage = 100 * completed_batches / total_batches

    progress_bar = "#" * completed_width + "-" * (bar_width - completed_width)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_width = len(str(max(total_batches, 1)))
    security_capacity = (
        total_securities
        if total_securities is not None
        else max(successful + failed, 1)
    )
    security_width = len(str(max(security_capacity, 1)))

    print(
        f"[{timestamp}] [{progress_bar}] {percentage:6.2f}% "
        f"batch {completed_batches:>{batch_width}}/{total_batches} | "
        f"success: {successful:>{security_width}} | "
        f"failed: {failed:>{security_width}}",
        flush=True,
    )


def requires_full_schema_refresh(raw_file: str | Path) -> bool:
    """Return True when an existing file lacks corporate-action history."""
    file_path = Path(raw_file)

    if not file_path.exists():
        return False

    existing_data = load_security_data(file_path)
    return CORPORATE_ACTION_COLUMNS.issubset(existing_data.columns) == False


def download_start_for_security(
    raw_file: str | Path,
    overlap_days: int = 7,
) -> str:
    """Choose full history for a new file or a short overlap for an update."""
    file_path = Path(raw_file)

    if not file_path.exists():
        return FULL_HISTORY_START

    if requires_full_schema_refresh(file_path):
        return FULL_HISTORY_START

    existing_data = load_security_data(file_path)
    last_date = pd.to_datetime(existing_data["date"]).max()
    download_start = last_date - timedelta(days=overlap_days)
    return download_start.strftime("%Y-%m-%d")


def merge_security_history(
    existing_data: pd.DataFrame,
    downloaded_data: pd.DataFrame,
) -> pd.DataFrame:
    """Combine old and new rows, keeping the newest copy of each session."""
    if len(existing_data) == 0:
        return prepare_ohlcv_data(downloaded_data)

    if len(downloaded_data) == 0:
        return prepare_ohlcv_data(existing_data)

    prepared_existing_data = prepare_ohlcv_data(existing_data)
    prepared_downloaded_data = prepare_ohlcv_data(downloaded_data)
    combined_data = pd.concat(
        [prepared_existing_data, prepared_downloaded_data],
        ignore_index=True,
    )
    combined_data = combined_data.drop_duplicates(
        subset=["security_id", "date"],
        keep="last",
    )
    return prepare_ohlcv_data(combined_data)


def update_market_data(
    universe: pd.DataFrame,
    raw_directory: str | Path,
    processed_directory: str | Path,
    manifest_file: str | Path,
    today: date | None = None,
    download_through: date | None = None,
    batch_size: int = 50,
    full_refresh: bool = False,
    retry_failed_now: bool = False,
) -> pd.DataFrame:
    """Update and process every security in the supplied registry."""
    validate_universe(universe)

    if len(universe) == 0:
        raise ValueError("Universe must contain at least one security")

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    current_date = today or date.today()
    if download_through is None:
        end_date = current_date.isoformat()
    else:
        # Yahoo excludes end_date, so request the day after the target session.
        end_date = (download_through + timedelta(days=1)).isoformat()
    raw_directory_path = Path(raw_directory)
    processed_directory_path = Path(processed_directory)
    manifest_path = Path(manifest_file)
    manifest_rows = []
    previous_manifest = load_previous_manifest(manifest_path)

    download_groups = {}

    for _, security in universe.iterrows():
        security_id = security["security_id"]
        previous_row = previous_row_for_security(
            previous_manifest,
            security_id,
        )

        if (
            full_refresh == False
            and retry_failed_now == False
            and not retry_is_due(
            previous_row,
            current_date,
            )
        ):
            deferred_row = previous_row.to_dict()
            deferred_row["ticker"] = security["ticker"]
            deferred_row["in_current_universe"] = bool(
                security.get("in_current_universe", True)
            )
            deferred_row["status"] = "retry_deferred"
            manifest_rows.append(deferred_row)
            continue

        raw_file = security_file_path(
            raw_directory_path,
            security_id,
        )
        if full_refresh:
            start_date = FULL_HISTORY_START
        else:
            start_date = download_start_for_security(raw_file)
        download_groups.setdefault(start_date, []).append(security)

    total_batches = sum(
        (len(securities) + batch_size - 1) // batch_size
        for securities in download_groups.values()
    )
    total_securities = sum(
        len(securities) for securities in download_groups.values()
    )
    completed_batches = 0

    print_update_progress(
        0,
        total_batches,
        successful=0,
        failed=0,
        total_securities=total_securities,
    )

    for start_date, securities in download_groups.items():
        for batch_start in range(0, len(securities), batch_size):
            security_batch = securities[batch_start : batch_start + batch_size]
            tickers = [security["ticker"] for security in security_batch]
            try:
                downloaded_batch, failed_tickers = download_yfinance_ohlcv(
                    tickers=tickers,
                    start_date=start_date,
                    end_date=end_date,
                    batch_size=batch_size,
                    required_session=download_through,
                )
            except Exception:
                downloaded_batch = pd.DataFrame(columns=["ticker"])
                failed_tickers = tickers

            for security in security_batch:
                security_id = security["security_id"]
                ticker = security["ticker"]
                previous_row = previous_row_for_security(
                    previous_manifest,
                    security_id,
                )
                raw_file = security_file_path(raw_directory_path, security_id)
                processed_file = security_file_path(
                    processed_directory_path,
                    security_id,
                )
                try:
                    ticker_download = downloaded_batch[
                        downloaded_batch["ticker"] == ticker
                    ].copy()

                    if ticker in failed_tickers or len(ticker_download) == 0:
                        raise ValueError("Yahoo returned no valid data")

                    ticker_download["security_id"] = security_id

                    replace_complete_history = (
                        full_refresh or requires_full_schema_refresh(raw_file)
                    )

                    if raw_file.exists() and replace_complete_history == False:
                        existing_data = load_security_data(raw_file)
                    else:
                        existing_data = pd.DataFrame(
                            columns=ticker_download.columns
                        )

                    complete_history = merge_security_history(
                        existing_data,
                        ticker_download,
                    )
                    processed_history = process_market_data(complete_history)

                    save_security_data(complete_history, raw_file)
                    save_security_data(processed_history, processed_file)

                    manifest_row = {
                            "security_id": security_id,
                            "ticker": ticker,
                            "in_current_universe": bool(
                                security.get("in_current_universe", True)
                            ),
                            "status": "success",
                            "last_date": complete_history["date"].max().date(),
                            "updated_at": current_date,
                            "dividend_events": int(
                                (complete_history["dividends"] > 0).sum()
                            ),
                            "split_events": int(
                                (complete_history["stock_splits"] > 0).sum()
                            ),
                            "repaired_rows": int(
                                complete_history["repaired"].sum()
                            ),
                            "error": None,
                    }
                    manifest_row.update(successful_retry_state())
                    manifest_rows.append(manifest_row)
                except Exception as error:
                    error_type = classify_download_error(
                        error,
                        raw_file.exists(),
                    )
                    manifest_row = {
                            "security_id": security_id,
                            "ticker": ticker,
                            "in_current_universe": bool(
                                security.get("in_current_universe", True)
                            ),
                            "status": "failed",
                            "last_date": None,
                            "updated_at": current_date,
                            "dividend_events": None,
                            "split_events": None,
                            "repaired_rows": None,
                            "error": f"{type(error).__name__}: {error}",
                    }
                    manifest_row.update(
                        failed_retry_state(
                            previous_row,
                            current_date,
                            error_type,
                        )
                    )
                    manifest_rows.append(manifest_row)

            manifest = pd.DataFrame(manifest_rows)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_manifest_path = manifest_path.with_suffix(".tmp.csv")
            manifest.to_csv(temporary_manifest_path, index=False)
            temporary_manifest_path.replace(manifest_path)

            completed_batches += 1
            successful_count = (manifest["status"] == "success").sum()
            failed_count = (manifest["status"] == "failed").sum()
            print_update_progress(
                completed_batches,
                total_batches,
                int(successful_count),
                int(failed_count),
                total_securities=total_securities,
            )

    if total_batches == 0:
        manifest = pd.DataFrame(manifest_rows)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_manifest_path = manifest_path.with_suffix(".tmp.csv")
        manifest.to_csv(temporary_manifest_path, index=False)
        temporary_manifest_path.replace(manifest_path)
        print_update_progress(
            0,
            0,
            successful=0,
            failed=0,
            total_securities=0,
        )

    return pd.DataFrame(manifest_rows)
