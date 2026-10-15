import numpy as np
import pandas as pd

from ath_breakout.research.high_breakout import (
    holding_return, prior_252_high, spy_holding_return,
)


def sample():
    return pd.DataFrame({"open": [100., 112., 120.], "close": [110., 121., 133.1],
                         "total_return": [.5, .1, .1], "delisting_flag": ["N"] * 3})


def test_excludes_signal_day_and_requires_full_252_sessions():
    x = pd.Series([10.] * 252 + [100., 101.])
    y = prior_252_high(x)
    assert y.iloc[:252].isna().all()
    assert y.iloc[252] == 10
    assert y.iloc[253] == 100
    x.iloc[100] = np.nan
    assert np.isnan(prior_252_high(x).iloc[252])


def test_open_entry_excludes_overnight_and_entry_dividend():
    value, status, terminal = holding_return(sample(), 0, 3)
    assert np.isclose(value, .331)
    assert status == "ok" and not terminal


def test_missing_entry_does_not_use_later_open():
    x = sample()
    x.loc[0, "open"] = np.nan
    assert holding_return(x, 0, 2)[1] == "missing_entry_open"


def test_missing_return_does_not_become_zero():
    x = sample()
    x.loc[1, "total_return"] = np.nan
    assert holding_return(x, 0, 3)[1] == "missing_or_invalid_return"


def test_ciz_terminal_return_once_then_cash_even_if_following_rows_missing():
    x = sample()
    x.loc[1, ["total_return", "delisting_flag", "close"]] = [-.5, "Y", np.nan]
    x.loc[2, ["total_return", "close"]] = np.nan
    value, status, terminal = holding_return(x, 0, 3)
    assert np.isclose(value, -.45)
    assert status == "ok_terminal_cash" and terminal


def test_missing_close_without_terminal_is_not_carried():
    x = sample()
    x.loc[1, "close"] = np.nan
    assert holding_return(x, 0, 3)[1] == "missing_close_without_terminal"


def test_incomplete_horizon_is_censored():
    assert holding_return(sample(), 1, 3)[1] == "censored"


def test_spy_entry_day_dividend_not_credited():
    x = pd.DataFrame({"open": [100., 102.], "close": [100., 110.],
                      "adj_close": [50., 55.]})
    assert np.isclose(spy_holding_return(x, 0, 2), .1)
    assert spy_holding_return(x, 0, 1) == 0
