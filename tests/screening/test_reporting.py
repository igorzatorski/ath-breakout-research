import pandas as pd

from ath_breakout.screening import reporting


def test_base_ready_table_has_a_compact_report_layout(capsys) -> None:
    results = pd.DataFrame(
        {
            "setup_state": ["base_ready"],
            "ticker": ["UNP"],
            "setup_score": [66.9],
            "setup_base_shape_points": [15.0],
            "setup_base_maturity_points": [8.0],
            "setup_trend_points": [17.0],
            "setup_relative_strength_points": [12.0],
            "setup_contraction_points": [9.0],
            "setup_ath_readiness_points": [5.9],
            "close": [309.86],
            "prior_ath": [315.99],
            "ath_distance_pct": [-0.0194],
        }
    )

    reporting.print_base_ready_table(results)

    output = capsys.readouterr().out
    assert "BASE-READY WATCHLIST (TOP 1)" in output
    assert "MARKET LEVELS" in output
    assert "SETUP SCORE BREAKDOWN" in output
    assert "ATH level" in output
    assert "$315.99" in output
    assert "Shape/20" in output
    assert "15.0" in output
    assert "RS/20" in output
    assert "UNP" in output
    assert "Trend > SMA200" not in output


def test_ranking_model_table_explains_all_one_hundred_points(capsys) -> None:
    reporting.print_ranking_model_table()

    output = capsys.readouterr().out
    assert "SETUP RANKING MODEL (100 POINTS)" in output
    assert "Base shape" in output
    assert "Base maturity" in output
    assert "Relative strength" in output
    assert "Breakout quality is separate" in output
