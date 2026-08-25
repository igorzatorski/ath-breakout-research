from datetime import date
from pathlib import Path
import sys

import pandas as pd

from scripts import run_data_pipeline


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
    assert update_calls[0]["download_through"] == date(2026, 8, 21)
    assert update_calls[1]["universe"]["ticker"].tolist() == ["IWV"]
    assert "Mode: FULL REFRESH" in output
    assert "Finished: 1 successful, 0 failed" in output
