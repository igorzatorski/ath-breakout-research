"""Download and normalize daily market data from Yahoo Finance."""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
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

_configured_cache = None
_warmed_caches = set()


def configure_yahoo_cache(directory):
    """Avoid repeatedly reopening SQLite caches between download batches."""
    global _configured_cache
    path = Path(directory).resolve()
    path.mkdir(parents=True, exist_ok=True)
    if path != _configured_cache:
        yf.set_tz_cache_location(str(path))
        _configured_cache = path
    return path


def yahoo_session_is_available(
    session: date,
    ticker: str = "SPY",
) -> bool:
    """Return whether Yahoo already publishes a daily row for one session."""
    cache_path = configure_yahoo_cache("data/cache/yfinance")
    end_date = session + timedelta(days=1)
    try:
        data = yf.download(
            tickers=[ticker],
            start=session.isoformat(),
            end=end_date.isoformat(),
            interval="1d",
            auto_adjust=False,
            actions=False,
            repair=True,
            threads=False,
            progress=False,
            multi_level_index=True,
            timeout=30,
        )
    except Exception:
        return False

    if data is None or len(data) == 0:
        return False

    try:
        normalized, failed = normalize_yfinance_download(data, [ticker])
    except (TypeError, ValueError):
        return False
    if not failed:
        _warmed_caches.add(cache_path)
    return not failed and session in set(normalized["date"].dt.date)


def normalize_yfinance_download(
    raw_data: pd.DataFrame,
    tickers: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Convert a multi-ticker Yahoo table to the canonical long format."""
    normalized_tables = []
    failed_tickers = []
    if raw_data is None or not isinstance(raw_data, pd.DataFrame) or raw_data.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS), list(dict.fromkeys(tickers))

    for ticker in dict.fromkeys(tickers):
        if isinstance(raw_data.columns, pd.MultiIndex):
            level = next(
                (
                    index
                    for index in range(raw_data.columns.nlevels)
                    if ticker.upper()
                    in {
                        str(value).upper()
                        for value in raw_data.columns.get_level_values(index)
                    }
                ),
                None,
            )
            if level is None:
                failed_tickers.append(ticker)
                continue
            symbol = next(
                value
                for value in raw_data.columns.get_level_values(level)
                if str(value).upper() == ticker.upper()
            )
            ticker_data = raw_data.xs(symbol, axis=1, level=level).copy()
        elif len(set(tickers)) == 1:
            ticker_data = raw_data.copy()
        else:
            failed_tickers.append(ticker)
            continue
        ticker_data.columns = [
            str(column).lower().replace(" ", "_").replace("?", "")
            for column in ticker_data.columns
        ]
        # A multi-ticker outer join adds empty rows outside a ticker's own history.
        prices = [
            name
            for name in ("open", "high", "low", "close", "volume")
            if name in ticker_data
        ]
        actions = [
            name for name in ("dividends", "stock_splits") if name in ticker_data
        ]
        if prices:
            empty_prices = ticker_data[prices].isna().all(axis=1)
            has_action = (
                ticker_data[actions].fillna(0).ne(0).any(axis=1)
                if actions
                else pd.Series(False, index=ticker_data.index)
            )
            ticker_data = ticker_data.loc[~(empty_prices & ~has_action)]

        if len(ticker_data) == 0:
            failed_tickers.append(ticker)
            continue

        ticker_data.index = pd.DatetimeIndex(pd.to_datetime(ticker_data.index))
        if ticker_data.index.tz is not None:
            ticker_data.index = ticker_data.index.tz_localize(None)
        ticker_data.index.name = "date"
        ticker_data = ticker_data.reset_index()
        ticker_data.columns = [
            str(column).lower().replace(" ", "_").replace("?", "")
            for column in ticker_data.columns
        ]
        ticker_data["security_id"] = ticker
        ticker_data["ticker"] = ticker
        ticker_data["prices_split_adjusted"] = True

        try:
            numeric = [
                name
                for name in (
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "adj_close",
                    "dividends",
                    "stock_splits",
                )
                if name in ticker_data
            ]
            if not np.isfinite(ticker_data[numeric].to_numpy(dtype=float)).all():
                raise ValueError("Yahoo returned non-finite prices, volume or actions")
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
    required_session: date | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Download tickers in batches and return validated canonical data."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if start >= end:
        raise ValueError("start_date must precede exclusive end_date")
    if (
        required_session is not None
        and not start.date() <= required_session < end.date()
    ):
        raise ValueError("required_session must be inside the requested date range")
    tickers = list(dict.fromkeys(tickers))

    successful_tables = []
    failed_tickers = []
    cache_path = configure_yahoo_cache(cache_directory)
    # Initialize Yahoo's SQLite/cookie caches serially before worker threads.
    # This is a normal request, not a discarded warm-up download.
    batches = []
    remaining = tickers
    if tickers and cache_path not in _warmed_caches:
        batches.append(tickers[:1])
        remaining = tickers[1:]
    batches.extend(
        remaining[index : index + batch_size]
        for index in range(0, len(remaining), batch_size)
    )

    for ticker_batch in batches:
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
                threads=cache_path in _warmed_caches and len(ticker_batch) > 1,
                progress=False,
                multi_level_index=True,
                timeout=30,
            )
        except Exception:
            failed_tickers.extend(ticker_batch)
            continue
        if raw_batch is not None and not raw_batch.empty:
            _warmed_caches.add(cache_path)

        normalized_batch, missing_tickers = normalize_yfinance_download(
            raw_batch,
            ticker_batch,
        )
        normalized_batch = normalized_batch.loc[
            (normalized_batch["date"] >= start) & (normalized_batch["date"] < end)
        ]
        available_after_bounds = set(normalized_batch["ticker"])
        missing_tickers.extend(
            ticker for ticker in ticker_batch if ticker not in available_after_bounds
        )
        if required_session is not None and len(normalized_batch) > 0:
            present = set(
                normalized_batch.loc[
                    normalized_batch["date"].dt.date == required_session, "ticker"
                ]
            )
            stale_tickers = [ticker for ticker in ticker_batch if ticker not in present]
            missing_tickers.extend(stale_tickers)
            normalized_batch = normalized_batch[
                ~normalized_batch["ticker"].isin(stale_tickers)
            ]
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
                timeout=30,
            )
            normalized_retry, retry_failures = normalize_yfinance_download(
                raw_retry,
                [ticker],
            )
            normalized_retry = normalized_retry.loc[
                (normalized_retry["date"] >= start) & (normalized_retry["date"] < end)
            ]
        except Exception:
            failed_tickers.append(ticker)
            continue

        if ticker in retry_failures or len(normalized_retry) == 0:
            failed_tickers.append(ticker)
            continue

        if required_session is not None and required_session not in set(
            normalized_retry["date"].dt.date
        ):
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
