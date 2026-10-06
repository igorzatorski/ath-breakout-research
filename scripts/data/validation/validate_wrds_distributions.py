"""Validate CRSP return components on bounded real distribution samples."""

import argparse
import os
from pathlib import Path

import pandas as pd

from ath_breakout.data.adapters.crsp import download_crsp_daily
from ath_breakout.data.crsp_adjustments import add_crsp_comparable_values
from ath_breakout.data.crsp_returns import validate_crsp_return_components
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_OUTPUT = Path("data/processed/wrds_samples/distribution_validation.parquet")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ordinary and non-ordinary CRSP distributions."
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

    print("Downloading bounded CRSP distribution samples...")
    connection = wrds.Connection(**connection_arguments)
    try:
        apple = download_crsp_daily(
            connection,
            permnos=[14593],
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
        event = connection.raw_sql(
            """
            SELECT permno, dlycaldt
            FROM crsp_q_stock.dsf_v2
            WHERE dlycaldt BETWEEN %(start_date)s AND %(end_date)s
              AND dlynonorddivamt > 0
              AND dlyret IS NOT NULL
            ORDER BY dlycaldt, permno
            LIMIT 1
            """,
            params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
            date_cols=["dlycaldt"],
        )
        if event.empty:
            raise SystemExit("No bounded non-ordinary distribution sample was found.")
        event_date = pd.Timestamp(event.loc[0, "dlycaldt"])
        nonordinary = download_crsp_daily(
            connection,
            permnos=[int(event.loc[0, "permno"])],
            start_date=event_date.strftime("%Y-%m-%d"),
            end_date=event_date.strftime("%Y-%m-%d"),
        )
    finally:
        connection.close()

    apple_validation = validate_crsp_return_components(apple)
    nonordinary_validation = validate_crsp_return_components(nonordinary)
    if apple_validation.ordinary_distribution_rows == 0:
        raise SystemExit("The Apple sample contains no ordinary dividend event.")
    if nonordinary_validation.nonordinary_distribution_rows != 1:
        raise SystemExit("The selected sample is not a non-ordinary distribution.")

    combined_records = apple.to_dict("records") + nonordinary.to_dict("records")
    combined = pd.DataFrame.from_records(combined_records, columns=apple.columns)
    combined = add_crsp_comparable_values(combined)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(arguments.output, index=False)

    print(f"Apple sessions validated: {len(apple):,}.")
    print(
        "Ordinary dividend events validated: "
        f"{apple_validation.ordinary_distribution_rows:,}."
    )
    print("Non-ordinary distribution events validated: 1.")
    print("No-distribution return equality: passed.")
    print("Total/price/income return identity: passed.")
    print("Distribution impact flags: passed.")
    print("Comparable dividend adjustment: created.")
    print(f"Local file: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
