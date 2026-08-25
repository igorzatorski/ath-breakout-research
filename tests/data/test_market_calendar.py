from datetime import date, datetime, timezone

import pandas as pd
import pytest

from ath_breakout.data.market_calendar import (
    latest_completed_nyse_session,
    resolve_completed_session,
)


def test_uses_previous_session_before_nyse_close() -> None:
    result = latest_completed_nyse_session(
        datetime(2026, 8, 24, 19, 0, tzinfo=timezone.utc)
    )

    assert result == pd.Timestamp("2026-08-21")


def test_uses_today_after_nyse_close_and_publication_delay() -> None:
    result = latest_completed_nyse_session(
        datetime(2026, 8, 24, 20, 30, tzinfo=timezone.utc)
    )

    assert result == pd.Timestamp("2026-08-24")


def test_manual_as_of_accepts_completed_session() -> None:
    result = resolve_completed_session(
        as_of=date(2026, 8, 21),
        now=datetime(2026, 8, 24, 20, 30, tzinfo=timezone.utc),
    )

    assert result == pd.Timestamp("2026-08-21")


def test_manual_as_of_rejects_weekend() -> None:
    with pytest.raises(ValueError, match="not an NYSE session"):
        resolve_completed_session(
            as_of=date(2026, 8, 22),
            now=datetime(2026, 8, 24, 20, 30, tzinfo=timezone.utc),
        )
