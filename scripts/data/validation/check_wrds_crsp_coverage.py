"""Report CRSP quarterly daily-table coverage without downloading observations."""

import argparse
import os
from datetime import date

import pandas as pd

from ath_breakout.data.crsp_coverage import assess_crsp_coverage
from ath_breakout.data.wrds_credentials import load_wrds_password


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check CRSP daily date coverage.")
    parser.add_argument("--username", default=os.environ.get("WRDS_USERNAME"))
    parser.add_argument("--as-of", default=date.today().isoformat())
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

    print("Checking CRSP quarterly coverage...")
    connection = wrds.Connection(**connection_arguments)
    try:
        coverage = connection.raw_sql(
            """
            SELECT MIN(dlycaldt) AS first_date, MAX(dlycaldt) AS last_date
            FROM crsp_q_stock.dsf_v2
            """,
            date_cols=["first_date", "last_date"],
        )
    finally:
        connection.close()

    if coverage.empty or pd.isna(coverage.loc[0, "last_date"]):
        raise SystemExit("CRSP coverage query returned no date range.")
    first_date = pd.Timestamp(coverage.loc[0, "first_date"]).date()
    last_date = pd.Timestamp(coverage.loc[0, "last_date"]).date()
    assessment = assess_crsp_coverage(first_date, last_date, arguments.as_of)
    print(f"First daily date: {first_date}.")
    print(f"Latest daily date: {last_date}.")
    print(f"Requested date: {assessment.requested_date}.")
    print(f"Calendar days behind: {assessment.calendar_days_behind}.")
    print(f"Suitable for requested-date screener: {'yes' if assessment.is_current else 'no'}.")
    print("Price observations transferred: 0.")


if __name__ == "__main__":
    main()
