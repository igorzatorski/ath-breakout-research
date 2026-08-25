from datetime import date

import pandas as pd
import pytest

from scripts.run_portfolio_backtest import parse_arguments, resolve_period


def test_defaults_to_five_years_and_standard_portfolio_rules() -> None:
    spy = pd.DataFrame({"date": pd.to_datetime(["2021-08-24", "2026-08-24"])})
    arguments = parse_arguments([])
    start, end = resolve_period(spy, arguments.start, arguments.end)

    assert start == date(2021, 8, 24)
    assert end == date(2026, 8, 24)
    assert arguments.position_weight == 0.03
    assert arguments.max_positions == 33
    assert arguments.min_setup_score == 0.0


def test_rejects_reversed_period() -> None:
    spy = pd.DataFrame({"date": pd.to_datetime(["2026-08-24"])})
    with pytest.raises(ValueError, match="start date"):
        resolve_period(spy, date(2026, 8, 24), date(2025, 8, 24))
