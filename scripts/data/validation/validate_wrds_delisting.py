"""Validate one observed CRSP delisting against its daily return row."""

import argparse
import math
import os
from pathlib import Path

import pandas as pd

from ath_breakout.data.adapters.crsp import download_crsp_daily
from ath_breakout.data.adapters.crsp_delistings import (
    calculate_delisting_terminal_value,
    download_crsp_delistings,
)
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_OUTPUT = Path("data/processed/wrds_samples/delisting_validation.parquet")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate one bounded CRSP delisting outcome."
    )
    parser.add_argument("--username", default=os.environ.get("WRDS_USERNAME"))
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

    connection_arguments = {"wrds_username": username}
    password = load_wrds_password(username)
    if password is not None:
        connection_arguments["wrds_password"] = password

    print("Downloading a bounded CRSP delisting sample...")
    connection = wrds.Connection(**connection_arguments)
    try:
        candidate = connection.raw_sql(
            """
            SELECT permno, delistingdt
            FROM crsp_q_stock.stkdelists
            WHERE delistingdt BETWEEN %(start_date)s AND %(end_date)s
              AND delret IS NOT NULL
              AND deldlydt IS NOT NULL
            ORDER BY delistingdt, permno
            LIMIT 1
            """,
            params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
            date_cols=["delistingdt"],
        )
        if candidate.empty:
            raise SystemExit("No observed delisting return was found in the bounded window.")
        permno = int(candidate.loc[0, "permno"])
        delisting_date = pd.Timestamp(candidate.loc[0, "delistingdt"])
        delistings = download_crsp_delistings(
            connection,
            permnos=[permno],
            start_date=delisting_date.strftime("%Y-%m-%d"),
            end_date=delisting_date.strftime("%Y-%m-%d"),
        )
        daily_date = pd.Timestamp(delistings.loc[0, "daily_return_date"])
        daily = download_crsp_daily(
            connection,
            permnos=[permno],
            start_date=daily_date.strftime("%Y-%m-%d"),
            end_date=daily_date.strftime("%Y-%m-%d"),
        )
    finally:
        connection.close()

    if len(delistings) != 1 or len(daily) != 1:
        raise SystemExit("Expected exactly one delisting and one daily return row.")
    delisting_return = float(delistings.loc[0, "delisting_return"])
    daily_return = float(daily.loc[0, "total_return"])
    if not math.isclose(delisting_return, daily_return, rel_tol=0.0, abs_tol=1e-10):
        raise SystemExit("Delisting return does not match the CRSP daily return row.")
    if str(daily.loc[0, "delisting_flag"]) == "N":
        raise SystemExit("CRSP daily row is not marked as a delisting return.")
    calculate_delisting_terminal_value(100.0, delisting_return)

    output = delistings.copy()
    output["matched_daily_return"] = daily_return
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(arguments.output, index=False)
    print("Observed delisting record validated: 1.")
    print("Daily delisting-return row found: yes.")
    print("Delisting and daily return equality: passed.")
    print("Single terminal-value application: passed.")
    print("Missing-return imputation performed: no.")
    print(f"Local file: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
