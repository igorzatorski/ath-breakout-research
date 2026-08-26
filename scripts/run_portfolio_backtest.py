"""Run the ranked multi-asset ATH breakout portfolio backtest."""

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from ath_breakout.backtesting.portfolio import prepare_historical_inputs
from ath_breakout.backtesting.portfolio import run_portfolio_backtest
from ath_breakout.backtesting.reporting import print_portfolio_report
from ath_breakout.backtesting.reporting import save_portfolio_report
from ath_breakout.data.storage import load_security_data


REGISTRY_FILE = Path("data/state/security_registry.csv")
PROCESSED_DIRECTORY = Path("data/processed/features")
SPY_FILE = PROCESSED_DIRECTORY / "SPY.parquet"
IWV_FILE = PROCESSED_DIRECTORY / "IWV.parquet"
OUTPUT_ROOT = Path("outputs/backtests/portfolio")


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backtest the ranked 33-position ATH portfolio."
    )
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    parser.add_argument("--capital", type=float, default=100_000.0)
    parser.add_argument("--position-weight", type=float, default=0.03)
    parser.add_argument("--max-positions", type=int, default=33)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument(
        "--min-setup-score",
        type=float,
        default=0.0,
        help="optional minimum 0-100 setup score required for entry",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="save but do not open the interactive HTML dashboard",
    )
    return parser.parse_args(arguments)


def resolve_period(
    spy_data: pd.DataFrame,
    requested_start: date | None,
    requested_end: date | None,
) -> tuple[date, date]:
    """Default to the latest five complete years available in SPY."""
    dates = pd.to_datetime(spy_data["date"])
    end_date = requested_end or dates.max().date()
    start_date = requested_start or (
        pd.Timestamp(end_date) - pd.DateOffset(years=5)
    ).date()
    if start_date >= end_date:
        raise ValueError("start date must be earlier than end date")
    return start_date, end_date


def request_optional_date(prompt: str) -> date | None:
    """Read an optional ISO date, repeating after an invalid value."""
    while True:
        value = input(prompt).strip()
        if value == "":
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD, for example 2017-01-01.")


def request_backtest_period() -> tuple[date | None, date | None]:
    """Ask for a period when Run was clicked without date arguments."""
    print("Choose the portfolio backtest period.")
    start_date = request_optional_date(
        "Start date (YYYY-MM-DD, Enter = latest 5 years): "
    )
    end_date = request_optional_date(
        "End date (YYYY-MM-DD, Enter = latest available session): "
    )
    return start_date, end_date


def main(arguments: list[str] | None = None) -> None:
    args = parse_arguments(arguments)
    if not SPY_FILE.exists() or not IWV_FILE.exists():
        raise FileNotFoundError(
            "SPY or IWV benchmark is missing. Run python scripts/run_data_pipeline.py first."
        )

    spy = load_security_data(SPY_FILE)
    iwv = load_security_data(IWV_FILE)
    requested_start = args.start
    requested_end = args.end
    if arguments is None and args.start is None and args.end is None:
        requested_start, requested_end = request_backtest_period()
    start_date, end_date = resolve_period(
        spy,
        requested_start,
        requested_end,
    )
    started_at = datetime.now()
    print(f"[{started_at:%Y-%m-%d %H:%M:%S}] Starting portfolio backtest")
    print(f"Period: {start_date} to {end_date}")
    print(
        "Warm-up: sessions stored before --start remain available to ATH, "
        "moving averages and ranking features."
    )
    print(
        f"Rules: max {args.max_positions} positions, "
        f"{args.position_weight:.1%} target weight, "
        f"{args.cost_bps:.1f} bps cost per side, "
        f"minimum setup score {args.min_setup_score:.1f}"
    )
    print("Preparing historical point-in-time prices and ranked signals...")

    price_history, candidates = prepare_historical_inputs(
        REGISTRY_FILE,
        PROCESSED_DIRECTORY,
        iwv,
        start_date,
        end_date,
        minimum_setup_score=args.min_setup_score,
        show_progress=True,
    )
    print(
        f"Prepared {len(price_history)} securities and "
        f"{len(candidates)} qualifying signals."
    )
    result = run_portfolio_backtest(
        price_history,
        candidates,
        spy,
        start_date,
        end_date,
        initial_capital=args.capital,
        target_position_weight=args.position_weight,
        maximum_positions=args.max_positions,
        transaction_cost_bps=args.cost_bps,
    )
    print_portfolio_report(result.equity, result.trades, result.summary)

    output_directory = OUTPUT_ROOT / f"{start_date}_{end_date}"
    files = save_portfolio_report(
        result.equity,
        result.trades,
        result.events,
        candidates,
        result.summary,
        output_directory,
        open_dashboard=not args.no_open,
    )
    elapsed = datetime.now() - started_at
    print(f"\nInteractive dashboard: {files['dashboard']}")
    print(f"Complete results: {output_directory}")
    print(f"Finished in: {elapsed}")


if __name__ == "__main__":
    main()
