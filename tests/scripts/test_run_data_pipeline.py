from datetime import date
from pathlib import Path
import sys

import pandas as pd
import pytest

from scripts import run_data_pipeline


def test_waits_until_yahoo_exposes_target_session(monkeypatch, capsys) -> None:
    availability = iter([False, True])
    monkeypatch.setattr(
        run_data_pipeline,
        "yahoo_session_is_available",
        lambda session: next(availability),
    )
    monkeypatch.setattr(run_data_pipeline.time, "sleep", lambda seconds: None)

    run_data_pipeline.wait_for_yahoo_session(
        date(2026, 8, 24),
        max_wait_minutes=60,
        poll_seconds=120,
    )

    output = capsys.readouterr().out
    assert "Yahoo is not ready yet" in output
    assert "Yahoo session 2026-08-24 is available" in output


def test_yahoo_wait_fails_clearly_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(
        run_data_pipeline,
        "yahoo_session_is_available",
        lambda session: False,
    )

    with pytest.raises(RuntimeError, match="has not published session"):
        run_data_pipeline.wait_for_yahoo_session(
            date(2026, 8, 24),
            max_wait_minutes=0,
            poll_seconds=120,
        )


def test_main_forwards_full_refresh_and_finishes_with_timezone_aware_time(
    monkeypatch,
    capsys,
) -> None:
    universe_file = Path("iwv_snapshot.csv")
    universe = pd.DataFrame(
        {"security_id": ["AAPL"], "ticker": ["AAPL"]}
    )
    registry = universe.assign(in_current_universe=True)
    update_calls = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_data_pipeline.py",
            "--full-refresh",
            "--as-of",
            "2026-08-21",
        ],
    )
    monkeypatch.setattr(
        run_data_pipeline,
        "resolve_completed_session",
        lambda **kwargs: pd.Timestamp("2026-08-21"),
    )
    monkeypatch.setattr(
        run_data_pipeline,
        "yahoo_session_is_available",
        lambda session: True,
    )
    monkeypatch.setattr(
        run_data_pipeline,
        "ensure_daily_iwv_snapshot",
        lambda directory: universe_file,
    )
    monkeypatch.setattr(
        run_data_pipeline,
        "load_universe_csv",
        lambda path: universe,
    )
    monkeypatch.setattr(
        run_data_pipeline,
        "update_security_registry",
        lambda loaded_universe, path: registry,
    )

    def fake_update_market_data(**kwargs):
        update_calls.append(kwargs)
        security = kwargs["universe"].iloc[0]
        return pd.DataFrame(
            {
                "security_id": [security["security_id"]],
                "ticker": [security["ticker"]],
                "status": ["success"],
            }
        )

    monkeypatch.setattr(
        run_data_pipeline,
        "update_market_data",
        fake_update_market_data,
    )
    monkeypatch.setattr(
        run_data_pipeline,
        "build_data_quality_report",
        lambda **kwargs: pd.DataFrame({"quality_status": ["good"]}),
    )
    monkeypatch.setattr(
        run_data_pipeline,
        "save_data_quality_report",
        lambda report, path: None,
    )

    run_data_pipeline.main()

    output = capsys.readouterr().out
    assert len(update_calls) == 2
    assert update_calls[0]["full_refresh"] is True
    assert update_calls[0]["retry_failed_now"] is True
    assert update_calls[0]["download_through"] == date(2026, 8, 21)
    assert update_calls[1]["universe"]["ticker"].tolist() == ["IWV", "SPY"]
    assert "Mode: FULL REFRESH" in output
    assert "Finished: 1 successful, 0 failed" in output
