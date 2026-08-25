"""Render compact terminal reports for current and historical screens."""

import pandas as pd
from tabulate import tabulate


TERMINAL_BASE_ROWS = 10
TERMINAL_TABLE_WIDTH = 88


def print_table_heading(title: str) -> None:
    """Separate terminal report sections without drawing a data grid."""
    print(f"\n{'=' * TERMINAL_TABLE_WIDTH}")
    print(title)
    print("=" * TERMINAL_TABLE_WIDTH)


def print_ranking_model_table() -> None:
    """Explain the setup-score categories before printing candidates."""
    print_table_heading("SETUP RANKING MODEL (100 POINTS)")
    rows = [
        ["Base shape", "20", "depth, rising lows, price-line consistency"],
        ["Base maturity", "10", "consolidation duration"],
        ["Trend", "20", "SMA structure and SMA200 slope"],
        ["Relative strength", "20", "return vs IWV over 3, 6 and 12 months"],
        ["Contraction", "15", "ATR and price-range contraction"],
        ["ATH readiness", "15", "distance from the prior ATH"],
    ]
    print(
        tabulate(
            rows,
            headers=["Category", "Weight", "What enters the score"],
            tablefmt="plain",
            disable_numparse=True,
        )
    )
    print(
        "Breakout quality is separate: volume confirmation (40), "
        "close quality (35), extension above ATH (25)."
    )


def _score_rows(candidates: pd.DataFrame) -> list[list[str]]:
    """Return formatted setup-component rows shared by both reports."""
    rows = []
    for _, row in candidates.iterrows():
        rows.append(
            [
                row["ticker"],
                f'{row["setup_base_shape_points"]:.1f}',
                f'{row["setup_base_maturity_points"]:.1f}',
                f'{row["setup_trend_points"]:.1f}',
                f'{row["setup_relative_strength_points"]:.1f}',
                f'{row["setup_contraction_points"]:.1f}',
                f'{row["setup_ath_readiness_points"]:.1f}',
            ]
        )
    return rows


def _print_score_breakdown(candidates: pd.DataFrame) -> None:
    """Print the six setup-score components for selected candidates."""
    print("\nSETUP SCORE BREAKDOWN")
    print(
        tabulate(
            _score_rows(candidates),
            headers=[
                "Ticker",
                "Shape/20",
                "Maturity/10",
                "Trend/20",
                "RS/20",
                "Contraction/15",
                "ATH/15",
            ],
            tablefmt="plain",
            disable_numparse=True,
        )
    )


def print_fresh_breakout_table(results: pd.DataFrame) -> None:
    """Print market levels and setup scores for qualified breakouts."""
    breakouts = results[results["setup_state"] == "fresh_breakout"]
    print_table_heading(f"FRESH BREAKOUTS ({len(breakouts)})")

    if len(breakouts) == 0:
        print("No qualified fresh breakouts.")
        return

    market_rows = []
    for number, (_, row) in enumerate(breakouts.iterrows(), start=1):
        market_rows.append(
            [
                number,
                row["ticker"],
                f'{row["setup_score"]:.1f}',
                f'{row["breakout_quality_score"]:.1f}',
                f'${row["close"]:,.2f}',
                f'${row["prior_ath"]:,.2f}',
                f'{row["ath_distance_pct"]:+.2%}',
            ]
        )

    print("\nMARKET LEVELS")
    print(
        tabulate(
            market_rows,
            headers=[
                "#",
                "Ticker",
                "Setup score",
                "Breakout Q",
                "Close",
                "ATH level",
                "Vs ATH",
            ],
            tablefmt="plain",
            disable_numparse=True,
        )
    )
    _print_score_breakdown(breakouts)


def print_base_ready_table(results: pd.DataFrame) -> None:
    """Print market levels and scores for the best watchlist bases."""
    bases = results[results["setup_state"] == "base_ready"].head(
        TERMINAL_BASE_ROWS
    )
    print_table_heading(f"BASE-READY WATCHLIST (TOP {len(bases)})")

    if len(bases) == 0:
        print("No qualified base-ready candidates.")
        return

    market_rows = []
    for number, (_, row) in enumerate(bases.iterrows(), start=1):
        market_rows.append(
            [
                number,
                row["ticker"],
                f'{row["setup_score"]:.1f}',
                f'${row["close"]:,.2f}',
                f'${row["prior_ath"]:,.2f}',
                f'{row["ath_distance_pct"]:+.2%}',
            ]
        )

    print("\nMARKET LEVELS")
    print(
        tabulate(
            market_rows,
            headers=[
                "#",
                "Ticker",
                "Setup score",
                "Close",
                "ATH level",
                "Vs ATH",
            ],
            tablefmt="plain",
            disable_numparse=True,
        )
    )
    _print_score_breakdown(bases)
    print("Vs ATH = distance from the previous all-time high")


def print_candidate_tables(results: pd.DataFrame) -> None:
    """Print the shared ranking explanation and candidate tables."""
    print_ranking_model_table()
    print_fresh_breakout_table(results)
    print_base_ready_table(results)
