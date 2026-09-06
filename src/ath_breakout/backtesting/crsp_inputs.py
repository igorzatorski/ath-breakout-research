"""Prepare point-in-time CRSP inputs for the portfolio simulator."""

from datetime import date
import time
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from ath_breakout.backtesting.portfolio import SIMULATION_COLUMNS
from ath_breakout.screening.features import build_security_snapshot


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}m {seconds % 60:02d}s"


def _progress_line(label: str, completed: int, total: int, started_at: float) -> str:
    width = 28
    fraction = completed / total if total else 1.0
    filled = int(width * fraction)
    elapsed = time.monotonic() - started_at
    eta = elapsed / completed * (total - completed) if completed else 0
    return (
        f"{label:<10} [{('#' * filled + '-' * (width - filled))}] "
        f"{fraction:6.1%} {completed:>{len(str(max(total, 1)))}}/{total} | "
        f"elapsed { _format_duration(elapsed)} | ETA {_format_duration(eta)}"
    )


def _print_progress(line: str) -> None:
    """Rewrite one terminal line and clear leftover characters."""
    print(f"\r\033[K{line}", end="", flush=True)


def _membership_intervals(history: pd.DataFrame) -> pd.DataFrame:
    required = {"permno", "formation_date", "effective_date"}
    missing = sorted(required - set(history.columns))
    if missing:
        raise ValueError(f"Missing universe membership columns: {', '.join(missing)}")
    result = history.copy()
    result["permno"] = pd.to_numeric(result["permno"], errors="raise").astype(int)
    result["formation_date"] = pd.to_datetime(
        result["formation_date"], errors="raise"
    ).dt.normalize()
    result["effective_date"] = pd.to_datetime(
        result["effective_date"], errors="raise"
    ).dt.normalize()
    snapshots = result[["formation_date", "effective_date"]].drop_duplicates()
    if snapshots["formation_date"].duplicated().any():
        raise ValueError("Duplicate CRSP universe formation dates found")
    snapshots = snapshots.sort_values("effective_date").reset_index(drop=True)
    if snapshots["effective_date"].duplicated().any():
        raise ValueError("Duplicate CRSP universe effective dates found")
    next_snapshot = snapshots["effective_date"].shift(-1)
    next_by_effective = dict(zip(snapshots["effective_date"], next_snapshot))
    result["next_effective_date"] = result["effective_date"].map(next_by_effective)
    result = result.sort_values(["permno", "effective_date"])
    if result.duplicated(["permno", "effective_date"]).any():
        raise ValueError("Duplicate CRSP membership effective dates found")
    return result.reset_index(drop=True)


def _active_on_dates(dates: pd.Series, intervals: pd.DataFrame) -> pd.Series:
    if intervals.empty:
        return pd.Series(False, index=dates.index)
    effective = intervals["effective_date"].array
    positions = effective.searchsorted(pd.DatetimeIndex(dates), side="right") - 1
    valid = positions >= 0
    result = pd.Series(False, index=dates.index)
    if valid.any():
        selected = intervals.iloc[positions[valid]]
        current_dates = pd.DatetimeIndex(dates.iloc[valid])
        next_dates = pd.DatetimeIndex(selected["next_effective_date"])
        result.iloc[valid] = next_dates.isna() | (current_dates < next_dates)
    return result


def load_crsp_point_in_time_inputs(
    strategy_directory: str | Path,
    universe_history_file: str | Path,
    start_date: date,
    end_date: date,
    benchmark_data: pd.DataFrame | None = None,
    maximum_securities: int | None = None,
    delistings_file: str | Path = "data/raw/crsp/delistings.parquet",
    show_progress: bool = False,
    retain_all_histories: bool = True,
    skip_continuations: bool = False,
    rank_all_setups: bool = False,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Load CRSP histories and signals using membership effective on each date.

    ``retain_all_histories`` keeps the original loader contract for callers
    that need every selected security.  The production backtest sets it to
    ``False`` so a first pass can identify PIT breakout securities and the
    second pass only materializes those histories.
    """
    if start_date > end_date:
        raise ValueError("start_date must not exceed end_date")
    universe = _membership_intervals(pd.read_parquet(universe_history_file))
    memberships = {
        int(permno): group.reset_index(drop=True)
        for permno, group in universe.groupby("permno", sort=False)
    }
    start_timestamp = pd.Timestamp(start_date).normalize()
    end_timestamp = pd.Timestamp(end_date).normalize()
    overlaps = universe[
        (universe["effective_date"] <= end_timestamp)
        & (
            universe["next_effective_date"].isna()
            | (universe["next_effective_date"] > start_timestamp)
        )
    ]
    selected_permnos = sorted(overlaps["permno"].unique().tolist())
    if maximum_securities is not None:
        if maximum_securities <= 0:
            raise ValueError("maximum_securities must be positive")
        selected_permnos = selected_permnos[:maximum_securities]
    if not selected_permnos:
        return {}, pd.DataFrame(), pd.DataFrame()

    strategy_directory = Path(strategy_directory)
    yearly_files = sorted(strategy_directory.glob("strategy_*.parquet"))
    candidate_permnos = _find_pit_breakout_permnos(
        yearly_files,
        selected_permnos,
        memberships,
        start_timestamp,
        end_timestamp,
        show_progress=show_progress,
    )
    history_permnos = (
        selected_permnos if retain_all_histories or rank_all_setups else sorted(candidate_permnos)
    )
    histories: dict[int, list[pd.DataFrame]] = {
        permno: [] for permno in history_permnos
    }
    prepared_benchmark = None
    if benchmark_data is not None:
        prepared_benchmark = benchmark_data.copy()
        prepared_benchmark["date"] = pd.to_datetime(
            prepared_benchmark["date"]
        ).dt.normalize()
        prepared_benchmark = prepared_benchmark.sort_values("date").reset_index(
            drop=True
        )
    if history_permnos:
        warmup_start = None  # Snapshot scores depend on all prior history.
        required_columns = [
            "security_id", "permno", "ticker", "date", "close", "dividends",
            "split_adj_open", "split_adj_close", "sma_50", "sma_100",
            "sma_150", "sma_200", "volume", "split_adj_high", "split_adj_low",
            "prior_ath", "breakout", "total_return",
        ]
        load_started = time.monotonic()
        if show_progress:
            _print_progress(_progress_line("Loading", 0, len(yearly_files), load_started))
        for file_number, path in enumerate(yearly_files, start=1):
            frame = _read_strategy_partition(
                path,
                required_columns,
                history_permnos,
                start_timestamp=warmup_start,
                end_timestamp=end_timestamp,
            )
            if len(frame):
                for permno, group in frame.groupby("permno", sort=False):
                    if int(permno) in histories:
                        histories[int(permno)].append(group)
            if show_progress:
                _print_progress(_progress_line("Loading", file_number, len(yearly_files), load_started))
        if show_progress:
            print()

    price_history: dict[str, pd.DataFrame] = {}
    candidate_rows = []
    prepare_started = time.monotonic()
    if show_progress:
        _print_progress(_progress_line("Preparing", 0, len(history_permnos), prepare_started))
    for number, permno in enumerate(history_permnos, start=1):
        if not histories[permno]:
            continue
        data = pd.concat(histories[permno], ignore_index=True).sort_values("date")
        if data.duplicated(["permno", "date"]).any():
            raise ValueError("Duplicate CRSP security dates across partitions")
        data = data.reset_index(drop=True)
        membership = memberships[permno]
        data["in_pit_universe"] = _active_on_dates(data["date"], membership).to_numpy()
        simulation_columns = [*SIMULATION_COLUMNS, "total_return", "nominal_close", "nominal_open"]
        simulation_columns = [
            column for column in simulation_columns if column in data.columns
        ]
        simulation = data[
            (data["date"].dt.date >= start_date)
            & (data["date"].dt.date <= end_date)
        ][simulation_columns].copy()
        if len(simulation):
            price_history[str(permno)] = simulation.set_index("date")
        signal_rows = data[
            data["breakout"]
            & data["in_pit_universe"]
            & (data["date"].dt.date >= start_date)
            & (data["date"].dt.date <= end_date)
        ]
        if rank_all_setups:
            signal_rows = data[data["in_pit_universe"] & (data["date"] == end_timestamp)]
        if skip_continuations and not rank_all_setups:
            # Same 20-session cooldown as the snapshot default. Use ALL
            # breakouts, including dates outside PIT membership.
            previous = pd.Series(data.index, index=data.index).where(data["breakout"]).ffill().shift()
            eligible = previous.isna() | ((data.index.to_series() - previous) > 20)
            signal_rows = signal_rows.loc[eligible.loc[signal_rows.index]]
        for row_number in signal_rows.index:
            signal_date = data.loc[row_number, "date"].date()
            snapshot = build_security_snapshot(
                data.loc[:row_number],
                signal_date,
                benchmark_data=prepared_benchmark,
                data_is_prepared=True,
                benchmark_is_prepared=prepared_benchmark is not None,
            )
            if snapshot is not None and (rank_all_setups or snapshot["setup_state"] == "fresh_breakout"):
                candidate_rows.append({
                    **(snapshot if rank_all_setups else {}),
                    "signal_date": pd.Timestamp(signal_date),
                    "security_id": str(permno),
                    "ticker": str(snapshot["ticker"]),
                    "setup_score": float(snapshot["setup_score"]),
                    "breakout_quality_score": float(snapshot["breakout_quality_score"]),
                    "close": float(snapshot["close"]),
                    "prior_ath": float(snapshot["prior_ath"]),
                })
        if show_progress and (number % 100 == 0 or number == len(history_permnos)):
            _print_progress(_progress_line("Preparing", number, len(history_permnos), prepare_started))
    if show_progress:
        print()

    candidates = pd.DataFrame(candidate_rows)
    if len(candidates):
        candidates = candidates.sort_values(
            ["signal_date", "setup_score", "breakout_quality_score"],
            ascending=[True, False, False],
        ).reset_index(drop=True)
    selected_delistings = pd.read_parquet(delistings_file)
    selected_delistings = selected_delistings[
        selected_delistings["permno"].isin(selected_permnos)
    ].copy()
    return price_history, candidates, selected_delistings


def _read_strategy_partition(
    path: Path,
    requested_columns: list[str],
    permnos: list[int],
    start_timestamp: pd.Timestamp | None = None,
    end_timestamp: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Read a narrow strategy partition and apply safe date filtering."""
    available = set(pq.ParquetFile(path).schema.names)
    missing = sorted(
        set(requested_columns) - available - {"total_return"}
    )
    if missing:
        raise ValueError(
            f"CRSP strategy partition {path.name} is missing columns: "
            f"{', '.join(missing)}"
        )
    columns = [column for column in requested_columns if column in available]
    if "close" in columns:
        columns += [c for c in ("nominal_close", "nominal_volume",
                    "price_adjustment_factor", "share_adjustment_factor")
                    if c in available and c not in columns]
    filters = [("permno", "in", permnos)]
    if start_timestamp is not None:
        filters.append(("date", ">=", start_timestamp))
    if end_timestamp is not None:
        filters.append(("date", "<=", end_timestamp))
    table = pq.read_table(
        path,
        filters=filters,
        columns=columns,
    )
    frame = table.to_pandas()
    if "split_adj_open" in frame and "price_adjustment_factor" in frame:
        frame["nominal_open"] = frame["split_adj_open"] * frame["price_adjustment_factor"]
    # Upgrade older local partitions without downloading licensed data again.
    if "nominal_close" not in frame and "price_adjustment_factor" in frame:
        frame["nominal_close"] = frame["close"] * frame["price_adjustment_factor"]
    if "nominal_volume" not in frame and "share_adjustment_factor" in frame:
        frame["nominal_volume"] = frame["volume"] / frame["share_adjustment_factor"]
    if len(frame) == 0:
        return frame
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    if start_timestamp is not None:
        frame = frame[frame["date"] >= start_timestamp]
    if end_timestamp is not None:
        frame = frame[frame["date"] <= end_timestamp]
    return frame


def _find_pit_breakout_permnos(
    yearly_files: list[Path],
    selected_permnos: list[int],
    memberships: dict[int, pd.DataFrame],
    start_timestamp: pd.Timestamp,
    end_timestamp: pd.Timestamp,
    show_progress: bool = False,
) -> set[int]:
    """Find securities with a breakout that was active in the PIT universe."""
    if not yearly_files:
        return set()
    breakout_rows = []
    started_at = time.monotonic()
    if show_progress:
        _print_progress(_progress_line("Scanning", 0, len(yearly_files), started_at))
    for file_number, path in enumerate(yearly_files, start=1):
        frame = _read_strategy_partition(
            path,
            ["permno", "date", "breakout"],
            selected_permnos,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )
        if len(frame):
            frame = frame[frame["breakout"].fillna(False).astype(bool)]
            if len(frame):
                breakout_rows.append(frame[["permno", "date"]])
        if show_progress:
            _print_progress(_progress_line("Scanning", file_number, len(yearly_files), started_at))
    if show_progress:
        print()
    if not breakout_rows:
        return set()
    breakouts = pd.concat(breakout_rows, ignore_index=True)
    result = set()
    for permno, rows in breakouts.groupby("permno", sort=False):
        permno = int(permno)
        membership = memberships[permno]
        if _active_on_dates(rows["date"], membership).any():
            result.add(permno)
    return result
