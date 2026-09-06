"""Run the portfolio backtest with CRSP point-in-time membership."""

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from ath_breakout.backtesting.crsp_inputs import load_crsp_point_in_time_inputs
from ath_breakout.backtesting.portfolio import run_portfolio_backtest
from ath_breakout.backtesting.reporting import print_portfolio_report
from ath_breakout.backtesting.reporting import save_portfolio_report
from ath_breakout.data.storage import load_security_data


STRATEGY_DIRECTORY = Path("data/processed/crsp/strategy_by_year")
UNIVERSE_FILE = Path("data/processed/crsp/universe_memberships.parquet")
DELISTINGS_FILE = Path("data/raw/crsp/delistings.parquet")
BENCHMARK_FILE = Path("data/processed/features/SPY.parquet")
OUTPUT_ROOT = Path("outputs/backtests/crsp")


def parse_arguments(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--capital", type=float, default=100_000.0)
    parser.add_argument("--max-positions", type=int, default=33)
    parser.add_argument("--position-weight", type=float, default=0.03)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--max-securities", type=int,
                        help="Diagnostic sorted PERMNO subset, NOT a liquidity universe")
    parser.add_argument("--no-open", action="store_true")
    return parser.parse_args(arguments)


def main(arguments=None):
    args = parse_arguments(arguments)
    manifest = json.loads(Path("data/state/crsp_daily_history_manifest.json").read_text())
    if args.start > args.end:
        raise ValueError("Start date must not exceed end date")
    if args.start < date.fromisoformat(manifest["start_date"]) or args.end > date.fromisoformat(manifest["end_date"]):
        raise ValueError(f"Requested backtest is outside CRSP coverage: {manifest['start_date']} to {manifest['end_date']}")
    from scripts.maintenance.validate_data_layer import ensure_ready
    ensure_ready()
    benchmark = load_security_data(BENCHMARK_FILE)
    benchmark_dates = benchmark["date"].astype("datetime64[ns]").dt.date
    if max(benchmark_dates) < args.end:
        from ath_breakout.data.market_calendar import valid_nyse_sessions
        sessions = valid_nyse_sessions(args.start, args.end)
        if len(sessions) and max(benchmark_dates) < sessions[-1].date():
            raise ValueError("SPY benchmark does not cover requested backtest end")
    benchmark_start = min(benchmark_dates)
    effective_start = max(args.start, benchmark_start)
    if effective_start != args.start:
        print(
            f"Requested start {args.start} is before the first SPY date "
            f"{benchmark_start}; using {effective_start}."
        )
    histories, candidates, delistings = load_crsp_point_in_time_inputs(
        STRATEGY_DIRECTORY, UNIVERSE_FILE, effective_start, args.end,
        benchmark_data=benchmark, maximum_securities=args.max_securities,
        delistings_file=DELISTINGS_FILE,
        show_progress=True,
        retain_all_histories=False,
        skip_continuations=True,
    )
    result = run_portfolio_backtest(
        histories, candidates, benchmark, effective_start, args.end,
        initial_capital=args.capital, target_position_weight=args.position_weight,
        maximum_positions=args.max_positions,
        transaction_cost_bps=args.cost_bps,
        delistings=delistings,
        survivorship_warning=(
            "CRSP monthly liquidity snapshots used for point-in-time membership; "
            "validate universe construction and delisting coverage before relying "
            "on full-period performance."
        ),
        return_mode="crsp_total_return",
    )
    result.summary["benchmark_name"] = "S&P 500 (SPY total-return proxy)"
    result.summary["diagnostic_subset"] = args.max_securities
    result.summary["accounting_version"] = 2
    if args.max_securities is not None:
        result.summary["survivorship_warning"] += (
            " DIAGNOSTIC SUBSET: first sorted PERMNOs, not representative performance."
        )
    print_portfolio_report(result.equity, result.trades, result.summary)
    output_directory = OUTPUT_ROOT / f"{effective_start}_{args.end}" / (
        "run_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    files = save_portfolio_report(
        result.equity, result.trades, result.events, candidates,
        result.summary, output_directory, open_dashboard=not args.no_open,
    )
    print(f"Complete results: {output_directory}")
    print(f"Dashboard: {files['dashboard']}")


if __name__ == "__main__":
    main()
