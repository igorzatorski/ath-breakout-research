"""Point-in-time portfolio simulation for ranked ATH breakout candidates."""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import numpy as np

from ath_breakout.data.storage import load_security_data, security_file_path
from ath_breakout.screening.features import build_security_snapshot
from ath_breakout.data.market_calendar import valid_nyse_sessions


SIMULATION_COLUMNS = [
    "security_id", "ticker", "date", "close", "dividends",
    "split_adj_open", "split_adj_close", "sma_50", "sma_100", "sma_150",
]
RETURN_MODES = {"cash_dividend", "crsp_total_return"}


@dataclass
class PortfolioBacktest:
    """Complete tables produced by the portfolio simulation."""

    equity: pd.DataFrame
    trades: pd.DataFrame
    events: pd.DataFrame
    summary: dict


def prepare_historical_inputs(
    registry_file: str | Path,
    processed_directory: str | Path,
    benchmark_data: pd.DataFrame,
    start_date: date,
    end_date: date,
    minimum_setup_score: float = 0.0,
    show_progress: bool = False,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Load current-universe histories and recreate ranked past signals."""
    registry = pd.read_csv(registry_file)
    registry = registry[registry["in_current_universe"] == True]
    price_history = {}
    candidate_rows = []
    total = len(registry)
    started_at = datetime.now()

    if show_progress:
        _print_preparation_progress(0, total, 0, started_at)

    for completed, (_, security) in enumerate(registry.iterrows(), start=1):
        security_id = str(security["security_id"])
        file_path = security_file_path(processed_directory, security_id)
        if not file_path.exists():
            if show_progress and (completed % 50 == 0 or completed == total):
                _print_preparation_progress(completed, total, len(candidate_rows), started_at)
            continue

        data = load_security_data(file_path)
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date").reset_index(drop=True)
        simulation_data = data[
            (data["date"].dt.date >= start_date)
            & (data["date"].dt.date <= end_date)
        ][SIMULATION_COLUMNS].copy()
        if len(simulation_data) > 0:
            simulation_data["date"] = simulation_data["date"].dt.normalize()
            price_history[security_id] = simulation_data.set_index("date")

        breakout_indices = data.index[
            (data["breakout"] == True)
            & (data["date"].dt.date >= start_date)
            & (data["date"].dt.date <= end_date)
        ]
        for row_number in breakout_indices:
            signal_date = data.loc[row_number, "date"].date()
            snapshot = build_security_snapshot(
                data.iloc[: row_number + 1],
                signal_date,
                benchmark_data=benchmark_data,
            )
            if (
                snapshot is not None
                and snapshot["setup_state"] == "fresh_breakout"
                and float(snapshot["setup_score"]) >= minimum_setup_score
            ):
                candidate_rows.append(
                    {
                        "signal_date": pd.Timestamp(signal_date),
                        "security_id": security_id,
                        "ticker": str(security["ticker"]),
                        "setup_score": float(snapshot["setup_score"]),
                        "breakout_quality_score": float(snapshot["breakout_quality_score"]),
                        "close": float(snapshot["close"]),
                        "prior_ath": float(snapshot["prior_ath"]),
                    }
                )

        if show_progress and (completed % 50 == 0 or completed == total):
            _print_preparation_progress(completed, total, len(candidate_rows), started_at)

    candidates = pd.DataFrame(candidate_rows)
    if len(candidates) > 0:
        candidates = candidates.sort_values(
            ["signal_date", "setup_score", "breakout_quality_score"],
            ascending=[True, False, False],
        ).reset_index(drop=True)
    return price_history, candidates


def run_portfolio_backtest(
    price_history: dict[str, pd.DataFrame],
    candidates: pd.DataFrame,
    benchmark_data: pd.DataFrame,
    start_date: date,
    end_date: date,
    initial_capital: float = 100_000.0,
    target_position_weight: float = 0.03,
    maximum_positions: int = 33,
    transaction_cost_bps: float = 10.0,
    delistings: pd.DataFrame | None = None,
    survivorship_warning: str | None = None,
    return_mode: str = "cash_dividend",
) -> PortfolioBacktest:
    """Simulate ranked next-open entries and moving-average exits."""
    _validate_assumptions(
        initial_capital,
        target_position_weight,
        maximum_positions,
        transaction_cost_bps,
        return_mode,
    )
    benchmark = _benchmark_curve(
        benchmark_data, start_date, end_date, initial_capital
    )
    sessions = valid_nyse_sessions(start_date, end_date).tolist()
    if not sessions:
        raise ValueError("No trading sessions in selected period")
    candidates_by_date = _candidates_by_date(candidates)
    cost_rate = transaction_cost_bps / 10_000
    cash = float(initial_capital)
    positions = {}
    pending_candidates = []
    equity_rows = []
    trades = []
    events = []
    skipped_capacity = 0
    delisting_map = _build_delisting_map(delistings)
    delisting_exits = 0
    use_total_return = return_mode == "crsp_total_return"
    return_fallbacks = 0
    stale_position_sessions = 0

    for session in sessions:
        session = pd.Timestamp(session).normalize()

        if not use_total_return:
            # A dividend belongs to a position held before the ex-date open.
            for security_id, position in list(positions.items()):
                row = _row_on(price_history, security_id, session)
                if row is None:
                    continue
                raw_close = float(row["close"])
                adjusted_close = float(row["split_adj_close"])
                split_factor = adjusted_close / raw_close if raw_close > 0 else 1.0
                dividend_cash = (
                    position["shares"] * float(row["dividends"]) * split_factor
                )
                cash += dividend_cash
                position["dividends_received"] += dividend_cash

        # CRSP supplies a terminal return when a security leaves the database.
        for security_id, position in list(positions.items()):
            outcome = delisting_map.get(security_id)
            if outcome is None or session.date() < outcome["exit_date"]:
                continue
            if pd.isna(outcome["delisting_return"]):
                raise ValueError(f"Missing terminal return for held security {security_id}")
            terminal_price = max(
                0.0,
                position["last_close"]
                * position["return_multiplier"]
                * (1.0 + outcome["delisting_return"]),
            ) * (1 - cost_rate)
            proceeds = position["shares"] * terminal_price
            cash += proceeds
            trades.append(
                {
                    "ticker": position["ticker"], "security_id": security_id,
                    "entry_date": position["entry_date"], "entry_price": position["entry_price"],
                    "exit_date": session, "exit_price": terminal_price,
                    "shares": position["shares"], "holding_sessions": position["holding_sessions"],
                    "exit_sma": position["active_sma"],
                    "dividends_received": position["dividends_received"],
                    "return_pct": (proceeds + position["dividends_received"])
                    / position["invested_value"] - 1,
                    "setup_score": position["setup_score"],
                    "breakout_quality_score": position["breakout_quality_score"],
                    "pnl": proceeds + position["dividends_received"] - position["invested_value"],
                }
            )
            events.append({
                "date": session, "ticker": position["ticker"],
                "event": "delisting_exit", "price": terminal_price,
            })
            del positions[security_id]
            delisting_exits += 1

        # Exit orders created at the previous close execute first.
        for security_id, position in list(positions.items()):
            if not position["pending_exit"]:
                continue
            row = _row_on(price_history, security_id, session)
            if row is None:
                continue
            if use_total_return:
                # Ex-date entitlement survives an exit at the open. Do not
                # use today's close-to-close return for an opening trade.
                dividend = row.get("dividends", 0.0)
                dividend = 0.0 if pd.isna(dividend) else float(dividend)
                dividend_cash = position["shares"] * position["return_multiplier"] * dividend
                cash += dividend_cash
                position["dividends_received"] += dividend_cash
            exit_price = (
                float(row["split_adj_open"])
                * position["return_multiplier"]
                * (1 - cost_rate)
            )
            proceeds = position["shares"] * exit_price
            cash += proceeds
            total_return = (
                proceeds + position["dividends_received"]
            ) / position["invested_value"] - 1
            trades.append(
                {
                    "ticker": position["ticker"],
                    "security_id": security_id,
                    "entry_date": position["entry_date"],
                    "entry_price": position["entry_price"],
                    "exit_date": session,
                    "exit_price": exit_price,
                    "shares": position["shares"],
                    "holding_sessions": position["holding_sessions"],
                    "exit_sma": position["active_sma"],
                    "dividends_received": position["dividends_received"],
                    "return_pct": total_return,
                    "setup_score": position["setup_score"],
                    "breakout_quality_score": position[
                        "breakout_quality_score"
                    ],
                    "pnl": proceeds + position["dividends_received"] - position["invested_value"],
                }
            )
            events.append(
                {"date": session, "ticker": position["ticker"], "event": "exit", "price": exit_price}
            )
            del positions[security_id]

        equity_at_open = cash + sum(
            position["shares"]
            * _mark_price(
                price_history,
                security_id,
                session,
                "split_adj_open",
                position["last_close"],
            )
            * position["return_multiplier"]
            for security_id, position in positions.items()
        )
        target_value = equity_at_open * target_position_weight
        ranked_candidates = sorted(
            pending_candidates,
            key=lambda item: (item["setup_score"], item["breakout_quality_score"]),
            reverse=True,
        )

        for candidate in ranked_candidates:
            security_id = candidate["security_id"]
            if security_id in positions:
                continue
            if len(positions) >= maximum_positions:
                skipped_capacity += 1
                continue
            row = _row_on(price_history, security_id, session)
            if row is None:
                continue
            execution_price = float(row["split_adj_open"]) * (1 + cost_rate)
            allocation = min(target_value, cash)
            nominal_close = row.get("nominal_close", row["close"])
            unit_factor = float(nominal_close) / float(row["split_adj_close"])
            # Round actual shares, then express holdings in adjusted units.
            shares = int(allocation // (execution_price * unit_factor)) * unit_factor
            if shares <= 0:
                continue
            invested_value = shares * execution_price
            cash -= invested_value
            positions[security_id] = {
                "ticker": candidate["ticker"],
                "shares": shares,
                "entry_date": session,
                "entry_price": execution_price,
                "invested_value": invested_value,
                "dividends_received": 0.0,
                "holding_sessions": 0,
                "active_sma": 150,
                "pending_exit": False,
                "last_close": float(row["split_adj_close"]),
                "return_multiplier": 1.0,
                "setup_score": candidate["setup_score"],
                "breakout_quality_score": candidate[
                    "breakout_quality_score"
                ],
            }
            events.append(
                {"date": session, "ticker": candidate["ticker"], "event": "entry", "price": execution_price}
            )

        # Close information is now available: update regimes and create orders.
        for security_id, position in positions.items():
            row = _row_on(price_history, security_id, session)
            if row is None:
                stale_position_sessions += 1
                continue
            close_price = float(row["split_adj_close"])
            if use_total_return and session.date() != position["entry_date"].date():
                if pd.isna(row.get("total_return")):
                    return_fallbacks += 1
                position["return_multiplier"] *= _total_return_factor(
                    row, position["last_close"]
                ) / (close_price / position["last_close"])
            position["last_close"] = close_price
            position["holding_sessions"] += 1
            gain = close_price / position["entry_price"] - 1
            new_sma = position["active_sma"]
            if gain >= 1.0:
                new_sma = 50
            elif gain >= 0.5 and new_sma == 150:
                new_sma = 100
            if new_sma != position["active_sma"]:
                position["active_sma"] = new_sma
                events.append(
                    {"date": session, "ticker": position["ticker"], "event": f"switch_to_sma_{new_sma}", "price": close_price}
                )
            exit_level = row[f"sma_{position['active_sma']}"]
            if pd.notna(exit_level) and close_price < float(exit_level):
                position["pending_exit"] = True

        position_value = sum(
            position["shares"]
            * position["last_close"]
            * position["return_multiplier"]
            for position in positions.values()
        )
        equity_value = cash + position_value
        equity_rows.append(
            {
                "date": session,
                "equity": equity_value,
                "cash": cash,
                "position_value": position_value,
                "exposure": position_value / equity_value if equity_value > 0 else 0.0,
                "open_positions": len(positions),
            }
        )
        pending_candidates = candidates_by_date.get(session, [])

    equity = pd.DataFrame(equity_rows).merge(benchmark, on="date", how="left")
    equity["daily_pnl"] = equity["equity"].diff().fillna(0.0)
    equity["daily_return"] = equity["equity"].pct_change().fillna(0.0)
    equity["equity_peak"] = equity["equity"].cummax()
    equity["drawdown"] = equity["equity"] / equity["equity_peak"] - 1
    equity["benchmark_daily_return"] = (
        equity["benchmark_equity"].pct_change(fill_method=None).fillna(0.0)
    )
    equity["benchmark_peak"] = equity["benchmark_equity"].cummax()
    equity["benchmark_drawdown"] = (
        equity["benchmark_equity"] / equity["benchmark_peak"] - 1
    )
    trades_table = pd.DataFrame(trades)
    events_table = pd.DataFrame(events)
    summary = _build_summary(
        equity,
        trades_table,
        initial_capital,
        maximum_positions,
        target_position_weight,
        transaction_cost_bps,
        len(candidates),
        skipped_capacity,
        len(positions),
        delisting_exits,
        survivorship_warning,
        return_mode,
    )
    summary["return_fallback_sessions"] = return_fallbacks
    summary["stale_position_sessions"] = stale_position_sessions
    return PortfolioBacktest(equity, trades_table, events_table, summary)


def _validate_assumptions(capital, weight, maximum_positions, costs, return_mode) -> None:
    if capital <= 0:
        raise ValueError("initial_capital must be greater than zero")
    if weight <= 0 or weight > 1:
        raise ValueError("target_position_weight must be between zero and one")
    if maximum_positions <= 0:
        raise ValueError("maximum_positions must be greater than zero")
    if costs < 0:
        raise ValueError("transaction_cost_bps cannot be negative")
    if return_mode not in RETURN_MODES:
        allowed = ", ".join(sorted(RETURN_MODES))
        raise ValueError(f"return_mode must be one of: {allowed}")


def _row_on(price_history, security_id, session):
    data = price_history.get(security_id)
    if data is None or session not in data.index:
        return None
    row = data.loc[session]
    return row.iloc[-1] if isinstance(row, pd.DataFrame) else row


def _mark_price(price_history, security_id, session, column, fallback):
    row = _row_on(price_history, security_id, session)
    return float(row[column]) if row is not None else float(fallback)


def _total_return_factor(row: pd.Series, previous_close: float) -> float:
    """Return one day's CRSP total-return factor with a transparent fallback."""
    total_return = row.get("total_return")
    if pd.notna(total_return) and (float(total_return) < -1 or not float(total_return) < float("inf")):
        raise ValueError("Invalid CRSP total return")
    if pd.notna(total_return) and float(total_return) >= -1.0:
        return 1.0 + float(total_return)
    if previous_close <= 0:
        return 1.0
    price_factor = float(row["split_adj_close"]) / previous_close
    dividend = row.get("dividends", 0.0)
    dividend = 0.0 if pd.isna(dividend) else float(dividend)
    return price_factor + dividend / previous_close


def _candidates_by_date(candidates):
    if len(candidates) == 0:
        return {}
    result = {}
    for signal_date, rows in candidates.groupby("signal_date"):
        result[pd.Timestamp(signal_date).normalize()] = rows.to_dict("records")
    return result


def _build_delisting_map(delistings: pd.DataFrame | None) -> dict[str, dict]:
    if delistings is None or len(delistings) == 0:
        return {}
    required = {"permno", "delisting_return"}
    missing = sorted(required - set(delistings.columns))
    if missing:
        raise ValueError(f"Missing delisting columns: {', '.join(missing)}")
    result = {}
    for _, row in delistings.iterrows():
        return_value = row["delisting_return"]
        # Parquet nullable columns yield pd.NA; such metadata rows are not
        # usable outcomes and must not abort a full-universe run.
        if return_value is pd.NA:
            continue
        exit_date = row.get("daily_return_date")
        if pd.isna(exit_date):
            exit_date = row.get("delisting_date")
        if pd.isna(exit_date):
            continue
        result[str(int(row["permno"]))] = {
            "exit_date": pd.Timestamp(exit_date).date(),
            "delisting_return": float(return_value),
        }
    return result


def _benchmark_curve(data, start_date, end_date, capital):
    benchmark = data.copy()
    benchmark["date"] = pd.to_datetime(benchmark["date"]).dt.normalize()
    benchmark = benchmark[
        (benchmark["date"].dt.date >= start_date)
        & (benchmark["date"].dt.date <= end_date)
    ].sort_values("date")
    if len(benchmark) == 0:
        return pd.DataFrame(columns=["date", "benchmark_equity"])
    column = "adj_close" if "adj_close" in benchmark.columns else "split_adj_close"
    benchmark["benchmark_equity"] = benchmark[column] / float(benchmark.iloc[0][column]) * capital
    return benchmark[["date", "benchmark_equity"]].reset_index(drop=True)


def _build_summary(
    equity,
    trades,
    capital,
    max_positions,
    weight,
    costs,
    signals,
    skipped,
    open_count,
    delisting_exits=0,
    survivorship_warning=None,
    return_mode="cash_dividend",
):
    years = max((equity.iloc[-1]["date"] - equity.iloc[0]["date"]).days / 365.25, 0.0)
    final_equity = float(equity.iloc[-1]["equity"])
    benchmark_final = float(equity.iloc[-1]["benchmark_equity"])
    if equity["benchmark_equity"].isna().any():
        benchmark_final = float("nan")
    cagr = (final_equity / capital) ** (1 / years) - 1 if years > 0 else 0.0
    benchmark_cagr = (benchmark_final / capital) ** (1 / years) - 1 if years > 0 else 0.0
    daily_std = float(equity["daily_return"].std())
    benchmark_returns = equity.loc[
        equity["benchmark_equity"].notna(), "benchmark_daily_return"
    ]
    benchmark_std = float(benchmark_returns.std())
    aligned = equity.loc[
        equity["benchmark_equity"].notna(),
        ["daily_return", "benchmark_daily_return"],
    ]
    benchmark_variance = float(aligned["benchmark_daily_return"].var())
    beta = (
        float(aligned.cov().loc["daily_return", "benchmark_daily_return"])
        / benchmark_variance
        if benchmark_variance > 0
        else float("nan")
    )
    alpha = float(
        (aligned["daily_return"] - beta * aligned["benchmark_daily_return"]).mean()
        * 252
    ) if pd.notna(beta) else float("nan")
    alpha_daily, alpha_standard_error, alpha_t_stat = _ols_hac_alpha(
        aligned["daily_return"].to_numpy(dtype=float),
        aligned["benchmark_daily_return"].to_numpy(dtype=float),
    )
    active_returns = aligned["daily_return"] - aligned["benchmark_daily_return"]
    tracking_error_daily = float(active_returns.std())
    downside = equity.loc[equity["daily_return"] < 0, "daily_return"]
    downside_std = float(downside.std())
    maximum_drawdown = float(equity["drawdown"].min())
    average_exposure = float(equity["exposure"].mean())
    wins = float((trades["return_pct"] > 0).mean()) if len(trades) else 0.0
    return {
        "start_date": equity.iloc[0]["date"].date(), "end_date": equity.iloc[-1]["date"].date(),
        "initial_capital": capital, "final_equity": final_equity,
        "total_return_pct": final_equity / capital - 1, "cagr": cagr,
        "annualized_volatility": daily_std * (252 ** 0.5),
        "sharpe_ratio_zero_rate": float(equity["daily_return"].mean() / daily_std * (252 ** 0.5)) if daily_std > 0 else 0.0,
        "sortino_ratio_zero_rate": float(
            equity["daily_return"].mean() / downside_std * (252 ** 0.5)
        ) if downside_std > 0 else 0.0,
        "calmar_ratio": cagr / abs(maximum_drawdown) if maximum_drawdown < 0 else float("nan"),
        "maximum_drawdown": maximum_drawdown,
        "average_exposure": average_exposure,
        "exposure_adjusted_cagr_heuristic": (
            cagr / average_exposure if average_exposure > 0 else float("nan")
        ),
        "maximum_positions_used": int(equity["open_positions"].max()),
        "maximum_positions": max_positions, "target_position_weight": weight,
        "completed_trades": len(trades), "open_positions_at_end": open_count,
        "delisting_exits": delisting_exits,
        "return_mode": return_mode,
        "win_rate": wins,
        "average_trade_return": float(trades["return_pct"].mean()) if len(trades) else 0.0,
        "benchmark_final_equity": benchmark_final,
        "benchmark_total_return_pct": benchmark_final / capital - 1,
        "benchmark_cagr": benchmark_cagr,
        "benchmark_annualized_volatility": benchmark_std * (252 ** 0.5),
        "benchmark_sharpe_ratio_zero_rate": (
            float(benchmark_returns.mean() / benchmark_std * (252 ** 0.5))
            if benchmark_std > 0 else 0.0
        ),
        "benchmark_maximum_drawdown": float(equity["benchmark_drawdown"].min()),
        "benchmark_sortino_ratio_zero_rate": (
            float(benchmark_returns.mean() / benchmark_returns[benchmark_returns < 0].std() * (252 ** 0.5))
            if float(benchmark_returns[benchmark_returns < 0].std()) > 0 else 0.0
        ),
        "benchmark_calmar_ratio": (
            benchmark_cagr / abs(float(equity["benchmark_drawdown"].min()))
            if float(equity["benchmark_drawdown"].min()) < 0 else float("nan")
        ),
        "beta_to_benchmark": beta,
        "annualized_alpha_zero_rate": alpha,
        "annualized_alpha_hac": alpha_daily * 252,
        "annualized_alpha_hac_standard_error": alpha_standard_error * 252,
        "annualized_alpha_hac_ci_lower": (alpha_daily - 1.96 * alpha_standard_error) * 252,
        "annualized_alpha_hac_ci_upper": (alpha_daily + 1.96 * alpha_standard_error) * 252,
        "alpha_hac_t_stat": alpha_t_stat,
        "annualized_tracking_error": tracking_error_daily * (252 ** 0.5),
        "information_ratio": (
            float(active_returns.mean() / tracking_error_daily * (252 ** 0.5))
            if tracking_error_daily > 0 else 0.0
        ),
        "candidate_signals": signals, "signals_skipped_at_capacity": skipped,
        "transaction_cost_bps_per_side": costs,
        "survivorship_warning": survivorship_warning
        or "Current IWV constituents used for all historical dates",
    }


def _ols_hac_alpha(
    strategy_returns: np.ndarray,
    benchmark_returns: np.ndarray,
) -> tuple[float, float, float]:
    """Estimate daily CAPM alpha and a Newey-West standard error."""
    if len(strategy_returns) < 3 or len(strategy_returns) != len(benchmark_returns):
        return float("nan"), float("nan"), float("nan")
    design = np.column_stack([np.ones(len(benchmark_returns)), benchmark_returns])
    inverse = np.linalg.pinv(design.T @ design)
    coefficients = inverse @ design.T @ strategy_returns
    residuals = strategy_returns - design @ coefficients
    scores = design * residuals[:, None]
    covariance_sum = scores.T @ scores
    lag_count = max(1, int(4 * (len(strategy_returns) / 100) ** (2 / 9)))
    for lag in range(1, min(lag_count, len(strategy_returns) - 1) + 1):
        weight = 1.0 - lag / (lag_count + 1.0)
        lag_covariance = scores[lag:].T @ scores[:-lag]
        covariance_sum += weight * (lag_covariance + lag_covariance.T)
    covariance = inverse @ covariance_sum @ inverse
    standard_error = float(np.sqrt(max(covariance[0, 0], 0.0)))
    alpha = float(coefficients[0])
    t_stat = alpha / standard_error if standard_error > 0 else float("nan")
    return alpha, standard_error, t_stat


def _print_preparation_progress(completed, total, signals, started_at):
    width = 30
    filled = int(width * completed / total) if total else width
    bar = "#" * filled + "-" * (width - filled)
    percent = 100 * completed / total if total else 100.0
    count_width = len(str(max(total, 1)))
    elapsed = datetime.now() - started_at
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{bar}] {percent:6.2f}% "
        f"securities {completed:>{count_width}}/{total} | signals: {signals} | elapsed: {elapsed}",
        flush=True,
    )
