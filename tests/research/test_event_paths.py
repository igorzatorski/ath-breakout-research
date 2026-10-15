import numpy as np
import pandas as pd

from ath_breakout.research.event_paths import describe_path, wealth_path


def history(closes):
    closes = np.asarray(closes, dtype=float)
    return pd.DataFrame({"open": [100.] * len(closes), "close": closes,
                         "low": np.minimum(closes, 100.) - 1,
                         "high": np.maximum(closes, 100.) + 1,
                         "price_adjustment_factor": np.ones(len(closes)),
                         "total_return": np.r_[np.nan, closes[1:] / closes[:-1] - 1],
                         "delisting_flag": ["N"] * len(closes)})


def test_recovers_winner_after_early_breach_without_looking_ahead_at_landmark():
    x = history([98., 96., 105., 110., 115., 125.])
    r, w = describe_path(x, 99., 95.)
    assert r["cohort"] == "winner20"
    assert r["first_plus20_close"] == 6
    assert r["first_below_level"] == 1
    assert r["below_level_by5"] and r["below_level_before20"]
    assert not r["below_252_by5"]
    assert np.isclose(r["min_close_before20"], -.04)
    assert np.isclose(r["return_after5"], 125 / 115 - 1)
    np.testing.assert_allclose(w, x.close / 100)


def test_future_change_does_not_change_day5_warning():
    a, _ = describe_path(history([98., 96., 105., 110., 115., 125.]), 99., 95.)
    b, _ = describe_path(history([98., 96., 105., 110., 115., 60.]), 99., 95.)
    assert a["below_level_by5"] == b["below_level_by5"]
    assert a["cohort"] != b["cohort"]


def test_terminal_once_and_landmark_survivorship_explicit():
    x = history([105., 100., 100., 100., 100., 100.])
    x.loc[1, ["delisting_flag", "total_return", "close"]] = ["Y", -.5, np.nan]
    x.loc[2:, "total_return"] = np.nan
    r, w = describe_path(x, 99., 95.)
    np.testing.assert_allclose(w, [1.05, .525, .525, .525, .525, .525])
    assert not r["landmark5_eligible"]
    assert r["terminal_session"] == 2


def test_missing_return_is_not_forward_filled():
    x = history([100., 105., 110., 115., 120.])
    x.loc[2, "total_return"] = np.nan
    w, status, _ = wealth_path(x)
    assert status == "invalid_return" and np.isnan(w[-1])


def test_missing_intraday_bar_does_not_produce_complete_excursion():
    x = history([100., 105., 110., 115., 125.])
    x.loc[1, "low"] = np.nan
    r, _ = describe_path(x, 99., 95.)
    assert np.isnan(r["min_price_return"])
    assert np.isfinite(r["return_126"])
