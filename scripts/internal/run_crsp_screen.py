"""Rank the historical point-in-time CRSP universe at one close."""
from pathlib import Path
from ath_breakout.backtesting.crsp_inputs import load_crsp_point_in_time_inputs
from ath_breakout.data.storage import load_security_data
from ath_breakout.screening.reporting import print_candidate_tables


def main(scan_date):
    from scripts.maintenance.validate_data_layer import ensure_ready
    ensure_ready()
    _, results, _ = load_crsp_point_in_time_inputs(
        Path("data/processed/crsp/strategy_by_year"),
        Path("data/processed/crsp/universe_memberships.parquet"),
        scan_date, scan_date,
        benchmark_data=load_security_data(Path("data/processed/features/SPY.parquet")),
        rank_all_setups=True, show_progress=True,
    )
    print(f"CRSP point-in-time ranking at {scan_date}; relative strength benchmark: SPY")
    output = Path("outputs/screening/crsp") / f"screener_{scan_date}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    if len(results):
        print_candidate_tables(results)
    else:
        print("No usable snapshots for this session.")
    print(f"Complete table: {output}")
