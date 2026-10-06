"""Refresh CRSP data, rebuild features, and run data-layer quality gates."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from ath_breakout.data.wrds_credentials import load_wrds_password

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data.validation.validate_data_layer import validate  # noqa: E402


def resolve_username(username=None):
    """Use an explicit, environment or locally remembered WRDS username."""
    settings = ROOT / "data/state/wrds_settings.json"
    username = username or os.environ.get("WRDS_USERNAME")
    if not username and settings.exists():
        username = json.loads(settings.read_text()).get("username")
    if not username and sys.stdin.isatty():
        username = input("WRDS username (remembered locally; password stays in credential manager): ").strip()
    if not username:
        raise SystemExit("Provide --username/--wrds-username or set WRDS_USERNAME; use --skip-crsp-check for an explicit local-only run.")
    return username


def refresh_benchmark(end):
    """Extend only SPY when its local coverage does not match the CRSP target."""
    from ath_breakout.data.market_calendar import valid_nyse_sessions
    from ath_breakout.data.market_update import update_market_data
    target = valid_nyse_sessions(pd.Timestamp(end) - pd.Timedelta(days=14), end)[-1].date()
    path = ROOT / "data/processed/features/SPY.parquet"
    if path.exists() and pd.to_datetime(pd.read_parquet(path, columns=["date"]).date).max().date() >= target:
        return
    update_market_data(
        universe=pd.DataFrame({"security_id": ["SPY"], "ticker": ["SPY"]}),
        raw_directory=ROOT / "data/raw/yfinance",
        processed_directory=ROOT / "data/processed/features",
        manifest_file=ROOT / "data/state/crsp_benchmark_manifest.csv",
        download_through=target, retry_failed_now=True,
    )
    if not path.exists() or pd.to_datetime(pd.read_parquet(path, columns=["date"]).date).max().date() < target:
        raise RuntimeError("SPY refresh did not reach the required CRSP benchmark date")


def refresh(username=None, end_date=None):
    """Check WRDS coverage and skip downloads when local data pass validation."""
    username = resolve_username(username)
    import wrds
    kwargs = {"wrds_username": username}
    password = load_wrds_password(username)
    if password is not None:
        kwargs["wrds_password"] = password
    connection = wrds.Connection(**kwargs)
    try:
        available = connection.raw_sql("SELECT MAX(dlycaldt) AS last_date FROM crsp_q_stock.dsf_v2").iloc[0]["last_date"]
        if pd.isna(available):
            raise SystemExit("WRDS returned no available CRSP date.")
        end = pd.Timestamp(available).date()
        if end_date is not None:
            requested = pd.Timestamp(end_date).date()
            if requested > end:
                raise SystemExit(f"Requested end exceeds CRSP coverage: {end}")
            end = requested
    finally:
        connection.close()
    settings = ROOT / "data/state/wrds_settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps({"username": username}), encoding="utf-8")
    manifest_path = ROOT / "data/state/crsp_daily_history_manifest.json"
    local = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    covered = (local.get("status") == "complete" and local.get("end_date", "") >= end.isoformat())
    errors = validate(ROOT) if covered else []
    if covered and not errors:
        refresh_benchmark(end)
        print(f"CRSP available through {pd.Timestamp(available).date()}; local coverage through {local['end_date']}. No download needed.")
        return 0
    print(f"CRSP available through {available}; updating through {end}")
    commands = []
    raw_errors = any("Unreadable partition daily_" in error or "Row count mismatch: daily_" in error for error in errors)
    if not covered or raw_errors:
        commands.extend([
            ["scripts/data/acquisition/build_wrds_crsp_universe_history.py", "--username", username, "--end-date", end.isoformat()],
            ["scripts/data/acquisition/download_wrds_crsp_daily_history.py", "--username", username, "--end-date", end.isoformat()],
        ])
        if raw_errors:
            commands[-1].append("--overwrite")
    else:
        print("Raw coverage is current; repairing local derived artifacts without redownloading CRSP.")
        if not (ROOT / "data/processed/crsp/universe_memberships.parquet").exists():
            commands.append(["scripts/data/acquisition/build_wrds_crsp_universe_history.py", "--username", username, "--end-date", end.isoformat()])
    commands.extend([
        ["scripts/data/acquisition/build_crsp_strategy_history.py"],
        ["scripts/data/validation/audit_crsp_history_quality.py"],
        ["scripts/data/validation/validate_data_layer.py"],
    ])
    for command in commands:
        if command[0] == "scripts/data/validation/validate_data_layer.py":
            refresh_benchmark(end)
        print(f"\n>>> {' '.join(command)}", flush=True)
        subprocess.run([sys.executable, *command], check=True, cwd=ROOT)
    return 0


def main(arguments=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=os.environ.get("WRDS_USERNAME"), required=False)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args(arguments)
    return refresh(args.username, args.end_date)


if __name__ == "__main__":
    raise SystemExit(main())
