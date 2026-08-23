import pandas as pd
import pytest

from ath_breakout.data.universe import find_latest_iwv_snapshot
from ath_breakout.data.universe import load_universe_csv, validate_universe


def test_loads_valid_universe() -> None:
    universe = load_universe_csv("tests/fixtures/universe_valid.csv")

    assert universe["ticker"].tolist() == ["AAPL", "MSFT"]


def test_rejects_duplicate_security_ids() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate security_id values found in universe",
    ):
        load_universe_csv("tests/fixtures/universe_duplicate.csv")


def test_rejects_missing_required_column(tmp_path) -> None:
    file_path = tmp_path / "missing_ticker.csv"
    pd.DataFrame({"security_id": ["AAPL"]}).to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Missing universe column: ticker"):
        load_universe_csv(file_path)


def test_rejects_missing_ticker(tmp_path) -> None:
    file_path = tmp_path / "missing_value.csv"
    pd.DataFrame(
        {"security_id": ["AAPL"], "ticker": [None]}
    ).to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Missing universe values in column: ticker"):
        load_universe_csv(file_path)


def test_rejects_duplicate_tickers(tmp_path) -> None:
    file_path = tmp_path / "duplicate_ticker.csv"
    pd.DataFrame(
        {
            "security_id": ["BRKB", "BRK-B"],
            "ticker": ["BRK-B", "BRK-B"],
        }
    ).to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Duplicate ticker values found in universe"):
        load_universe_csv(file_path)


def test_validates_universe_already_held_in_memory() -> None:
    universe = pd.DataFrame(
        {
            "security_id": ["AAPL", "MSFT"],
            "ticker": ["AAPL", "MSFT"],
        }
    )

    validate_universe(universe)


def test_finds_latest_iwv_snapshot(tmp_path) -> None:
    older_file = tmp_path / "iwv_holdings_2026-08-19.csv"
    newer_file = tmp_path / "iwv_holdings_2026-08-20.csv"
    older_file.touch()
    newer_file.touch()

    result = find_latest_iwv_snapshot(tmp_path)

    assert result == newer_file


def test_reports_missing_iwv_snapshot(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="No IWV universe snapshot found"):
        find_latest_iwv_snapshot(tmp_path)
