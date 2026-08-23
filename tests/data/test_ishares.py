from pathlib import Path

import pandas as pd

from ath_breakout.data.adapters.ishares import parse_iwv_holdings


FIXTURE_PATH = Path("tests/fixtures/iwv_holdings_sample.csv")


def test_parse_iwv_holdings_keeps_only_equities() -> None:
    csv_text = FIXTURE_PATH.read_text(encoding="utf-8")

    universe = parse_iwv_holdings(csv_text)

    assert universe["security_id"].tolist() == ["AAPL", "BRKB", "HEIA"]
    assert universe["ticker"].tolist() == ["AAPL", "BRK-B", "HEI-A"]
    assert universe["ticker"].duplicated().sum() == 0


def test_parse_iwv_holdings_adds_snapshot_information() -> None:
    csv_text = FIXTURE_PATH.read_text(encoding="utf-8")

    universe = parse_iwv_holdings(csv_text)

    assert universe["as_of_date"].iloc[0] == pd.Timestamp("2026-08-20")
    assert pd.api.types.is_datetime64_any_dtype(universe["downloaded_at"])
    assert universe["source"].iloc[0] == "IWV holdings"
