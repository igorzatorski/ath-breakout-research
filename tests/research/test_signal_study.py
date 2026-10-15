import numpy as np
import pandas as pd

from ath_breakout.research.signal_study import forward_arrays, match_controls


def test_vector_returns_entry_timing_missing_terminal_and_total_loss():
    o = np.full((5, 4), 100.)
    c = np.full((5, 4), 110.)
    r = np.full((5, 4), .1)
    t = np.zeros((5, 4), dtype=bool)
    t[2, 1] = True
    r[2, 1] = -.5
    c[2:, 1] = np.nan
    r[3:, 1] = np.nan
    r[2, 2] = -1
    r[1, 3] = np.nan
    value, status, terminal = forward_arrays(o, c, r, t, [0]*4, [0,1,2,3], 5, 4)
    assert np.isclose(value[0], 1.1**5-1)
    assert np.isclose(value[1], 1.1*1.1*.5-1)
    assert value[2] == -1
    assert np.isnan(value[3]) and status[3] == "invalid_path"
    assert terminal.tolist() == [False, True, False, False]


def test_entry_and_censoring_do_not_use_later_price():
    x = np.ones((5, 1))*100
    o = x.copy();o[0, 0] = np.nan
    value, status, _ = forward_arrays(o, x, np.zeros_like(x), np.zeros_like(x, bool), [0,3], [0,0], 3, 4)
    assert np.isnan(value).all()
    assert status.tolist() == ["missing_entry", "censored"]


def test_matching_calipers_distinct_companies_and_no_future_fields():
    e = pd.DataFrame({"permno": [1], "permco": [10], "market_cap": [100.], "vol63": [.2]})
    c = pd.DataFrame({"permno": [2,3,4,5,6], "permco": [10,20,20,30,40],
                      "market_cap": [100.,100.,101.,110.,10000.], "vol63": [.2,.2,.2,.21,.2]})
    assert match_controls(e,c,k=2)[1] == [3,5]
    assert match_controls(e,c,k=3) == {}
    c["future_return"] = [1000,-1000,50,20,30]
    assert match_controls(e,c,k=2)[1] == [3,5]


def test_vector_engine_matches_scalar_for_varied_entries_and_terminal_paths():
    from ath_breakout.research.high_breakout import holding_return

    rng = np.random.default_rng(52)
    o = rng.uniform(90, 110, size=(50, 6))
    c = rng.uniform(90, 110, size=(50, 6))
    r = rng.uniform(-.1, .1, size=(50, 6))
    t = np.zeros((50, 6), dtype=bool)
    t[25, 1] = True
    r[25, 1] = -.4
    c[25:, 1] = np.nan
    r[26:, 1] = np.nan
    r[15, 2] = -1
    r[12, 3] = np.nan
    o[5, 4] = np.nan
    c[9, 5] = np.nan
    entries, columns = np.meshgrid([0, 5, 10, 24, 25, 40, 48], range(6))
    entries, columns = entries.ravel(), columns.ravel()
    for horizon in (5, 21):
        value, status, terminal = forward_arrays(o, c, r, t, entries, columns, horizon, 49)
        for j, (entry, column) in enumerate(zip(entries, columns)):
            history = pd.DataFrame({"open": o[:, column], "close": c[:, column],
                                    "total_return": r[:, column],
                                    "delisting_flag": np.where(t[:, column], "Y", "N")})
            expected, expected_status, expected_terminal = holding_return(history, entry, horizon)
            assert np.isclose(value[j], expected, atol=1e-12, equal_nan=True)
            if expected_status.startswith("ok"):
                assert status[j] == "ok" and terminal[j] == expected_terminal
