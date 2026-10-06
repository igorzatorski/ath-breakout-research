"""Validate CRSP cumulative adjustments around Apple's 2020 split."""

import argparse
import os
from pathlib import Path

from ath_breakout.data.adapters.crsp import download_crsp_daily
from ath_breakout.data.crsp_adjustments import add_crsp_comparable_values
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_OUTPUT = Path("data/processed/wrds_samples/apple_split_2020.parquet")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate CRSP price and share adjustments around Apple's 2020 split."
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("WRDS_USERNAME"),
        help="WRDS username (or set WRDS_USERNAME).",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
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
    connection_arguments = {"wrds_username": username}
    if password is not None:
        connection_arguments["wrds_password"] = password

    print("Downloading the bounded Apple split window from WRDS...")
    connection = wrds.Connection(**connection_arguments)
    try:
        raw_data = download_crsp_daily(
            connection,
            permnos=[14593],
            start_date="2020-08-03",
            end_date="2020-09-30",
        )
    finally:
        connection.close()

    if raw_data.empty:
        raise SystemExit("No Apple rows were returned for the split window.")
    data = add_crsp_comparable_values(raw_data)

    factor_change = data["price_adjustment_factor"].ne(
        data["price_adjustment_factor"].shift(1)
    )
    factor_change.iloc[0] = False
    factor_change_dates = data.loc[factor_change, "date"]
    if factor_change_dates.empty:
        raise SystemExit("No price adjustment-factor transition was found.")
    if not (factor_change_dates.dt.strftime("%Y-%m-%d") == "2020-08-31").any():
        raise SystemExit("The expected 2020-08-31 Apple factor transition was not found.")

    transition_index = factor_change_dates.index[
        factor_change_dates.dt.strftime("%Y-%m-%d") == "2020-08-31"
    ][0]
    previous_index = data.index[data.index.get_loc(transition_index) - 1]
    raw_move = abs(data.loc[transition_index, "close"] / data.loc[previous_index, "close"] - 1)
    comparable_move = abs(
        data.loc[transition_index, "comparable_close"]
        / data.loc[previous_index, "comparable_close"]
        - 1
    )
    if raw_move <= 0.50:
        raise SystemExit("The raw series did not show the expected split discontinuity.")
    if comparable_move >= 0.20:
        raise SystemExit("The comparable series remains discontinuous around the split.")

    ohlc_is_valid = (
        (data["comparable_high"] >= data["comparable_open"])
        & (data["comparable_high"] >= data["comparable_close"])
        & (data["comparable_high"] >= data["comparable_low"])
        & (data["comparable_low"] <= data["comparable_open"])
        & (data["comparable_low"] <= data["comparable_close"])
    )
    if not ohlc_is_valid.all():
        raise SystemExit("Adjusted OHLC relationships are invalid.")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(arguments.output, index=False)
    print(f"Success: validated {len(data):,} Apple sessions around the split.")
    print("Factor transition: 2020-08-31.")
    print("Raw discontinuity detected: yes.")
    print("Comparable-price continuity check: passed.")
    print("Adjusted OHLC consistency check: passed.")
    print(f"Local file: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
