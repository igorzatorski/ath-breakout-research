"""Past-only, cross-year exclusion of repeated security signals."""
import numpy as np
import pandas as pd


def cooldown_event_ids(events, sessions, cooldown=21):
    """Skip the next `cooldown` sessions after each retained event, per PERMNO."""
    if not isinstance(cooldown, int) or isinstance(cooldown, bool) or cooldown < 0:
        raise ValueError("Cooldown must be a nonnegative integer")
    if events.event_id.duplicated().any() or events.duplicated(["permno", "date"]).any():
        raise ValueError("Duplicate event identity")
    calendar = pd.DatetimeIndex(sessions)
    if calendar.has_duplicates or not calendar.is_monotonic_increasing:
        raise ValueError("Calendar must be unique and increasing")
    ordered = events.sort_values(["permno", "date", "event_id"])
    positions = calendar.get_indexer(pd.DatetimeIndex(ordered.date))
    if (positions < 0).any():
        raise ValueError("Signal date outside exchange calendar")
    last = {}
    retained = []
    for row, position in zip(ordered.itertuples(), positions):
        if position - last.get(row.permno, -np.inf) > cooldown:
            retained.append(row.event_id)
            last[row.permno] = position
    return retained
