import pandas as pd
import pytest

from ath_breakout.research.event_selection import cooldown_event_ids


def events(calendar, indices, permnos=None):
    return pd.DataFrame({"event_id": range(len(indices)),
                         "permno": permnos or [1]*len(indices),
                         "date": calendar[indices]})


def test_skips_following_21_sessions_and_skips_do_not_reset_clock():
    dates = pd.bdate_range("2024-01-01", periods=60)
    x = events(dates, [0, 1, 20, 21, 22, 42, 43, 44])
    assert cooldown_event_ids(x, dates) == [0, 4, 7]


def test_tracks_securities_separately_across_year_boundary_and_input_order():
    dates = pd.bdate_range("2023-12-01", periods=60)
    x = events(dates, [19, 20, 40, 41, 20], [1, 1, 1, 1, 2])
    assert set(cooldown_event_ids(x.sample(frac=1, random_state=1), dates)) == {0, 3, 4}


def test_future_returns_and_execution_status_do_not_affect_selection():
    dates = pd.bdate_range("2024-01-01", periods=60)
    x = events(dates, [0, 10, 22])
    x["return"] = [-1., 10., .2]
    x["status"] = ["missing_entry", "ok", "ok"]
    assert cooldown_event_ids(x, dates) == [0, 2]


def test_prefix_selection_stays_unchanged_when_future_events_are_added():
    dates = pd.bdate_range("2024-01-01", periods=100)
    x = events(dates, [0, 10, 22, 30, 44, 80])
    assert cooldown_event_ids(x.iloc[:4], dates) == [i for i in cooldown_event_ids(x, dates) if i < 4]


def test_rejects_duplicate_and_non_session_dates():
    dates = pd.bdate_range("2024-01-01", periods=30)
    x = events(dates, [0, 0])
    with pytest.raises(ValueError, match="Duplicate"):
        cooldown_event_ids(x, dates)
    with pytest.raises(ValueError, match="outside"):
        cooldown_event_ids(events(dates, [0]), dates[1:])


def test_joint_bootstrap_identical_samples_have_zero_difference():
    from scripts.research.compare_ath_cooldown import joint_intervals

    x = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
                      "excess": [.01, -.02, .03, .04], "retained": True})
    result = joint_intervals(x, "excess", block=2, draws=40)
    delta = result[2]
    assert delta["mean"] == delta["lower95"] == delta["upper95"] == 0
    assert result[0]["lower95"] == result[1]["lower95"]
