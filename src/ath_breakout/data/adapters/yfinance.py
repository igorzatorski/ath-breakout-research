"""Download and normalize daily market data from Yahoo Finance."""

from pathlib import Path

import pandas as pd
import yfinance as yf

from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.validation import REQUIRED_OHLCV_COLUMNS


CANONICAL_COLUMNS = list(REQUIRED_OHLCV_COLUMNS) + [
    "adj_close",
    "dividends",
    "stock_splits",
    "repaired",
    "prices_split_adjusted",
]


def normalize_yfinance_download(
    raw_data: pd.DataFrame,
    tickers: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Convert a multi-ticker Yahoo table to the canonical long format."""
    normalized_tables = []
    failed_tickers = []

    for ticker in tickers:
        if ticker not in raw_data.columns.get_level_values(0):
            failed_tickers.append(ticker)
            continue

        ticker_data = raw_data[ticker].copy()
        ticker_data = ticker_data.dropna(how="all")

        if len(ticker_data) == 0:
            failed_tickers.append(ticker)
            continue

        ticker_data = ticker_data.reset_index()
        ticker_data.columns = [
            str(column).lower().replace(" ", "_").replace("?", "")
            for column in ticker_data.columns
        ]
        ticker_data["security_id"] = ticker
        ticker_data["ticker"] = ticker
        ticker_data["prices_split_adjusted"] = True

        try:
            ticker_data = prepare_ohlcv_data(ticker_data)
        except (KeyError, TypeError, ValueError):
            failed_tickers.append(ticker)
            continue

        ticker_data = ticker_data[CANONICAL_COLUMNS]
        normalized_tables.append(ticker_data)

    if len(normalized_tables) == 0:
        empty_data = pd.DataFrame(columns=CANONICAL_COLUMNS)
        return empty_data, failed_tickers

    normalized_data = pd.concat(normalized_tables, ignore_index=True)
    return normalized_data, failed_tickers


def download_yfinance_ohlcv(
    tickers: list[str],
    start_date: str,
    end_date: str,
    batch_size: int = 50,
    cache_directory: str | Path = "data/cache/yfinance",
) -> tuple[pd.DataFrame, list[str]]:
    """Download tickers in batches and return validated canonical data."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    successful_tables = []
    failed_tickers = []
    cache_path = Path(cache_directory)
    cache_path.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_path))

    for batch_start in range(0, len(tickers), batch_size):
        ticker_batch = tickers[batch_start : batch_start + batch_size]

        try:
            raw_batch = yf.download(
                tickers=ticker_batch,
                start=start_date,
                end=end_date,
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                actions=True,
                repair=True,
                threads=True,
                progress=False,
                multi_level_index=True,
            )
        except Exception:
            failed_tickers.extend(ticker_batch)
            continue

        normalized_batch, missing_tickers = normalize_yfinance_download(
            raw_batch,
            ticker_batch,
        )
        failed_tickers.extend(missing_tickers)

        available_tickers = normalized_batch["ticker"].unique().tolist()

        for ticker in available_tickers:
            ticker_data = normalized_batch[normalized_batch["ticker"] == ticker]

            try:
                prepared_ticker_data = prepare_ohlcv_data(ticker_data)
            except (KeyError, TypeError, ValueError):
                failed_tickers.append(ticker)
                continue

            successful_tables.append(prepared_ticker_data)

    # Batch requests occasionally fail for otherwise valid Yahoo tickers.
    # Retry every failed ticker once on its own before reporting failure.
    retry_tickers = sorted(set(failed_tickers))
    failed_tickers = []

    for ticker in retry_tickers:
        try:
            raw_retry = yf.download(
                tickers=[ticker],
                start=start_date,
                end=end_date,
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                actions=True,
                repair=True,
                threads=False,
                progress=False,
                multi_level_index=True,
            )
            normalized_retry, retry_failures = normalize_yfinance_download(
                raw_retry,
                [ticker],
            )
        except Exception:
            failed_tickers.append(ticker)
            continue

        if ticker in retry_failures or len(normalized_retry) == 0:
            failed_tickers.append(ticker)
            continue

        successful_tables.append(normalized_retry)

    if len(successful_tables) == 0:
        empty_data = pd.DataFrame(columns=CANONICAL_COLUMNS)
        return empty_data, sorted(set(failed_tickers))

    market_data = pd.concat(successful_tables, ignore_index=True)
    market_data = market_data.sort_values(["security_id", "date"])
    market_data = market_data.reset_index(drop=True)
    return market_data, sorted(set(failed_tickers))
