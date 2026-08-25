"""Rebuild every processed Parquet from locally stored raw data."""

from datetime import datetime
from pathlib import Path

from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.processing import process_market_data
from ath_breakout.data.storage import load_security_data, save_security_data


RAW_DIRECTORY = Path("data/raw/yfinance")
PROCESSED_DIRECTORY = Path("data/processed/features")


def print_rebuild_progress(
    completed: int,
    total: int,
    successful: int,
    failed: int,
) -> None:
    """Print fixed-width counters for a processed-data rebuild."""
    percentage = 100 * completed / total if total > 0 else 100.0
    count_width = len(str(max(total, 1)))
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"{percentage:6.2f}% "
        f"({completed:>{count_width}}/{total}) | "
        f"success: {successful:>{count_width}} | "
        f"failed: {failed:>{count_width}}",
        flush=True,
    )


def main() -> None:
    started_at = datetime.now()
    raw_files = sorted(RAW_DIRECTORY.glob("*.parquet"))
    successful = 0
    failed = 0

    print(
        f"[{started_at:%Y-%m-%d %H:%M:%S}] "
        f"Rebuilding {len(raw_files)} processed files"
    )

    for file_number, raw_file in enumerate(raw_files, start=1):
        try:
            raw_data = load_security_data(raw_file)
            prepared_data = prepare_ohlcv_data(raw_data)
            processed_data = process_market_data(prepared_data)
            output_file = PROCESSED_DIRECTORY / raw_file.name
            save_security_data(processed_data, output_file)
            successful += 1
        except Exception as error:
            failed += 1
            print(f"  failed {raw_file.stem}: {type(error).__name__}: {error}")

        if file_number % 50 == 0 or file_number == len(raw_files):
            print_rebuild_progress(
                completed=file_number,
                total=len(raw_files),
                successful=successful,
                failed=failed,
            )

    elapsed = datetime.now() - started_at
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"Finished: {successful} successful, {failed} failed | elapsed: {elapsed}"
    )


if __name__ == "__main__":
    main()
