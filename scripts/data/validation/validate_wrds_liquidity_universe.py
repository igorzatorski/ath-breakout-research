"""Build one lightweight CRSP top-liquidity universe snapshot."""

import argparse
import os
from pathlib import Path

from ath_breakout.data.adapters.crsp_universe import (
    download_crsp_liquidity_universe,
)
from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_OUTPUT = Path("data/processed/wrds_samples/universe_2025-09-30.parquet")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a bounded CRSP liquidity-universe prototype."
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

    print("Building one server-aggregated CRSP liquidity universe...")
    connection = wrds.Connection(**connection_arguments)
    try:
        universe = download_crsp_liquidity_universe(
            connection,
            lookback_start="2025-07-01",
            formation_date="2025-09-30",
            effective_date="2025-10-01",
        )
    finally:
        connection.close()

    if universe.empty:
        raise SystemExit("The bounded universe query returned no securities.")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    universe.to_parquet(arguments.output, index=False)
    print(f"Ranked securities returned: {len(universe):,}.")
    print("Formation date: 2025-09-30.")
    print("Effective date: 2025-10-01.")
    print("Lookback: 2025-07-01 through 2025-09-30.")
    print("Minimum observations: 40; minimum formation price: USD 5.")
    print("Daily rows transferred: 0; aggregation ran inside WRDS.")
    print(f"Local file: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
