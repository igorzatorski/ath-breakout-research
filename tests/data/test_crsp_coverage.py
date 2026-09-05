from datetime import date

import pytest

from ath_breakout.data.crsp_coverage import (
    assess_crsp_coverage,
    require_crsp_screener_coverage,
)


def test_reports_stale_quarterly_coverage() -> None:
    coverage = assess_crsp_coverage("1925-12-31", "2026-06-30", "2026-09-05")

    assert coverage.latest_date == date(2026, 6, 30)
    assert coverage.calendar_days_behind == 67
    assert coverage.is_current is False


def test_accepts_coverage_through_requested_date() -> None:
    coverage = assess_crsp_coverage("1925-12-31", "2026-09-05", "2026-09-05")

    require_crsp_screener_coverage(coverage)
    assert coverage.is_current is True


def test_rejects_stale_data_for_current_screener() -> None:
    coverage = assess_crsp_coverage("1925-12-31", "2026-06-30", "2026-09-05")

    with pytest.raises(ValueError, match="before requested screener date"):
        require_crsp_screener_coverage(coverage)
