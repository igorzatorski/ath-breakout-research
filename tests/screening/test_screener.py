from datetime import date

import pandas as pd

from ath_breakout.data.storage import save_security_data
from ath_breakout.screening.screener import (
    print_screen_progress,
    run_stock_screen,
    save_screen_results,
)
from ath_breakout.screening.features import build_security_snapshot
from tests.screening.test_features import make_processed_prices


def test_scans_only_current_security_with_good_fresh_data(tmp_path) -> None:
    registry_file = tmp_path / "registry.csv"
    quality_file = tmp_path / "quality.csv"
    processed_directory = tmp_path / "processed"

    pd.DataFrame(
        {
            "security_id": ["AAPL", "OLD", "BAD"],
            "ticker": ["AAPL", "OLD", "BAD"],
            "in_current_universe": [True, False, True],
        }
    ).to_csv(registry_file, index=False)
    pd.DataFrame(
        {
            "security_id": ["AAPL", "OLD", "BAD"],
            "quality_status": ["good", "good", "no_data"],
            "last_date": ["2024-12-03", "2024-12-03", None],
        }
    ).to_csv(quality_file, index=False)
    save_security_data(
        make_processed_prices(),
        processed_directory / "AAPL.parquet",
    )

    result, scan_date, summary = run_stock_screen(
        registry_file=registry_file,
        quality_report_file=quality_file,
        processed_directory=processed_directory,
        today=date(2024, 12, 4),
    )

    assert scan_date == date(2024, 12, 3)
    assert result["ticker"].tolist() == ["AAPL"]
    assert summary == {
        "current_universe": 2,
        "usable_quality": 1,
        "scanned": 1,
        "excluded_quality_or_stale": 1,
        "historical_mode": False,
    }


def test_historical_screen_ignores_every_later_session(tmp_path) -> None:
    registry_file = tmp_path / "registry.csv"
    quality_file = tmp_path / "quality.csv"
    processed_directory = tmp_path / "processed"
    full_history = make_processed_prices()
    historical_date = full_history.iloc[-2]["date"].date()

    # Make the following session extreme. It must not affect the earlier view.
    future_index = full_history.index[-1]
    full_history.loc[future_index, "split_adj_close"] *= 10
    full_history.loc[future_index, "split_adj_high"] *= 10
    full_history.loc[future_index, "split_adj_low"] *= 10

    pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
            "in_current_universe": [True],
        }
    ).to_csv(registry_file, index=False)
    pd.DataFrame({"security_id": ["AAPL"]}).to_csv(
        quality_file,
        index=False,
    )
    save_security_data(
        full_history,
        processed_directory / "AAPL.parquet",
    )

    result, scan_date, summary = run_stock_screen(
        registry_file=registry_file,
        quality_report_file=quality_file,
        processed_directory=processed_directory,
        as_of_date=historical_date,
    )

    history_without_future = make_processed_prices().iloc[:-1].copy()
    expected = build_security_snapshot(
        history_without_future,
        historical_date,
    )
    assert expected is not None
    assert scan_date == historical_date
    assert result.iloc[0]["close"] == expected["close"]
    assert result.iloc[0]["prior_ath"] == expected["prior_ath"]
    assert result.iloc[0]["setup_score"] == expected["setup_score"]
    assert result.iloc[0]["date"] == historical_date
    assert summary["historical_mode"] == True


def test_saves_complete_screen_without_temporary_file(tmp_path) -> None:
    output_file = tmp_path / "screen.csv"
    results = pd.DataFrame({"ticker": ["AAPL"], "trend_score": [4]})

    save_screen_results(results, output_file)

    saved_results = pd.read_csv(output_file)
    assert saved_results.to_dict("records") == [
        {"ticker": "AAPL", "trend_score": 4}
    ]
    assert not (tmp_path / "screen.tmp.csv").exists()


def test_returns_empty_screen_when_no_current_security_has_good_data(
    tmp_path,
) -> None:
    registry_file = tmp_path / "registry.csv"
    quality_file = tmp_path / "quality.csv"

    pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
            "in_current_universe": [True],
        }
    ).to_csv(registry_file, index=False)
    pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "quality_status": ["update_failed"],
            "last_date": ["2024-12-02"],
            "expected_latest_date": ["2024-12-03"],
        }
    ).to_csv(quality_file, index=False)

    result, scan_date, summary = run_stock_screen(
        registry_file=registry_file,
        quality_report_file=quality_file,
        processed_directory=tmp_path / "processed",
    )

    assert result.empty
    assert scan_date == date(2024, 12, 3)
    assert summary["current_universe"] == 1
    assert summary["scanned"] == 0
    assert summary["excluded_quality_or_stale"] == 1


def test_prints_screener_progress_bar(capsys) -> None:
    print_screen_progress(completed=25, total=100)

    output = capsys.readouterr().out
    assert "[#######-----------------------]" in output
    assert "25.00%" in output
    assert "scanned  25/100" in output


def test_screener_progress_count_stays_aligned(capsys) -> None:
    print_screen_progress(completed=99, total=2429)
    print_screen_progress(completed=100, total=2429)
    print_screen_progress(completed=1000, total=2429)

    lines = capsys.readouterr().out.splitlines()
    scanned_positions = [line.index("scanned") for line in lines]
    slash_positions = [line.index("/") for line in lines]
    assert len(set(scanned_positions)) == 1
    assert len(set(slash_positions)) == 1
