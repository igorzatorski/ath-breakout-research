"""Terminal and interactive reports for the multi-asset backtest."""

from pathlib import Path
import webbrowser

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tabulate import tabulate


def print_portfolio_report(
    equity: pd.DataFrame,
    trades: pd.DataFrame,
    summary: dict,
) -> None:
    """Print charts, statistics, exposure, and trades in the terminal."""
    print("\n" + "=" * 118)
    print("MULTI-ASSET ATH BREAKOUT PORTFOLIO BACKTEST")
    print("=" * 118)
    print(
        f"Period: {summary['start_date']} to {summary['end_date']} | "
        f"max {summary['maximum_positions']} positions | "
        f"target {summary['target_position_weight']:.1%} each | "
        f"cost {summary['transaction_cost_bps_per_side']:.1f} bps per side"
    )
    print(f"WARNING: {summary['survivorship_warning']}")
    benchmark_name = summary.get("benchmark_name", "S&P 500")

    _heading(f"EQUITY CURVE: STRATEGY (S) VS {benchmark_name} (B)")
    print(
        _two_series_chart(
            equity["equity"], equity["benchmark_equity"],
            width=92, height=16,
        )
    )
    print(
        f"S = ${summary['final_equity']:,.0f} | "
        f"B = ${summary['benchmark_final_equity']:,.0f} | "
        "X = overlap"
    )

    _heading("DRAWDOWN CURVE")
    print(_single_series_chart(equity["drawdown"] * 100, width=92, height=12, symbol="#"))
    print(f"Worst drawdown: {summary['maximum_drawdown']:.2%}")

    _heading("CAPITAL EXPOSURE")
    print(_single_series_chart(equity["exposure"] * 100, width=92, height=10, symbol="@"))
    print(
        f"Average invested: {summary['average_exposure']:.2%} | "
        f"Maximum simultaneous positions: {summary['maximum_positions_used']}/"
        f"{summary['maximum_positions']}"
    )

    statistics = [
        ["Initial capital", _money(summary["initial_capital"]), "Final equity", _money(summary["final_equity"])],
        ["Total return", _percent(summary["total_return_pct"]), f"{benchmark_name} return", _percent(summary["benchmark_total_return_pct"])],
        ["CAGR", _percent(summary["cagr"]), f"{benchmark_name} CAGR", _percent(summary["benchmark_cagr"])],
        ["Annual volatility", _percent(summary["annualized_volatility"]), "Sharpe (cash rate 0%)", f"{summary['sharpe_ratio_zero_rate']:.2f}"],
        ["Maximum drawdown", _percent(summary["maximum_drawdown"]), "Average exposure", _percent(summary["average_exposure"])],
        ["Completed trades", summary["completed_trades"], "Open positions at end", summary["open_positions_at_end"]],
        ["Win rate", _percent(summary["win_rate"]), "Average trade", _percent(summary["average_trade_return"])],
        ["Candidate signals", summary["candidate_signals"], "Skipped: portfolio full", summary["signals_skipped_at_capacity"]],
    ]
    _heading("PERFORMANCE STATISTICS")
    print(tabulate(statistics, tablefmt="plain"))

    _heading("FIVE WORST AND FIVE BEST DAILY PNL SESSIONS")
    extremes = pd.concat(
        [equity.nsmallest(5, "daily_pnl"), equity.nlargest(5, "daily_pnl")]
    ).drop_duplicates("date").sort_values("daily_pnl")
    print(
        tabulate(
            [
                [
                    pd.Timestamp(row["date"]).date(), _money(row["daily_pnl"]),
                    _percent(row["daily_return"]), _percent(row["exposure"]),
                    int(row["open_positions"]),
                ]
                for _, row in extremes.iterrows()
            ],
            headers=["Date", "Daily PnL", "Return", "Exposure", "Positions"],
            tablefmt="plain",
        )
    )

    _heading("LATEST COMPLETED TRADES")
    if len(trades) == 0:
        print("No completed trades.")
    else:
        latest = trades.sort_values("exit_date").tail(20)
        print(
            tabulate(
                [
                    [
                        row["ticker"], pd.Timestamp(row["entry_date"]).date(),
                        pd.Timestamp(row["exit_date"]).date(), int(row["holding_sessions"]),
                        f"SMA{int(row['exit_sma'])}", _percent(row["return_pct"]),
                        _money(row["pnl"]),
                    ]
                    for _, row in latest.iterrows()
                ],
                headers=["Ticker", "Entry", "Exit", "Days", "Exit rule", "Return", "PnL"],
                tablefmt="plain",
            )
        )
    print("=" * 118)


def save_portfolio_report(
    equity: pd.DataFrame,
    trades: pd.DataFrame,
    events: pd.DataFrame,
    candidates: pd.DataFrame,
    summary: dict,
    output_directory: str | Path,
    open_dashboard: bool = True,
) -> dict[str, Path]:
    """Save result tables and an interactive Plotly dashboard."""
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "equity": output / "equity_curve.csv",
        "trades": output / "trades.csv",
        "events": output / "events.csv",
        "candidates": output / "ranked_candidates.csv",
        "summary": output / "summary.csv",
        "dashboard": output / "interactive_dashboard.html",
    }
    equity.to_csv(files["equity"], index=False)
    trades.to_csv(files["trades"], index=False)
    events.to_csv(files["events"], index=False)
    candidates.to_csv(files["candidates"], index=False)
    pd.DataFrame([summary]).to_csv(files["summary"], index=False)
    _write_interactive_dashboard(equity, events, summary, files["dashboard"])
    if open_dashboard:
        webbrowser.open(files["dashboard"].resolve().as_uri())
    return files


def _write_interactive_dashboard(equity, events, summary, output_file):
    figure = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=[0.42, 0.20, 0.18, 0.20],
        subplot_titles=("Equity curve", "Drawdown", "Capital exposure", "Daily PnL"),
    )
    figure.add_trace(go.Scatter(x=equity["date"], y=equity["equity"], name="Strategy", line={"width": 2.5}), row=1, col=1)
    benchmark_name = summary.get("benchmark_name", "S&P 500")
    figure.add_trace(go.Scatter(x=equity["date"], y=equity["benchmark_equity"], name=benchmark_name, line={"width": 2}), row=1, col=1)
    if len(events) > 0:
        event_equity = events.merge(equity[["date", "equity"]], on="date", how="left")
        for event_name, color, symbol in [("entry", "green", "triangle-up"), ("exit", "red", "triangle-down")]:
            selected = event_equity[event_equity["event"] == event_name]
            figure.add_trace(
                go.Scatter(
                    x=selected["date"], y=selected["equity"], mode="markers",
                    name=event_name.title(), marker={"color": color, "symbol": symbol, "size": 8},
                    text=selected["ticker"], hovertemplate="%{text}<br>%{x}<br>Equity: %{y:$,.0f}<extra></extra>",
                ), row=1, col=1,
            )
    figure.add_trace(go.Scatter(x=equity["date"], y=equity["drawdown"] * 100, fill="tozeroy", name="Drawdown", line={"color": "firebrick"}), row=2, col=1)
    figure.add_trace(go.Scatter(x=equity["date"], y=equity["exposure"] * 100, fill="tozeroy", name="Exposure", line={"color": "navy"}), row=3, col=1)
    colors = ["seagreen" if value >= 0 else "firebrick" for value in equity["daily_pnl"]]
    figure.add_trace(go.Bar(x=equity["date"], y=equity["daily_pnl"], marker_color=colors, name="Daily PnL"), row=4, col=1)
    figure.update_layout(
        title=(
            "ATH Breakout Portfolio | "
            f"CAGR {summary['cagr']:.2%} | Max DD {summary['maximum_drawdown']:.2%} | "
            f"Sharpe {summary['sharpe_ratio_zero_rate']:.2f}"
        ),
        height=1050, hovermode="x unified", template="plotly_white",
        legend={"orientation": "h", "y": 1.03},
    )
    figure.update_yaxes(title_text="Portfolio value", row=1, col=1)
    figure.update_yaxes(title_text="%", row=2, col=1)
    figure.update_yaxes(title_text="%", row=3, col=1)
    figure.update_yaxes(title_text="PnL", row=4, col=1)
    figure.write_html(output_file, include_plotlyjs=True, full_html=True)


def _two_series_chart(first, second, width, height):
    first_values = _sample(first, width)
    second_values = _sample(second, width)
    valid = [v for v in first_values + second_values if pd.notna(v)]
    minimum, maximum = min(valid), max(valid)
    grid = [[" " for _ in range(width)] for _ in range(height)]
    for symbol, values in [("S", first_values), ("B", second_values)]:
        for x, value in enumerate(values):
            if pd.isna(value):
                continue
            y = _row_for_value(value, minimum, maximum, height)
            grid[y][x] = "X" if grid[y][x] != " " else symbol
    lines = []
    for row_number, row in enumerate(grid):
        level = maximum - row_number / max(height - 1, 1) * (maximum - minimum)
        lines.append(f"{level:>12,.0f} |{''.join(row)}|")
    return "\n".join(lines)


def _single_series_chart(values, width, height, symbol):
    sampled = _sample(values, width)
    minimum, maximum = min(sampled), max(sampled)
    grid = [[" " for _ in range(width)] for _ in range(height)]
    for x, value in enumerate(sampled):
        y = _row_for_value(value, minimum, maximum, height)
        grid[y][x] = symbol
    lines = []
    for row_number, row in enumerate(grid):
        level = maximum - row_number / max(height - 1, 1) * (maximum - minimum)
        lines.append(f"{level:>8.1f}% |{''.join(row)}|")
    return "\n".join(lines)


def _sample(values, width):
    numeric = pd.to_numeric(values, errors="coerce")
    if len(numeric) == 0:
        return [0.0] * width
    indices = [int(i * (len(numeric) - 1) / max(width - 1, 1)) for i in range(width)]
    return [float(numeric.iloc[index]) for index in indices]


def _row_for_value(value, minimum, maximum, height):
    if maximum <= minimum:
        return height - 1
    normalized = (value - minimum) / (maximum - minimum)
    return height - 1 - min(int(normalized * (height - 1)), height - 1)


def _heading(title):
    print("\n" + title)
    print("-" * len(title))


def _money(value):
    return f"${float(value):,.2f}"


def _percent(value):
    return f"{float(value):.2%}"
