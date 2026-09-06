"""List point-in-time CRSP breakouts and next-session entry prices in a date range."""

import sys
import json
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ath_breakout.backtesting.crsp_inputs import load_crsp_point_in_time_inputs  # noqa: E402
from ath_breakout.data.storage import load_security_data  # noqa: E402
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from scripts.maintenance.validate_data_layer import ensure_ready  # noqa: E402


STRATEGY_DIRECTORY = Path("data/processed/crsp/strategy_by_year")
UNIVERSE_FILE = Path("data/processed/crsp/universe_memberships.parquet")
DELISTINGS_FILE = Path("data/raw/crsp/delistings.parquet")
BENCHMARK_FILE = Path("data/processed/features/SPY.parquet")
OUTPUT_DIRECTORY = Path("outputs/screening/periods")


def request_date(prompt: str) -> date:
    while True:
        try:
            return date.fromisoformat(input(prompt).strip())
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")


def main(arguments=None) -> None:
    if arguments and len(arguments) == 2:
        start, end = map(date.fromisoformat, arguments)
    else:
        start = request_date("Start date (YYYY-MM-DD): ")
        end = request_date("End date (YYYY-MM-DD): ")
    if start > end:
        raise SystemExit("Start date must not be later than end date.")
    manifest = json.loads(Path("data/state/crsp_daily_history_manifest.json").read_text())
    available_end = date.fromisoformat(manifest["end_date"])
    if start < date.fromisoformat(manifest["start_date"]) or end > available_end:
        raise SystemExit(f"Requested period is outside CRSP coverage: {manifest['start_date']} to {available_end}. No complete screen can be produced.")
    ensure_ready()
    sessions = valid_nyse_sessions(end, pd.Timestamp(end) + pd.Timedelta(days=14))
    next_sessions = sessions[sessions > pd.Timestamp(end)]
    load_end = min(next_sessions[0].date(), available_end)
    benchmark = load_security_data(BENCHMARK_FILE)
    histories, candidates, _ = load_crsp_point_in_time_inputs(
        STRATEGY_DIRECTORY, UNIVERSE_FILE, start, load_end,
        benchmark_data=benchmark, delistings_file=DELISTINGS_FILE,
        show_progress=True, retain_all_histories=False, skip_continuations=True,
    )
    rows = []
    for candidate in candidates.to_dict("records"):
        if pd.Timestamp(candidate["signal_date"]).date() > end:
            continue
        history = histories.get(str(candidate["security_id"]))
        signal = pd.Timestamp(candidate["signal_date"])
        sessions = valid_nyse_sessions(signal, signal + pd.Timedelta(days=14))
        entry_date = sessions[sessions > signal][0]
        entry_row = history.loc[entry_date] if history is not None and entry_date in history.index else None
        rows.append({
            **candidate,
            "entry_date": entry_date,
            "entry_price": float(entry_row["nominal_open"]) if entry_row is not None else float("nan"),
            "entry_status": "available" if entry_row is not None else "unavailable",
        })
    result = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["signal_date", "security_id", "ticker", "close", "entry_date", "entry_price", "entry_status", "setup_score", "breakout_quality_score"])
    if len(result):
        result = result.sort_values(["signal_date", "setup_score"], ascending=[True, False])
    output = OUTPUT_DIRECTORY / f"{start}_{end}" / "breakouts.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(f"\nPERIOD BREAKOUT SCREENER | {start} to {end}")
    print("=" * 72)
    if len(result):
        display = result[
            [
                "signal_date", "ticker", "close", "entry_date", "entry_price",
                "entry_status", "setup_score", "breakout_quality_score",
            ]
        ].copy()
        for column in ("signal_date", "entry_date"):
            display[column] = pd.to_datetime(display[column]).dt.strftime("%Y-%m-%d")
        for column in ("close", "entry_price"):
            display[column] = display[column].map(lambda value: f"{value:,.2f}")
        for column in ("setup_score", "breakout_quality_score"):
            display[column] = display[column].map(lambda value: f"{value:,.1f}")
        print(display.to_markdown(index=False))
    else:
        print("No fresh breakouts found in this period.")
    print(f"\nFound {len(result)} fresh breakouts.")
    print(f"Results: {output}")


if __name__ == "__main__":
    main(sys.argv[1:])
