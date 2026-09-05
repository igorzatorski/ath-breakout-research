"""Make CRSP coverage and screener freshness boundaries explicit."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class CrspCoverage:
    first_date: date
    latest_date: date
    requested_date: date
    calendar_days_behind: int
    is_current: bool


def assess_crsp_coverage(
    first_date: date | str,
    latest_date: date | str,
    requested_date: date | str,
) -> CrspCoverage:
    """Compare available CRSP history with a requested research date."""
    first = pd.Timestamp(first_date).date()
    latest = pd.Timestamp(latest_date).date()
    requested = pd.Timestamp(requested_date).date()
    if first > latest:
        raise ValueError("CRSP first date cannot follow its latest date")
    days_behind = max((requested - latest).days, 0)
    return CrspCoverage(
        first_date=first,
        latest_date=latest,
        requested_date=requested,
        calendar_days_behind=days_behind,
        is_current=latest >= requested,
    )


def require_crsp_screener_coverage(coverage: CrspCoverage) -> None:
    """Prevent a stale quarterly release from being labelled as current."""
    if not coverage.is_current:
        raise ValueError(
            "CRSP data ends on "
            f"{coverage.latest_date}, before requested screener date "
            f"{coverage.requested_date}"
        )
