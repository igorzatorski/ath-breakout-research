import numpy as np
import pandas as pd

from ath_breakout.research.exit_rules import simulate_exit, signal_atr, matched_spy_return


def rows(opens, closes):
    close = np.asarray(closes, float)
    return pd.DataFrame({"open": np.asarray(opens, float), "close": close,
                         "high": close+2, "low": close-2,
                         "price_adjustment_factor": np.ones(len(close)),
                         "total_return": np.r_[np.nan, close[1:]/close[:-1]-1],
                         "delisting_flag": ["N"]*len(close),
                         "ordinary_dividend": np.zeros(len(close)),
                         "nonordinary_dividend": np.zeros(len(close))})


def test_failure_fills_next_open_not_trigger_close_and_includes_gap():
    x = rows([100, 80, 200], [95, 200, 300])
    r = simulate_exit(x, "failed_breakout", 99, 5)
    assert r["exit_index"] == 1 and r["exit_reason"] == "trigger_next_open"
    assert np.isclose(r["gross_return"], -.2)


def test_exit_day_close_and_return_cannot_change_open_fill():
    a = rows([100, 80, 200], [95, 200, 300])
    b = a.copy()
    b.loc[1:, ["close", "total_return"]] = np.nan
    assert simulate_exit(a, "failed_breakout", 99, 5)["gross_return"] == simulate_exit(b, "failed_breakout", 99, 5)["gross_return"]


def test_ex_date_dividend_entitlement_on_opening_exit():
    x = rows([100, 89, 100], [95, 90, 100])
    x.loc[1, "ordinary_dividend"] = 1
    r = simulate_exit(x, "failed_breakout", 99, 5)
    assert np.isclose(r["gross_return"], -.1)


def test_missing_exit_open_is_not_replaced_with_later_price():
    x = rows([100, np.nan, 200], [95, 110, 300])
    assert simulate_exit(x, "failed_breakout", 99, 5)["status"] == "missing_scheduled_exit_open"


def test_initial_atr_and_trailing_close_trigger():
    x = rows([100, 99, 129, 121, 118], [100, 130, 125, 120, 119])
    r = simulate_exit(x, "atr_trend", 99, 3)
    assert r["trigger_session"] == 4
    assert r["exit_index"] == 4
    assert np.isclose(r["gross_return"], .18)
    y = rows([100, 85, 90], [89, 90, 90])
    assert simulate_exit(y, "atr_trend", 99, 5)["trigger_session"] == 1


def test_terminal_return_is_not_double_counted_after_pending_exit():
    x = rows([100, np.nan, np.nan], [95, np.nan, np.nan])
    x.loc[1, ["delisting_flag", "total_return"]] = ["Y", -.5]
    r = simulate_exit(x, "failed_breakout", 99, 5)
    assert np.isclose(r["gross_return"], -.525)
    assert r["exit_reason"] == "terminal_cash"


def test_split_basis_preserves_opening_exit_value():
    x = rows([100, 40, 50], [95, 45, 50])
    x.loc[0, "price_adjustment_factor"] = 2
    r = simulate_exit(x, "failed_breakout", 49, 2)
    assert np.isclose(r["gross_return"], -.2)


def test_atr_uses_current_and_past_only():
    x = rows([100]*23, [100]*23)
    a = signal_atr(x)
    assert np.isnan(a.iloc[19]) and a.iloc[20] == 4
    x.loc[22, "high"] = 1000
    assert signal_atr(x).iloc[21] == a.iloc[21]


def test_spy_opening_exit_dividend_and_horizon_close():
    x = pd.DataFrame({"open": [100., 90., 95.], "close": [100., 95., 110.],
                      "adj_close": [50., 48., 56.], "dividends": [0., 1., 0.]})
    assert np.isclose(matched_spy_return(x, 1, "trigger_next_open"), -.09)
    assert np.isclose(matched_spy_return(x, 2, "horizon_close"), .12)
