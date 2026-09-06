"""Validate a real ticker change under one stable CRSP PERMNO."""

import argparse
import os
from pathlib import Path

from ath_breakout.data.adapters.crsp_identity import download_crsp_identity_history
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_OUTPUT = Path("data/processed/wrds_samples/meta_ticker_history.parquet")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the FB-to-META ticker change under one CRSP PERMNO."
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

    print("Downloading bounded CRSP identity history...")
    connection = wrds.Connection(**connection_arguments)
    try:
        candidates = connection.raw_sql(
            """
            SELECT permno
            FROM crsp_q_stock.stksecurityinfohist
            WHERE ticker IN ('FB', 'META')
              AND secinfostartdt <= %(end_date)s
              AND secinfoenddt >= %(start_date)s
            GROUP BY permno
            HAVING COUNT(DISTINCT ticker) = 2
            ORDER BY permno
            LIMIT 1
            """,
            params={"start_date": "2022-01-01", "end_date": "2022-12-31"},
        )
        if candidates.empty:
            raise SystemExit("No FB-to-META identity history was found.")
        permno = int(candidates.loc[0, "permno"])
        history = download_crsp_identity_history(
            connection,
            permnos=[permno],
            start_date="2022-01-01",
            end_date="2022-12-31",
        )
    finally:
        connection.close()

    tickers = set(history["ticker"].dropna())
    if not {"FB", "META"}.issubset(tickers):
        raise SystemExit("Expected FB and META identity records were not both returned.")
    if history["security_id"].nunique() != 1:
        raise SystemExit("Ticker history unexpectedly maps to multiple security IDs.")
    if history["effective_from"].duplicated().any():
        raise SystemExit("Identity history contains ambiguous effective dates.")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    history.to_parquet(arguments.output, index=False)
    print(f"Identity intervals validated: {len(history):,}.")
    print("Ticker transition FB to META: found.")
    print("Stable PERMNO across ticker transition: passed.")
    print("Effective interval overlap check: passed.")
    print(f"Local file: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
