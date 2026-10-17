import numpy as np

from ath_breakout.data.market_calendar import valid_nyse_sessions
from ath_breakout.research.signal_study import forward_arrays


def test_252_sessions_can_extend_past_next_calendar_year():
    calendar = valid_nyse_sessions("2022-01-01", "2024-01-31")
    entry = calendar.get_loc("2022-12-30")+1
    assert calendar[entry+251].year == 2024
    close = np.full((len(calendar), 1), 100.)
    opening = close.copy()
    returns = np.full_like(close, .001)
    value, status, _ = forward_arrays(opening, close, returns, np.zeros_like(close, bool),
                                      [entry], [0], 252, len(calendar)-1)
    assert status[0] == "ok"
    assert np.isclose(value[0], 1.001**251-1)


def test_annual_horizon_respects_cutoff_even_if_later_prices_exist():
    calendar = valid_nyse_sessions("2025-01-01", "2027-01-31")
    price = np.full((len(calendar), 1), 100.)
    entry = calendar.get_loc("2025-12-31")+1
    value, status, _ = forward_arrays(price, price, np.zeros_like(price),
                                      np.zeros_like(price, bool), [entry], [0], 252,
                                      calendar.get_loc("2026-06-30"))
    assert status[0] == "censored" and np.isnan(value[0])


def test_annual_terminal_cash_is_not_repeated_or_dropped():
    price = np.full((260, 1), 100.)
    returns = np.zeros_like(price)
    terminal = np.zeros_like(price, dtype=bool)
    terminal[100, 0] = True
    returns[100, 0] = -.5
    returns[101:, 0] = np.nan
    price[100:, 0] = np.nan
    opening = np.full_like(price, 100.)
    value, status, settled = forward_arrays(opening, price, returns, terminal, [0], [0], 252, 259)
    assert status[0] == "ok" and settled[0]
    assert np.isclose(value[0], -.5)
