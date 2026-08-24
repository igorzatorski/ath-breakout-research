"""Incrementally update market data for every known security."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from ath_breakout.data.adapters.yfinance import download_yfinance_ohlcv
from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.storage import (
    load_security_data,
    save_security_data,
    security_file_path,
)
from ath_breakout.data.universe import validate_universe
from ath_breakout.strategy.ath import add_breakout_signal, add_prior_ath


FULL_HISTORY_START = "1900-01-01"


def download_start_for_security(
    raw_file: str | Path,
    overlap_days: int = 7,
) -> str:
    """Choose full history for a new file or a short overlap for an update."""
    file_path = Path(raw_file)

    if not file_path.exists():
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

    combined_data = pd.concat(
        [existing_data, downloaded_data],
        ignore_index=True,
    )
    combined_data = combined_data.drop_duplicates(
        subset=["security_id", "date"],
        keep="last",
    )
    return prepare_ohlcv_data(combined_data)


def process_security_history(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Recalculate all currently available strategy columns."""
    data_with_ath = add_prior_ath(raw_data)
    return add_breakout_signal(data_with_ath)


def update_market_data(
    universe: pd.DataFrame,
    raw_directory: str | Path,
    processed_directory: str | Path,
    manifest_file: str | Path,
    today: date | None = None,
    batch_size: int = 50,
) -> pd.DataFrame:
    """Update and process every security in the supplied registry."""
    validate_universe(universe)

    if len(universe) == 0:
        raise ValueError("Universe must contain at least one security")

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    current_date = today or date.today()
    # Yahoo excludes end_date, so using today keeps an unfinished daily bar out.
    end_date = current_date.isoformat()
    raw_directory_path = Path(raw_directory)
    processed_directory_path = Path(processed_directory)
    manifest_path = Path(manifest_file)
    manifest_rows = []

    download_groups = {}

    for _, security in universe.iterrows():
        raw_file = security_file_path(
            raw_directory_path,
            security["security_id"],
        )
        start_date = download_start_for_security(raw_file)
        download_groups.setdefault(start_date, []).append(security)

    for start_date, securities in download_groups.items():
        for batch_start in range(0, len(securities), batch_size):
            security_batch = securities[batch_start : batch_start + batch_size]
            tickers = [security["ticker"] for security in security_batch]
            downloaded_batch, failed_tickers = download_yfinance_ohlcv(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                batch_size=batch_size,
            )

            for security in security_batch:
                security_id = security["security_id"]
                ticker = security["ticker"]
                raw_file = security_file_path(raw_directory_path, security_id)
                processed_file = security_file_path(
                    processed_directory_path,
                    security_id,
                )
                ticker_download = downloaded_batch[
                    downloaded_batch["ticker"] == ticker
                ].copy()

                if ticker in failed_tickers or len(ticker_download) == 0:
                    manifest_rows.append(
                        {
                            "security_id": security_id,
                            "ticker": ticker,
                            "in_current_universe": bool(
                                security.get("in_current_universe", True)
                            ),
                            "status": "failed",
                            "last_date": None,
                            "updated_at": current_date,
                            "error": "download or validation failed",
                        }
                    )
                    continue

                ticker_download["security_id"] = security_id

                if raw_file.exists():
                    existing_data = load_security_data(raw_file)
                else:
                    existing_data = pd.DataFrame(columns=ticker_download.columns)

                complete_history = merge_security_history(
                    existing_data,
                    ticker_download,
                )
                processed_history = process_security_history(complete_history)

                save_security_data(complete_history, raw_file)
                save_security_data(processed_history, processed_file)

                manifest_rows.append(
                    {
                        "security_id": security_id,
                        "ticker": ticker,
                        "in_current_universe": bool(
                            security.get("in_current_universe", True)
                        ),
                        "status": "success",
                        "last_date": complete_history["date"].max().date(),
                        "updated_at": current_date,
                        "error": None,
                    }
                )

            manifest = pd.DataFrame(manifest_rows)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_manifest_path = manifest_path.with_suffix(".tmp.csv")
            manifest.to_csv(temporary_manifest_path, index=False)
            temporary_manifest_path.replace(manifest_path)

    return pd.DataFrame(manifest_rows)
