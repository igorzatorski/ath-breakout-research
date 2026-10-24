"""Fetch two separate public daily snapshots for the declared SHA comparison."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]


def main():
    yf.set_tz_cache_location(str(ROOT / "outputs/smoothed_heikin_ashi/vendor_cache"))
    for ticker, slug, start in [
        ("QQQ", "QQQ", "1999-03-10"),
        ("BTC-USD", "BTC_USD", "2014-09-01"),
    ]:
        path = ROOT / f"data/raw/yfinance/sha_{slug}_20261005.parquet"
        if path.exists():
            print(f"Using preserved snapshot {path}", flush=True)
            continue
        print(f"Fetching public {ticker} daily history...", flush=True)
        frame = yf.Ticker(ticker).history(
            start=start,
            end="2026-10-06",
            interval="1d",
            auto_adjust=False,
            back_adjust=False,
            actions=True,
            repair=False,
            keepna=True,
            raise_errors=True,
        )
        if frame.empty or not {
            "Open",
            "High",
            "Low",
            "Close",
            "Dividends",
            "Stock Splits",
        }.issubset(frame.columns):
            raise ValueError("Incomplete OHLC/actions response")
        source_timezone = str(frame.index.tz)
        frame = frame.rename_axis("date").reset_index()
        frame.columns = frame.columns.str.lower().str.replace(" ", "_")
        frame["date"] = pd.to_datetime(frame.date).dt.tz_localize(None).dt.normalize()
        frame["ticker"] = ticker
        frame["prices_split_adjusted"] = True
        frame.to_parquet(path, index=False)
        metadata = dict(
            ticker=ticker,
            source="Yahoo Finance via yfinance",
            source_timezone=source_timezone,
            requested_start=start,
            requested_end_exclusive="2026-10-06",
            fetched_utc=datetime.now(timezone.utc).isoformat(),
            rows=len(frame),
            start=str(frame.date.min().date()),
            end=str(frame.date.max().date()),
            auto_adjust=False,
            repair=False,
            actions=True,
            yfinance_version=yf.__version__,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        path.with_suffix(".json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        print(json.dumps(metadata), flush=True)


if __name__ == "__main__":
    main()
