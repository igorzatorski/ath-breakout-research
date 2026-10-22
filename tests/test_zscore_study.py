"""Timing and no-look-ahead checks for the isolated Z-score study."""
import numpy as np
import pandas as pd

from scripts.research.study_zscore import nonoverlap, prepare


def prices():
    close = np.arange(100, 200, dtype=float)
    return pd.DataFrame(dict(date=pd.bdate_range("2020-01-01", periods=100),
                             close=close, open=close - .5, adj_close=close * .8))


def test_signal_matches_independent_sample_formula():
    raw = prices()
    actual = prepare(raw)
    for window in (30, 60):
        values = raw.close.iloc[81-window:81].to_numpy()
        mean = sum(values) / window
        sd = (sum((values - mean) ** 2) / (window - 1)) ** .5
        assert np.isclose(actual.loc[80, f"z{window}"], (values[-1] - mean) / sd)


def test_execution_timing_and_dividend_factor():
    raw = prices()
    raw.loc[61:, "adj_close"] *= 1.01
    actual = prepare(raw)
    expected = raw.adj_close.iloc[65] / (raw.open.iloc[61] * raw.adj_close.iloc[61] / raw.close.iloc[61]) - 1
    assert np.isclose(actual.forward_return.iloc[60], expected)
    assert actual.entry_date.iloc[60] == raw.date.iloc[61]
    assert actual.exit_date.iloc[60] == raw.date.iloc[65]
    assert actual.forward_return.tail(5).isna().all()


def test_future_changes_do_not_change_past_signals():
    raw = prices()
    original = prepare(raw)
    raw.loc[81:, ["close", "open", "adj_close"]] *= 7
    changed = prepare(raw)
    pd.testing.assert_frame_equal(original.loc[:80, ["z30", "z60"]], changed.loc[:80, ["z30", "z60"]])


def test_nonoverlap_allows_only_entry_after_previous_exit():
    chosen = np.flatnonzero(nonoverlap(np.ones(21, dtype=bool)))
    np.testing.assert_array_equal(chosen, [0, 5, 10, 15, 20])
    assert ((chosen[1:] + 1) > (chosen[:-1] + 5)).all()
