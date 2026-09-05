"""Download a small CRSP Apple sample locally for connection validation."""

import argparse
import os
from pathlib import Path

from ath_breakout.data.adapters.crsp import download_crsp_daily
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_OUTPUT = Path("data/raw/wrds_samples/apple_permno_14593_2025.parquet")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Apple daily CRSP data for 2025 and save it locally."
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("WRDS_USERNAME"),
        help="WRDS username (or set WRDS_USERNAME).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Local Parquet destination.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    username = arguments.username or input("WRDS username: ").strip()
    if not username:
        raise SystemExit("A WRDS username is required.")

    try:
        import wrds
    except ImportError as error:
        raise SystemExit(
            'WRDS support is not installed. Run: python -m pip install -e ".[wrds]"'
        ) from error

    password = load_wrds_password(username)
    if password is None:
        print("No Windows credential found; WRDS will request the password.")

    print("Connecting to WRDS. Approve the Duo Mobile push if prompted...")
    connection_arguments = {"wrds_username": username}
    if password is not None:
        connection_arguments["wrds_password"] = password
    connection = wrds.Connection(**connection_arguments)
    try:
        data = download_crsp_daily(
            connection,
            permnos=[14593],
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
    finally:
        connection.close()

    if data.empty:
        raise SystemExit("The query succeeded but returned no Apple rows for 2025.")
    if data["security_id"].nunique() != 1 or int(data["security_id"].iloc[0]) != 14593:
        raise SystemExit("The result contains an unexpected security identifier.")
    if not data["date"].is_monotonic_increasing:
        raise SystemExit("The returned dates are not chronological.")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(arguments.output, index=False)

    print(f"Success: saved {len(data):,} rows.")
    print(f"Date range: {data['date'].min().date()} to {data['date'].max().date()}.")
    print(f"Columns: {', '.join(data.columns)}.")
    print(f"Local file: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
