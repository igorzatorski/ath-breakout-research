"""Concise terminal and interactive reports for portfolio backtests."""

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
    """Print compact statistics and diagnostic tables in the terminal."""
    benchmark_label = "S&P 500"
    print("\n" + "=" * 118)
    print("MULTI-ASSET ATH BREAKOUT PORTFOLIO BACKTEST")
    print("=" * 118)
    print(
        f"Period: {summary['start_date']} to {summary['end_date']} | "
        f"max {summary['maximum_positions']} positions | "
        f"target {summary['target_position_weight']:.1%} each | "
        f"cost {summary['transaction_cost_bps_per_side']:.1f} bps per side"
    )
    print(f"Data note: {summary['survivorship_warning']}")

    comparison = [
        ["Initial capital", _money(summary["initial_capital"]), _money(summary["initial_capital"]), "--"],
        ["Final value", _money(summary["final_equity"]), _money(summary["benchmark_final_equity"]), _money(summary["final_equity"] - summary["benchmark_final_equity"])],
        ["Total return", _percent(summary["total_return_pct"]), _percent(summary["benchmark_total_return_pct"]), _percentage_points(summary["total_return_pct"] - summary["benchmark_total_return_pct"])],
        ["CAGR", _percent(summary["cagr"]), _percent(summary["benchmark_cagr"]), _percentage_points(summary["cagr"] - summary["benchmark_cagr"])],
        ["Annual volatility", _percent(summary["annualized_volatility"]), _percent(summary["benchmark_annualized_volatility"]), _percentage_points(summary["annualized_volatility"] - summary["benchmark_annualized_volatility"])],
        ["Sharpe (cash rate 0%)", _number(summary["sharpe_ratio_zero_rate"]), _number(summary["benchmark_sharpe_ratio_zero_rate"]), _signed_number(summary["sharpe_ratio_zero_rate"] - summary["benchmark_sharpe_ratio_zero_rate"])],
        ["Maximum drawdown", _percent(summary["maximum_drawdown"]), _percent(summary["benchmark_maximum_drawdown"]), _percentage_points(summary["maximum_drawdown"] - summary["benchmark_maximum_drawdown"])],
        ["Sortino (cash rate 0%)", _number(summary["sortino_ratio_zero_rate"]), _number(summary["benchmark_sortino_ratio_zero_rate"]), _signed_number(summary["sortino_ratio_zero_rate"] - summary["benchmark_sortino_ratio_zero_rate"])],
        ["Calmar", _number(summary["calmar_ratio"]), _number(summary["benchmark_calmar_ratio"]), _signed_number(summary["calmar_ratio"] - summary["benchmark_calmar_ratio"])],
        ["Average exposure", _percent(summary["average_exposure"]), "100.00%", _percentage_points(summary["average_exposure"] - 1.0)],
    ]
    _heading("STRATEGY VS S&P 500")
    print(
        tabulate(
            comparison,
            headers=["Metric", "Strategy", benchmark_label, "Difference"],
            tablefmt="simple",
        )
    )

    relative = [
        ["Beta to S&P 500", _number(summary["beta_to_benchmark"])],
        ["Annualized CAPM alpha (0% cash)", _percent(summary["annualized_alpha_hac"])],
        ["Alpha 95% HAC confidence interval", f"{_percent(summary['annualized_alpha_hac_ci_lower'])} to {_percent(summary['annualized_alpha_hac_ci_upper'])}"],
        ["Alpha HAC t-statistic", _number(summary["alpha_hac_t_stat"])],
        ["Annualized tracking error", _percent(summary["annualized_tracking_error"])],
        ["Information ratio", _number(summary["information_ratio"])],
        ["CAGR / average exposure*", _percent(summary["exposure_adjusted_cagr_heuristic"])],
    ]
    _heading("RELATIVE PERFORMANCE")
    print(tabulate(relative, headers=["Metric", "Value"], tablefmt="simple"))
    print("* Exposure-adjusted CAGR is a simple diagnostic ratio, not a simulated 100%-invested return.")

    operations = [
        ["Completed trades", summary["completed_trades"], "Open positions at end", summary["open_positions_at_end"]],
        ["Win rate", _percent(summary["win_rate"]), "Average trade", _percent(summary["average_trade_return"])],
        ["Candidate signals", summary["candidate_signals"], "Skipped: portfolio full", summary["signals_skipped_at_capacity"]],
        ["Maximum positions used", f"{summary['maximum_positions_used']}/{summary['maximum_positions']}", "Delisting exits", summary["delisting_exits"]],
        ["Return fallbacks", summary.get("return_fallback_sessions", 0), "Stale position sessions", summary.get("stale_position_sessions", 0)],
    ]
    _heading("PORTFOLIO DIAGNOSTICS")
    print(tabulate(operations, tablefmt="plain"))

    _heading("ANNUAL PERFORMANCE")
    annual = build_annual_performance(equity)
    print(
        tabulate(
            [[int(row.year), _percent(row.strategy_return), _percent(row.benchmark_return), _percent(row.active_return)] for row in annual.itertuples()],
            headers=["Year", "Strategy", benchmark_label, "Active"],
            tablefmt="plain",
        )
    )

    _heading("FIVE WORST AND FIVE BEST DAILY RETURNS")
    extremes = pd.concat(
        [equity.nsmallest(5, "daily_return"), equity.nlargest(5, "daily_return")]
    ).drop_duplicates("date").sort_values("daily_return")
    print(
        tabulate(
            [[pd.Timestamp(row.date).date(), _percent(row.daily_return), _percent(row.benchmark_daily_return), _percent(row.exposure), int(row.open_positions)] for row in extremes.itertuples()],
            headers=["Date", "Strategy return", f"{benchmark_label} return", "Exposure", "Positions"],
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
                [[row.ticker, pd.Timestamp(row.entry_date).date(), pd.Timestamp(row.exit_date).date(), int(row.holding_sessions), f"SMA{int(row.exit_sma)}", _percent(row.return_pct), _money(row.pnl)] for row in latest.itertuples()],
                headers=["Ticker", "Entry", "Exit", "Days", "Exit rule", "Return", "PnL"],
                tablefmt="plain",
            )
        )
    print("=" * 118)


def build_annual_performance(equity: pd.DataFrame) -> pd.DataFrame:
    """Return calendar-year strategy, benchmark, and active returns."""
    data = equity.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["year"] = data["date"].dt.year
    rows = []
    for year, group in data.groupby("year", sort=True):
        strategy_return = (1.0 + group["daily_return"]).prod() - 1.0
        benchmark = group.loc[group["benchmark_equity"].notna(), "benchmark_daily_return"]
        benchmark_return = (1.0 + benchmark).prod() - 1.0 if len(benchmark) else float("nan")
        rows.append(
            {
                "year": int(year),
                "strategy_return": float(strategy_return),
                "benchmark_return": float(benchmark_return),
                "active_return": float(strategy_return - benchmark_return),
            }
        )
    return pd.DataFrame(rows)


def build_monthly_performance(equity: pd.DataFrame) -> pd.DataFrame:
    """Return compounded monthly strategy and benchmark returns."""
    data = equity.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["month"] = data["date"].dt.to_period("M").dt.to_timestamp()
    rows = []
    for month, group in data.groupby("month", sort=True):
        strategy_return = (1.0 + group["daily_return"]).prod() - 1.0
        benchmark = group.loc[
            group["benchmark_equity"].notna(), "benchmark_daily_return"
        ]
        benchmark_return = (
            (1.0 + benchmark).prod() - 1.0 if len(benchmark) else float("nan")
        )
        rows.append(
            {
                "month": month,
                "strategy_return": float(strategy_return),
                "benchmark_return": float(benchmark_return),
            }
        )
    return pd.DataFrame(rows)


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
        "annual": output / "annual_performance.csv",
        "dashboard": output / "interactive_dashboard.html",
    }
    equity.to_csv(files["equity"], index=False)
    trades.to_csv(files["trades"], index=False)
    events.to_csv(files["events"], index=False)
    candidates.to_csv(files["candidates"], index=False)
    pd.DataFrame([summary]).to_csv(files["summary"], index=False)
    annual = build_annual_performance(equity)
    annual.to_csv(files["annual"], index=False)
    monthly = build_monthly_performance(equity)
    _write_interactive_dashboard(
        equity, events, monthly, annual, summary, files["dashboard"]
    )
    if open_dashboard:
        webbrowser.open(files["dashboard"].resolve().as_uri())
    return files


def _write_interactive_dashboard(
    equity, events, monthly, annual, summary, output_file
):
    benchmark = summary.get("benchmark_name", "S&P 500")
    initial = float(summary["initial_capital"])
    strategy_growth = equity["equity"] / initial * 100
    benchmark_growth = equity["benchmark_equity"] / initial * 100
    maximum_growth = max(
        float(strategy_growth.max()), float(benchmark_growth.max())
    )
    minimum_drawdown = min(
        float((equity["drawdown"] * 100).min()),
        float((equity["benchmark_drawdown"] * 100).min()),
    )
    drawdown_floor = int(minimum_drawdown // 5) * 5
    drawdown_ticks = list(range(drawdown_floor, 1, 5))
    growth_tick_candidates = [50, 100, 200, 500, 1_000, 2_000, 5_000, 10_000]
    growth_ticks = [
        value for value in growth_tick_candidates if value <= maximum_growth * 1.15
    ]
    if 100 not in growth_ticks:
        growth_ticks.append(100)
        growth_ticks.sort()
    figure = make_subplots(
        rows=6,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.045,
        row_heights=[0.28, 0.17, 0.13, 0.14, 0.14, 0.14],
        subplot_titles=(
            "Growth of 100 (log scale)",
            "Drawdown comparison",
            "Capital exposure",
            "Rolling 21-session annualized volatility",
            "Monthly returns",
            "Calendar-year returns",
        ),
    )
    figure.add_trace(go.Scatter(x=equity["date"], y=strategy_growth, name="Strategy", line={"width": 2.5, "color": "#2855d9"}), row=1, col=1)
    figure.add_trace(go.Scatter(x=equity["date"], y=benchmark_growth, name=benchmark, line={"width": 2, "color": "#f05a3c"}), row=1, col=1)
    if len(events):
        event_equity = events.merge(equity[["date", "equity"]], on="date", how="left")
        event_equity["growth"] = event_equity["equity"] / initial * 100
        for event_name, color, symbol in (("entry", "#16833b", "triangle-up"), ("exit", "#c42b2b", "triangle-down")):
            selected = event_equity[event_equity["event"] == event_name]
            figure.add_trace(
                go.Scatter(x=selected["date"], y=selected["growth"], mode="markers", name=event_name.title(), marker={"color": color, "symbol": symbol, "size": 6}, text=selected["ticker"], hovertemplate="%{text}<br>%{x}<br>Growth: %{y:.1f}<extra></extra>"),
                row=1,
                col=1,
            )
    figure.add_trace(go.Scatter(
        x=equity["date"], y=equity["drawdown"] * 100,
        name="Strategy drawdown",
        line={"color": "#2855d9", "width": 2.2},
        hovertemplate="Strategy: %{y:.2f}%<extra></extra>",
    ), row=2, col=1)
    figure.add_trace(go.Scatter(
        x=equity["date"], y=equity["benchmark_drawdown"] * 100,
        name=f"{benchmark} drawdown",
        line={"color": "#f05a3c", "width": 1.8},
        hovertemplate=f"{benchmark}: %{{y:.2f}}%<extra></extra>",
    ), row=2, col=1)
    figure.add_trace(go.Scatter(x=equity["date"], y=equity["exposure"] * 100, fill="tozeroy", name="Exposure", line={"color": "#29358f"}), row=3, col=1)
    strategy_volatility = (
        equity["daily_return"].rolling(21, min_periods=10).std()
        * (252 ** 0.5) * 100
    )
    benchmark_volatility = (
        equity["benchmark_daily_return"].rolling(21, min_periods=10).std()
        * (252 ** 0.5) * 100
    )
    figure.add_trace(go.Scatter(x=equity["date"], y=strategy_volatility, name="Strategy 21d volatility", line={"color": "#2855d9", "width": 1.8}), row=4, col=1)
    figure.add_trace(go.Scatter(x=equity["date"], y=benchmark_volatility, name=f"{benchmark} 21d volatility", line={"color": "#f05a3c", "width": 1.5}), row=4, col=1)
    figure.add_trace(go.Bar(x=monthly["month"], y=monthly["strategy_return"] * 100, name="Strategy monthly return", marker_color="#2855d9", opacity=0.85), row=5, col=1)
    figure.add_trace(go.Bar(x=monthly["month"], y=monthly["benchmark_return"] * 100, name=f"{benchmark} monthly return", marker_color="#f05a3c", opacity=0.72), row=5, col=1)
    figure.add_trace(go.Bar(x=annual["year"], y=annual["strategy_return"] * 100, name="Strategy annual return", marker_color="#2855d9"), row=6, col=1)
    figure.add_trace(go.Bar(x=annual["year"], y=annual["benchmark_return"] * 100, name=f"{benchmark} annual return", marker_color="#f05a3c"), row=6, col=1)
    figure.update_layout(
        title={
            "text": f"ATH Breakout Research Report | CAGR {summary['cagr']:.2%} vs {summary['benchmark_cagr']:.2%} | Sharpe {summary['sharpe_ratio_zero_rate']:.2f} vs {summary['benchmark_sharpe_ratio_zero_rate']:.2f} | Beta {summary['beta_to_benchmark']:.2f}",
            "x": 0.02,
            "xanchor": "left",
            "y": 0.985,
            "yanchor": "top",
            "font": {"size": 22},
        },
        height=1580,
        hovermode="x unified",
        template="plotly_white",
        paper_bgcolor="#f7f9fc",
        plot_bgcolor="#ffffff",
        font={"family": "Inter, Segoe UI, Arial", "color": "#17233c", "size": 12},
        legend={
            "orientation": "h",
            "y": -0.055,
            "yanchor": "top",
            "x": 0.0,
            "xanchor": "left",
            "bgcolor": "rgba(255,255,255,0.9)",
        },
        margin={"l": 85, "r": 35, "t": 125, "b": 165},
        barmode="group",
        bargap=0.18,
    )
    figure.update_yaxes(
        title_text="Growth of 100",
        type="log",
        tickmode="array",
        tickvals=growth_ticks,
        ticktext=[f"{value:,}" for value in growth_ticks],
        row=1,
        col=1,
    )
    figure.update_yaxes(
        title_text="%",
        tickmode="array",
        tickvals=drawdown_ticks,
        ticktext=[f"{value}%" for value in drawdown_ticks],
        range=[drawdown_floor, 1],
        showgrid=True,
        gridcolor="#d8deea",
        gridwidth=1,
        row=2,
        col=1,
    )
    figure.update_yaxes(title_text="%", range=[0, 105], row=3, col=1)
    figure.update_yaxes(title_text="%", row=4, col=1)
    figure.update_yaxes(title_text="%", row=5, col=1)
    figure.update_yaxes(title_text="%", row=6, col=1)
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#e7ebf2", zerolinecolor="#aeb8c8")
    figure.write_html(output_file, include_plotlyjs=True, full_html=True)


def _heading(title):
    print("\n" + title)
    print("-" * len(title))


def _money(value):
    return f"${float(value):,.2f}"


def _percent(value):
    return f"{float(value):.2%}"


def _number(value):
    return f"{float(value):.2f}"


def _signed_number(value):
    return f"{float(value):+.2f}"


def _percentage_points(value):
    return f"{float(value) * 100:+.2f} pp"
