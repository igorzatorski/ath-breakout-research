import pandas as pd

import pytest

from ath_breakout.data.adapters.yfinance import download_yfinance_ohlcv
from ath_breakout.data.adapters.yfinance import normalize_yfinance_download
from ath_breakout.data.adapters.yfinance import yahoo_session_is_available


def test_detects_whether_yahoo_has_published_requested_session(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "ath_breakout.data.adapters.yfinance.yf.download",
        lambda **kwargs: pd.DataFrame(
            {
                "Open": [100.0],
                "High": [101.0],
                "Low": [99.0],
                "Close": [100.0],
                "Adj Close": [100.0],
                "Volume": [1000.0],
            },
            index=pd.to_datetime(["2026-08-24"]),
        ),
    )

    assert yahoo_session_is_available(pd.Timestamp("2026-08-24").date())
    assert not yahoo_session_is_available(pd.Timestamp("2026-08-25").date())


def test_normalizes_multiple_yahoo_tickers() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    columns = pd.MultiIndex.from_product(
        [
            ["AAPL", "MSFT"],
            ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
        ]
    )
    raw_data = pd.DataFrame(
        [
            [100, 103, 99, 102, 102, 1200000, 200, 204, 198, 203, 203, 900000],
            [102, 105, 101, 104, 104, 1350000, 203, 205, 200, 201, 201, 950000],
        ],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(
        raw_data,
        ["AAPL", "MSFT"],
    )

    assert failed_tickers == []
    assert result["security_id"].tolist() == ["AAPL", "AAPL", "MSFT", "MSFT"]
    assert result["ticker"].tolist() == ["AAPL", "AAPL", "MSFT", "MSFT"]
    assert result["close"].tolist() == [102, 104, 203, 201]
    assert result["adj_close"].tolist() == [102, 104, 203, 201]
    assert result["dividends"].tolist() == [0.0, 0.0, 0.0, 0.0]
    assert result["stock_splits"].tolist() == [0.0, 0.0, 0.0, 0.0]
    assert result["prices_split_adjusted"].tolist() == [True, True, True, True]


def test_preserves_yahoo_corporate_actions() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    columns = pd.MultiIndex.from_product(
        [
            ["AAPL"],
            [
                "Open",
                "High",
                "Low",
                "Close",
                "Adj Close",
                "Volume",
                "Dividends",
                "Stock Splits",
                "Repaired?",
            ],
        ]
    )
    raw_data = pd.DataFrame(
        [
            [100, 103, 99, 102, 101, 1200000, 0.25, 0.0, False],
            [51, 53, 50, 52, 52, 2400000, 0.0, 2.0, True],
        ],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(raw_data, ["AAPL"])

    assert failed_tickers == []
    assert result["adj_close"].tolist() == [101, 52]
    assert result["dividends"].tolist() == [0.25, 0.0]
    assert result["stock_splits"].tolist() == [0.0, 2.0]
    assert result["repaired"].tolist() == [False, True]


def test_reports_missing_yahoo_ticker() -> None:
    dates = pd.to_datetime(["2024-01-02"])
    columns = pd.MultiIndex.from_product(
        [["AAPL"], ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )
    raw_data = pd.DataFrame(
        [[100, 103, 99, 102, 102, 1200000]],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(
        raw_data,
        ["AAPL", "MSFT"],
    )

    assert result["ticker"].tolist() == ["AAPL"]
    assert failed_tickers == ["MSFT"]


def test_one_invalid_ticker_does_not_stop_the_batch() -> None:
    dates = pd.to_datetime(["2024-01-02"])
    columns = pd.MultiIndex.from_product(
        [
            ["AAPL", "BROKEN"],
            ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
        ]
    )
    raw_data = pd.DataFrame(
        [[100, 103, 99, 102, 102, 1200000, 50, 52, 49, 51, None, 500000]],
        index=dates,
        columns=columns,
    )
    raw_data.index.name = "Date"

    result, failed_tickers = normalize_yfinance_download(
        raw_data,
        ["AAPL", "BROKEN"],
    )

    assert result["ticker"].tolist() == ["AAPL"]
    assert failed_tickers == ["BROKEN"]


def test_rejects_non_positive_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be greater than zero"):
        download_yfinance_ohlcv(
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-02-01",
            batch_size=0,
        )


def test_retries_failed_batch_ticker_individually(tmp_path, monkeypatch) -> None:
    dates = pd.to_datetime(["2024-01-02"])
    columns = pd.MultiIndex.from_product(
        [["AAPL"], ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )
    invalid_download = pd.DataFrame(
        [[100, 103, 99, 102, None, 1200000]],
        index=dates,
        columns=columns,
    )
    invalid_download.index.name = "Date"
    valid_download = invalid_download.copy()
    valid_download[("AAPL", "Adj Close")] = 102
    downloads = iter([invalid_download, valid_download])

    monkeypatch.setattr(
        "ath_breakout.data.adapters.yfinance.yf.download",
        lambda **kwargs: next(downloads),
    )

    result, failed_tickers = download_yfinance_ohlcv(
        tickers=["AAPL"],
        start_date="2024-01-01",
        end_date="2024-01-03",
        cache_directory=tmp_path / "cache",
    )

    assert failed_tickers == []
    assert result["ticker"].tolist() == ["AAPL"]


def test_rejects_ticker_when_required_session_is_still_missing(
    tmp_path,
    monkeypatch,
) -> None:
    dates = pd.to_datetime(["2024-01-02"])
    columns = pd.MultiIndex.from_product(
        [["AAPL"], ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )
    stale_download = pd.DataFrame(
        [[100, 103, 99, 102, 102, 1200000]],
        index=dates,
        columns=columns,
    )
    stale_download.index.name = "Date"
    monkeypatch.setattr(
        "ath_breakout.data.adapters.yfinance.yf.download",
        lambda **kwargs: stale_download,
    )

    result, failed_tickers = download_yfinance_ohlcv(
        tickers=["AAPL"],
        start_date="2024-01-01",
        end_date="2024-01-04",
        cache_directory=tmp_path / "cache",
        required_session=pd.Timestamp("2024-01-03").date(),
    )

    assert len(result) == 0
    assert failed_tickers == ["AAPL"]


def yahoo_table(dates):
    return pd.DataFrame(
        {
            "Open": [100.0] * len(dates),
            "High": [101.0] * len(dates),
            "Low": [99.0] * len(dates),
            "Close": [100.0] * len(dates),
            "Adj Close": [100.0] * len(dates),
            "Volume": [1000.0] * len(dates),
        },
        index=pd.to_datetime(dates),
    )


@pytest.mark.parametrize("layout", ["flat", "ticker_first", "price_first"])
def test_response_layouts_and_local_session_dates(layout):
    raw = yahoo_table(["2024-01-02"])
    raw.index = raw.index.tz_localize("America/New_York")
    if layout != "flat":
        raw.columns = pd.MultiIndex.from_tuples(
            [
                ("AAPL", c) if layout == "ticker_first" else (c, "AAPL")
                for c in raw.columns
            ]
        )
    result, failures = normalize_yfinance_download(raw, ["AAPL"])
    assert failures == []
    assert result["date"].tolist() == [pd.Timestamp("2024-01-02")]


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_rejects_non_finite_adjusted_prices(value):
    raw = yahoo_table(["2024-01-02"])
    raw["Adj Close"] = value
    result, failures = normalize_yfinance_download(raw, ["AAPL"])
    assert result.empty and failures == ["AAPL"]


def test_outer_join_padding_with_zero_actions_keeps_valid_history():
    raw = yahoo_table(["2024-01-02", "2024-01-03"])
    raw.iloc[0] = float("nan")
    raw["Dividends"] = 0.0
    raw["Stock Splits"] = 0.0
    raw["Repaired?"] = False
    raw.columns = pd.MultiIndex.from_tuples([("AAPL", c) for c in raw.columns])
    result, failures = normalize_yfinance_download(raw, ["AAPL"])
    assert failures == []
    assert result["date"].tolist() == [pd.Timestamp("2024-01-03")]


def test_later_bar_does_not_replace_missing_required_session(tmp_path, monkeypatch):
    raw = yahoo_table(["2024-01-02", "2024-01-04"])
    monkeypatch.setattr(
        "ath_breakout.data.adapters.yfinance.yf.download", lambda **kwargs: raw
    )
    result, failures = download_yfinance_ohlcv(
        ["AAPL"],
        "2024-01-01",
        "2024-01-05",
        cache_directory=tmp_path,
        required_session=pd.Timestamp("2024-01-03").date(),
    )
    assert result.empty and failures == ["AAPL"]


def test_duplicate_requests_and_outside_dates_are_not_saved(tmp_path, monkeypatch):
    calls = []

    def download(**kwargs):
        calls.append(kwargs)
        return yahoo_table(["2023-12-29", "2024-01-02", "2024-01-03"])

    monkeypatch.setattr("ath_breakout.data.adapters.yfinance.yf.download", download)
    result, failures = download_yfinance_ohlcv(
        ["AAPL", "AAPL"], "2024-01-01", "2024-01-03", cache_directory=tmp_path
    )
    assert failures == []
    assert result["date"].tolist() == [pd.Timestamp("2024-01-02")]
    assert calls[0]["tickers"] == ["AAPL"] and calls[0]["timeout"] == 30


def test_probe_rejects_date_without_valid_prices(monkeypatch):
    monkeypatch.setattr(
        "ath_breakout.data.adapters.yfinance.yf.download",
        lambda **kwargs: pd.DataFrame(index=pd.to_datetime(["2024-01-02"])),
    )
    assert not yahoo_session_is_available(pd.Timestamp("2024-01-02").date())


def test_fresh_cache_is_initialized_before_parallel_requests(tmp_path, monkeypatch):
    from ath_breakout.data.adapters import yfinance as adapter

    calls = []

    def download(**kwargs):
        calls.append(kwargs)
        raw = yahoo_table(["2024-01-02"])
        return pd.concat({ticker: raw for ticker in kwargs["tickers"]}, axis=1)

    monkeypatch.setattr(adapter.yf, "download", download)
    result, failures = adapter.download_yfinance_ohlcv(
        ["AAPL", "MSFT", "SPY"], "2024-01-01", "2024-01-03", cache_directory=tmp_path
    )
    assert failures == [] and len(result) == 3
    assert calls[0]["tickers"] == ["AAPL"] and calls[0]["threads"] is False
    assert calls[1]["tickers"] == ["MSFT", "SPY"] and calls[1]["threads"] is True


def test_repeated_downloads_do_not_reopen_same_cache(tmp_path, monkeypatch):
    from ath_breakout.data.adapters import yfinance as adapter

    paths = []
    monkeypatch.setattr(adapter, "_configured_cache", None)
    monkeypatch.setattr(
        adapter.yf, "set_tz_cache_location", lambda path: paths.append(path)
    )
    adapter.configure_yahoo_cache(tmp_path)
    adapter.configure_yahoo_cache(tmp_path)
    assert paths == [str(tmp_path.resolve())]


def test_only_outside_dates_report_ticker_as_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ath_breakout.data.adapters.yfinance.yf.download",
        lambda **kwargs: yahoo_table(["2023-12-29"]),
    )
    result, failures = download_yfinance_ohlcv(
        ["AAPL"], "2024-01-01", "2024-01-03", cache_directory=tmp_path
    )
    assert result.empty and failures == ["AAPL"]
