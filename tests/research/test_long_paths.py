import numpy as np

from ath_breakout.research.long_paths import closing_wealth_paths, wealth_excursions


def test_positive_endpoint_can_hide_a_large_drawdown():
    wealth = np.array([[1.1, .7, 1.5], [.9, 1., 1.2]])
    worst, drawdown = wealth_excursions(wealth)
    np.testing.assert_allclose(worst, [-.3, -.1])
    np.testing.assert_allclose(drawdown, [.7/1.1-1, -.1])


def test_terminal_cash_and_entry_overnight_are_handled_once():
    o = np.full((5, 1), 100.)
    c = np.full((5, 1), 110.)
    r = np.full((5, 1), .1)
    t = np.zeros((5, 1), bool)
    t[2, 0] = True
    r[2, 0] = -.5
    r[3:, 0] = np.nan
    c[2:, 0] = np.nan
    w = closing_wealth_paths(o, c, r, t, np.array([0]), np.array([0]), 5)
    np.testing.assert_allclose(w[0], [1.1, 1.21, .605, .605, .605])


def test_complete_loss_stays_zero_without_dividing_by_zero():
    worst, drawdown = wealth_excursions(np.array([[1., 0., 0.]]))
    assert worst[0] == drawdown[0] == -1
