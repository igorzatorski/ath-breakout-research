"""Run the ATH breakout pipeline for a local CSV file."""

from pathlib import Path

from ath_breakout.data.adapters.csv import load_ohlcv_csv
from ath_breakout.strategy.ath import add_breakout_signal, add_prior_ath


INPUT_FILE = Path("examples/data/sample_market.csv")
OUTPUT_FILE = Path("data/processed/example_breakouts.csv")


def main() -> None:
    data = load_ohlcv_csv(INPUT_FILE)
    data_with_ath = add_prior_ath(data)
    result = add_breakout_signal(data_with_ath)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(result)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
