"""The single user-facing entry point for historical CRSP backtests."""

import sys
import json
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.internal.run_crsp_portfolio_backtest import main as run_crsp_backtest  # noqa: E402


def request_date(prompt: str, default: date | None = None) -> date:
    while True:
        value = input(prompt).strip()
        if not value and default is not None:
            return default
        try:
            return date.fromisoformat(value)
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")


def main(arguments=None):
    if arguments:
        return run_crsp_backtest(arguments)
    start = request_date("Start date (YYYY-MM-DD; Enter = 1993-01-29): ", date(1993, 1, 29))
    manifest = json.loads((PROJECT_ROOT / "data/state/crsp_daily_history_manifest.json").read_text())
    last_date = date.fromisoformat(manifest["end_date"])
    end = request_date(f"End date (YYYY-MM-DD; Enter = {last_date}): ", last_date)
    return run_crsp_backtest(["--start", start.isoformat(), "--end", end.isoformat()])


if __name__ == "__main__":
    main(sys.argv[1:])
