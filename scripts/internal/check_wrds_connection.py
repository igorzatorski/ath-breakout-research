"""Verify WRDS PostgreSQL access without downloading licensed CRSP records."""

import argparse
import os

from ath_breakout.data.wrds_credentials import load_wrds_password


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check access to the quarterly CRSP Stock Version 2 table."
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("WRDS_USERNAME"),
        help="WRDS username (or set WRDS_USERNAME).",
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
        table = connection.raw_sql(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = 'crsp_q_stock'
              AND table_name = 'dsf_v2'
            """
        )
    finally:
        connection.close()

    if table.empty:
        raise SystemExit("Connected, but crsp_q_stock.dsf_v2 was not visible.")
    print("Success: crsp_q_stock.dsf_v2 is available.")


if __name__ == "__main__":
    main()
