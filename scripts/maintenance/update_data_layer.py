"""Refresh CRSP data, rebuild features, and run data-layer quality gates."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from ath_breakout.data.wrds_credentials import load_wrds_password

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=os.environ.get("WRDS_USERNAME"), required=False)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()
    if not args.username:
        raise SystemExit("Provide --username or set WRDS_USERNAME.")
    import wrds
    kwargs = {"wrds_username": args.username}
    password = load_wrds_password(args.username)
    if password is not None:
        kwargs["wrds_password"] = password
    connection = wrds.Connection(**kwargs)
    try:
        available = connection.raw_sql("SELECT MAX(dlycaldt) AS last_date FROM crsp_q_stock.dsf_v2").iloc[0]["last_date"]
        if pd.isna(available):
            raise SystemExit("WRDS returned no available CRSP date.")
        end = pd.Timestamp(available).date()
        if args.end_date is not None:
            requested = pd.Timestamp(args.end_date).date()
            if requested > end:
                raise SystemExit(f"Requested end exceeds CRSP coverage: {end}")
            end = requested
        args.end_date = end.isoformat()
    finally:
        connection.close()
    print(f"CRSP available through {available}; updating through {args.end_date}")
    commands = [
        ["scripts/internal/build_wrds_crsp_universe_history.py", "--username", args.username, "--end-date", args.end_date],
        ["scripts/internal/download_wrds_crsp_daily_history.py", "--username", args.username, "--end-date", args.end_date],
        ["scripts/internal/build_crsp_strategy_history.py"],
        ["scripts/internal/audit_crsp_history_quality.py"],
        ["scripts/maintenance/validate_data_layer.py"],
    ]
    for command in commands:
        print(f"\n>>> {' '.join(command)}", flush=True)
        subprocess.run([sys.executable, *command], check=True, cwd=ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
