from datetime import date

import pandas as pd

from ath_breakout.data.security_registry import update_security_registry


def test_adds_new_current_securities(tmp_path) -> None:
    registry_file = tmp_path / "security_registry.csv"
    current_universe = pd.DataFrame(
        {
            "security_id": ["AAPL", "MSFT"],
            "ticker": ["AAPL", "MSFT"],
        }
    )

    registry = update_security_registry(
        current_universe,
        registry_file,
        today=date(2026, 8, 24),
    )

    assert registry["security_id"].tolist() == ["AAPL", "MSFT"]
    assert registry["in_current_universe"].tolist() == [True, True]
    assert registry_file.exists()
    assert not (tmp_path / "security_registry.tmp.csv").exists()


def test_retains_and_marks_security_removed_from_universe(tmp_path) -> None:
    registry_file = tmp_path / "security_registry.csv"
    initial_universe = pd.DataFrame(
        {
            "security_id": ["AAPL", "MSFT"],
            "ticker": ["AAPL", "MSFT"],
        }
    )
    update_security_registry(
        initial_universe,
        registry_file,
        today=date(2026, 8, 17),
    )

    current_universe = pd.DataFrame(
        {"security_id": ["AAPL"], "ticker": ["AAPL"]}
    )
    registry = update_security_registry(
        current_universe,
        registry_file,
        today=date(2026, 8, 24),
    )

    msft = registry[registry["security_id"] == "MSFT"].iloc[0]
    assert bool(msft["in_current_universe"]) is False
    assert msft["last_seen_in_universe"] == "2026-08-17"


def test_updates_ticker_for_existing_security(tmp_path) -> None:
    registry_file = tmp_path / "security_registry.csv"
    old_universe = pd.DataFrame(
        {"security_id": ["HEIA"], "ticker": ["HEIA"]}
    )
    update_security_registry(old_universe, registry_file)

    corrected_universe = pd.DataFrame(
        {"security_id": ["HEIA"], "ticker": ["HEI-A"]}
    )
    registry = update_security_registry(corrected_universe, registry_file)

    assert registry["ticker"].tolist() == ["HEI-A"]
