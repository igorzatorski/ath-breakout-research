"""Process a local OHLCV CSV into strategy-ready market data."""

from pathlib import Path

from ath_breakout.data.adapters.csv import load_ohlcv_csv
from ath_breakout.data.processing import process_market_data


INPUT_FILE = Path("examples/data/sample_market.csv")
OUTPUT_FILE = Path("data/processed/example_processed.csv")


def main() -> None:
    data = load_ohlcv_csv(INPUT_FILE)
    result = process_market_data(data)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(result)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
