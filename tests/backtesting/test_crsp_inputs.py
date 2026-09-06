from datetime import date

import pandas as pd
import pytest

import ath_breakout.backtesting.crsp_inputs as crsp_inputs
from ath_breakout.backtesting.crsp_inputs import load_crsp_point_in_time_inputs


def test_progress_reports_elapsed_eta_and_estimated_total(monkeypatch) -> None:
    monkeypatch.setattr(crsp_inputs.time, "monotonic", lambda: 130.0)

    values = crsp_inputs._progress_values(25, 100, 100.0)

    assert values["elapsed"] == "0m 30s"
    assert values["eta"] == "1m 30s"
    assert values["total"] == "2m 00s"


def test_progress_table_renders_all_stages(capsys, monkeypatch) -> None:
    monkeypatch.setattr(crsp_inputs.time, "monotonic", lambda: 130.0)
    table = crsp_inputs._ProgressTable()

    table.update("Scanning", 25, 100, 100.0)

    output = capsys.readouterr().out
    assert "| Stage" in output
    assert "| Scanning" in output
    assert "| Loading" in output
    assert "| Preparing" in output
    assert "2m 00s" in output


def test_prepared_input_cache_reuses_exact_result(tmp_path, monkeypatch) -> None:
    strategy_directory = tmp_path / "strategy"
    strategy_directory.mkdir()
    _strategy_rows().to_parquet(
        strategy_directory / "strategy_2020.parquet", index=False
    )
    universe_file = tmp_path / "universe.parquet"
    pd.DataFrame(
        {
            "permno": [1, 2],
            "formation_date": ["2018-12-31", "2018-12-31"],
            "effective_date": ["2019-01-01", "2019-01-01"],
        }
    ).to_parquet(universe_file, index=False)
    delistings_file = tmp_path / "delistings.parquet"
    pd.DataFrame({"permno": [], "delisting_return": []}).to_parquet(
        delistings_file, index=False
    )
    monkeypatch.setattr(
        crsp_inputs,
        "build_security_snapshot",
        lambda data, scan_date, benchmark_data=None, **kwargs: {
            "setup_state": "fresh_breakout",
            "ticker": str(data.iloc[-1]["ticker"]),
            "setup_score": 80.0,
            "breakout_quality_score": 70.0,
            "close": float(data.iloc[-1]["close"]),
            "prior_ath": 100.0,
        },
    )
    arguments = (
        strategy_directory, universe_file, date(2020, 1, 1), date(2020, 1, 6)
    )
    options = {
        "delistings_file": delistings_file,
        "cache_directory": tmp_path / "cache",
    }

    first = load_crsp_point_in_time_inputs(*arguments, **options)
    monkeypatch.setattr(
        crsp_inputs,
        "_find_pit_breakout_permnos",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("cache miss")
        ),
    )
    second = load_crsp_point_in_time_inputs(*arguments, **options)

    assert first[0].keys() == second[0].keys()
    for security_id in first[0]:
        pd.testing.assert_frame_equal(first[0][security_id], second[0][security_id])
    pd.testing.assert_frame_equal(first[1], second[1])
    pd.testing.assert_frame_equal(first[2], second[2])


def _strategy_rows() -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=6, freq="D")
    rows = []
    for permno, ticker in [(1, "OLD"), (2, "LIVE")]:
        for number, current_date in enumerate(dates):
            rows.append(
                {
                    "permno": permno,
                    "security_id": str(permno),
                    "ticker": ticker,
                    "date": current_date,
                    "close": 100.0 + number,
                    "dividends": 0.0,
                    "total_return": 0.0,
                    "split_adj_open": 100.0 + number,
                    "split_adj_close": 100.0 + number,
                    "sma_50": 90.0,
                    "sma_100": 90.0,
                    "sma_150": 90.0,
                    "sma_200": 90.0,
                    "volume": 1_000_000.0,
                    "split_adj_high": 101.0 + number,
                    "split_adj_low": 99.0 + number,
                    "prior_ath": 100.0,
                    "breakout": number == 4,
                }
            )
    return pd.DataFrame(rows)


def test_uses_effective_membership_for_historical_candidates(tmp_path, monkeypatch) -> None:
    strategy_directory = tmp_path / "strategy"
    strategy_directory.mkdir()
    _strategy_rows().to_parquet(strategy_directory / "strategy_2020.parquet", index=False)
    universe = pd.DataFrame(
        {
            "permno": [1, 2],
            "formation_date": ["2018-12-31", "2020-01-03"],
            "effective_date": ["2019-01-01", "2020-01-04"],
        }
    )
    universe_file = tmp_path / "universe.parquet"
    universe.to_parquet(universe_file, index=False)
    delistings_file = tmp_path / "delistings.parquet"
    pd.DataFrame(
        {
            "permno": [1],
            "daily_return_date": [pd.Timestamp("2020-01-06")],
            "delisting_return": [-0.5],
        }
    ).to_parquet(delistings_file, index=False)

    monkeypatch.setattr(
        crsp_inputs,
        "build_security_snapshot",
        lambda data, scan_date, benchmark_data=None, **kwargs: {
            "setup_state": "fresh_breakout",
            "ticker": str(data.iloc[-1]["ticker"]),
            "setup_score": 80.0,
            "breakout_quality_score": 70.0,
            "close": float(data.iloc[-1]["close"]),
            "prior_ath": 100.0,
        },
    )

    histories, candidates, selected_delistings = load_crsp_point_in_time_inputs(
        strategy_directory,
        universe_file,
        date(2020, 1, 1),
        date(2020, 1, 6),
        maximum_securities=2,
        delistings_file=delistings_file,
    )

    assert set(histories) == {"1", "2"}
    assert candidates["security_id"].tolist() == ["2"]
    assert selected_delistings["permno"].tolist() == [1]
    assert len(histories["1"]) == 6
    assert "total_return" in histories["1"].columns

    optimized_histories, optimized_candidates, _ = (
        load_crsp_point_in_time_inputs(
            strategy_directory,
            universe_file,
            date(2020, 1, 1),
            date(2020, 1, 6),
            maximum_securities=2,
            delistings_file=delistings_file,
            retain_all_histories=False,
        )
    )
    assert set(optimized_histories) == {"2"}
    assert optimized_candidates["security_id"].tolist() == ["2"]


    _, ranking, _ = load_crsp_point_in_time_inputs(
        strategy_directory, universe_file, date(2020, 1, 6), date(2020, 1, 6),
        delistings_file=delistings_file, rank_all_setups=True,
    )
    assert ranking["security_id"].tolist() == ["2"]
    assert ranking["signal_date"].tolist() == [pd.Timestamp("2020-01-06")]
    assert "setup_state" in ranking


def test_limits_selected_permnos_before_reading_partitions(tmp_path) -> None:
    strategy_directory = tmp_path / "strategy"
    strategy_directory.mkdir()
    _strategy_rows().to_parquet(strategy_directory / "strategy_2020.parquet", index=False)
    universe_file = tmp_path / "universe.parquet"
    pd.DataFrame(
        {
            "permno": [1, 2],
            "formation_date": ["2018-12-31", "2018-12-31"],
            "effective_date": ["2019-01-01", "2019-01-01"],
        }
    ).to_parquet(universe_file, index=False)
    delistings_file = tmp_path / "delistings.parquet"
    pd.DataFrame({"permno": [], "delisting_return": []}).to_parquet(
        delistings_file, index=False
    )

    histories, _, _ = load_crsp_point_in_time_inputs(
        strategy_directory,
        universe_file,
        date(2020, 1, 1),
        date(2020, 1, 6),
        maximum_securities=1,
        delistings_file=delistings_file,
    )

    assert set(histories) == {"1"}


def test_optimized_loader_preserves_long_history_scores(tmp_path):
    from tests.screening.test_features import make_processed_prices
    directory = tmp_path / "strategy"
    directory.mkdir()
    data = make_processed_prices()
    # Extend the prefix far beyond the former 550-day cutoff.
    prefix = pd.concat([data.iloc[:200].copy() for _ in range(3)], ignore_index=True)
    prefix["date"] = pd.bdate_range(end=data.date.min() - pd.Timedelta(days=1), periods=600)
    prefix["breakout"] = False
    for column in ("close", "split_adj_close", "split_adj_high", "split_adj_low"):
        prefix[column] = 50.0
    data = pd.concat([prefix, data], ignore_index=True)
    data["permno"] = 1
    data["security_id"] = "1"
    data.to_parquet(directory / "strategy_2024.parquet", index=False)
    universe = tmp_path / "universe.parquet"
    pd.DataFrame({"permno": [1], "formation_date": ["2010-12-31"],
                  "effective_date": ["2011-01-03"]}).to_parquet(universe)
    delistings = tmp_path / "delistings.parquet"
    pd.DataFrame({"permno": [], "delisting_return": []}).to_parquet(delistings)
    args = (directory, universe, date(2024, 12, 2), date(2024, 12, 3))
    full = load_crsp_point_in_time_inputs(*args, delistings_file=delistings)
    fast = load_crsp_point_in_time_inputs(*args, delistings_file=delistings,
                                          retain_all_histories=False)
    assert len(full[1]) > 0
    pd.testing.assert_frame_equal(full[1], fast[1])
    pd.testing.assert_frame_equal(full[0]["1"], fast[0]["1"])
    # Duplicate observations must not silently alter prices or signal history.
    data.to_parquet(directory / "strategy_duplicate.parquet", index=False)
    with pytest.raises(ValueError, match="Duplicate CRSP"):
        load_crsp_point_in_time_inputs(*args, delistings_file=delistings)
