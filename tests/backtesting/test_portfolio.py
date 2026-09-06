from datetime import date

import pandas as pd
import pytest

from ath_breakout.backtesting.portfolio import run_portfolio_backtest


DATES = pd.bdate_range("2026-01-02", periods=6)


def make_prices(ticker: str, closes: list[float], sma_50: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "security_id": [ticker] * 6,
            "ticker": [ticker] * 6,
            "date": DATES,
            "close": closes,
            "dividends": [0.0] * 6,
            "split_adj_open": [100.0, 100.0, 120.0, 160.0, 200.0, 140.0],
            "split_adj_close": closes,
            "sma_50": sma_50,
            "sma_100": [70.0] * 6,
            "sma_150": [60.0] * 6,
        }
    ).set_index("date")


def make_inputs():
    histories = {
        "A": make_prices("A", [100, 105, 110, 115, 120, 125], [50] * 6),
        "B": make_prices("B", [100, 120, 160, 210, 150, 140], [50, 50, 50, 50, 180, 180]),
        "C": make_prices("C", [100, 101, 102, 103, 104, 105], [50] * 6),
    }
    candidates = pd.DataFrame(
        [
            {"signal_date": DATES[0], "security_id": "A", "ticker": "A", "setup_score": 80.0, "breakout_quality_score": 60.0},
            {"signal_date": DATES[0], "security_id": "B", "ticker": "B", "setup_score": 90.0, "breakout_quality_score": 60.0},
            {"signal_date": DATES[0], "security_id": "C", "ticker": "C", "setup_score": 70.0, "breakout_quality_score": 60.0},
            {"signal_date": DATES[4], "security_id": "C", "ticker": "C", "setup_score": 75.0, "breakout_quality_score": 60.0},
        ]
    )
    benchmark = pd.DataFrame({"date": DATES, "adj_close": [100, 101, 102, 103, 104, 105]})
    return histories, candidates, benchmark


def test_ranks_next_open_entries_and_respects_capacity() -> None:
    histories, candidates, benchmark = make_inputs()
    result = run_portfolio_backtest(
        histories, candidates, benchmark,
        date(2026, 1, 2), date(2026, 1, 9),
        target_position_weight=0.4, maximum_positions=2,
    )

    entries = result.events[result.events["event"] == "entry"]
    first_entries = entries[entries["date"] == DATES[1]]
    assert first_entries["ticker"].tolist() == ["B", "A"]
    assert result.summary["maximum_positions_used"] == 2
    assert result.summary["signals_skipped_at_capacity"] == 1


def test_switches_sma_permanently_and_sells_on_next_open() -> None:
    histories, candidates, benchmark = make_inputs()
    result = run_portfolio_backtest(
        histories, candidates, benchmark,
        date(2026, 1, 2), date(2026, 1, 9),
        target_position_weight=0.4, maximum_positions=2,
    )

    b_events = result.events[result.events["ticker"] == "B"]
    assert b_events["event"].tolist() == [
        "entry", "switch_to_sma_100", "switch_to_sma_50", "exit"
    ]
    assert b_events.iloc[-1]["date"] == DATES[5]
    assert result.trades.iloc[0]["exit_sma"] == 50


def test_executes_new_ranked_entry_after_an_exit_frees_a_slot() -> None:
    histories, candidates, benchmark = make_inputs()
    result = run_portfolio_backtest(
        histories, candidates, benchmark,
        date(2026, 1, 2), date(2026, 1, 9),
        target_position_weight=0.4, maximum_positions=2,
    )

    final_day_events = result.events[result.events["date"] == DATES[5]]
    assert final_day_events["event"].tolist() == ["exit", "entry"]
    assert final_day_events.iloc[1]["ticker"] == "C"
    assert result.summary["open_positions_at_end"] == 2


def test_tracks_equity_exposure_drawdown_and_benchmark() -> None:
    histories, candidates, benchmark = make_inputs()
    result = run_portfolio_backtest(
        histories, candidates, benchmark,
        date(2026, 1, 2), date(2026, 1, 9),
        target_position_weight=0.4, maximum_positions=2,
    )

    assert result.equity["exposure"].between(0, 1).all()
    assert result.equity["drawdown"].min() < 0
    assert result.summary["benchmark_total_return_pct"] == pytest.approx(0.05)


def test_closes_position_using_crsp_delisting_return() -> None:
    histories, candidates, benchmark = make_inputs()
    histories["1"] = histories.pop("A")
    candidates = candidates.copy()
    candidates.loc[candidates["security_id"] == "A", "security_id"] = "1"
    delistings = pd.DataFrame(
        {
            "permno": [1],
            "daily_return_date": [DATES[3]],
            "delisting_return": [-0.5],
        }
    )

    result = run_portfolio_backtest(
        histories,
        candidates,
        benchmark,
        date(2026, 1, 2),
        date(2026, 1, 9),
        target_position_weight=0.4,
        maximum_positions=3,
        delistings=delistings,
    )

    events = result.events[result.events["ticker"] == "A"]
    assert "delisting_exit" in events["event"].tolist()
    assert result.summary["delisting_exits"] == 1
    assert result.trades.iloc[0]["exit_date"] == DATES[3]


def test_crsp_total_return_reinvests_distribution_in_position_value() -> None:
    history = pd.DataFrame(
        {
            "security_id": ["1"] * len(DATES),
            "ticker": ["TEST"] * len(DATES),
            "date": DATES,
            "close": [100.0] * len(DATES),
            "dividends": [0.0] * len(DATES),
            "total_return": [0.0, 0.0, 0.10, 0.0, 0.0, 0.0],
            "split_adj_open": [100.0] * len(DATES),
            "split_adj_close": [100.0] * len(DATES),
            "sma_50": [50.0] * len(DATES),
            "sma_100": [40.0] * len(DATES),
            "sma_150": [30.0] * len(DATES),
        }
    ).set_index("date")
    histories = {"1": history}
    candidates = pd.DataFrame(
        [
            {
                "signal_date": DATES[0],
                "security_id": "1",
                "ticker": "TEST",
                "setup_score": 80.0,
                "breakout_quality_score": 70.0,
            }
        ]
    )
    benchmark = pd.DataFrame({"date": DATES, "adj_close": [100.0] * len(DATES)})

    result = run_portfolio_backtest(
        histories,
        candidates,
        benchmark,
        date(2026, 1, 2),
        date(2026, 1, 9),
        target_position_weight=1.0,
        maximum_positions=1,
        transaction_cost_bps=0.0,
        return_mode="crsp_total_return",
    )

    assert result.summary["return_mode"] == "crsp_total_return"
    assert result.equity.iloc[-1]["equity"] == pytest.approx(110_000.0)
