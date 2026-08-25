"""Choose completed NYSE sessions consistently across the data pipeline."""

from datetime import date, datetime, timedelta

import pandas as pd
import pandas_market_calendars as market_calendars


NYSE_CALENDAR = market_calendars.get_calendar("NYSE")
DATA_PUBLICATION_DELAY = timedelta(minutes=15)


def valid_nyse_sessions(
    start_date: str | date,
    end_date: str | date,
) -> pd.DatetimeIndex:
    """Return timezone-free dates on which the NYSE was open."""
    sessions = NYSE_CALENDAR.valid_days(
        start_date=start_date,
        end_date=end_date,
    )
    return sessions.tz_localize(None).normalize()


def latest_expected_session(today: date) -> pd.Timestamp:
    """Return the final NYSE session strictly before a calendar date."""
    end_date = pd.Timestamp(today) - pd.Timedelta(days=1)
    start_date = end_date - pd.Timedelta(days=14)
    sessions = valid_nyse_sessions(start_date, end_date)

    if len(sessions) == 0:
        raise ValueError("No completed NYSE session found")

    return sessions[-1]


def latest_completed_nyse_session(
    now: datetime | None = None,
) -> pd.Timestamp:
    """Use today's NYSE session only after its close and a short delay."""
    current_time = pd.Timestamp(now or datetime.now().astimezone())

    if current_time.tzinfo is None:
        raise ValueError("Current time must include a timezone")

    current_time_utc = current_time.tz_convert("UTC")
    new_york_date = current_time_utc.tz_convert("America/New_York").date()
    schedule = NYSE_CALENDAR.schedule(
        start_date=new_york_date - timedelta(days=14),
        end_date=new_york_date,
    )
    completed = schedule[
        schedule["market_close"] + DATA_PUBLICATION_DELAY <= current_time_utc
    ]

    if len(completed) == 0:
        raise ValueError("No completed NYSE session found")

    return pd.Timestamp(completed.index[-1]).normalize()


def resolve_completed_session(
    as_of: date | None = None,
    now: datetime | None = None,
) -> pd.Timestamp:
    """Resolve automatic or manually requested completed session date."""
    latest_completed = latest_completed_nyse_session(now)

    if as_of is None:
        return latest_completed

    requested_session = pd.Timestamp(as_of).normalize()
    valid_sessions = valid_nyse_sessions(as_of, as_of)

    if len(valid_sessions) == 0:
        raise ValueError(f"Requested date is not an NYSE session: {as_of}")

    if requested_session > latest_completed:
        raise ValueError(
            f"Requested NYSE session has not completed yet: {as_of}"
        )

    return requested_session
