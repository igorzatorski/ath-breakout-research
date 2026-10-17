import numpy as np

from ath_breakout.research.capm_events import capm_event_arrays


def fixture_arrays():
    rng = np.random.default_rng(65)
    x = rng.normal(.0003, .01, 800)
    rf = np.full(800, .0001)
    r = (rf+1.4*x+.0002)[:, None]
    return r, np.zeros_like(r, bool), x, rf


def test_beta_lag_car_and_future_information():
    r, t, x, rf = fixture_arrays()
    b, a, n, car = capm_event_arrays(r, t, x, rf, np.array([300]), np.array([0]), np.array([True]))
    assert n[0] == 252 and np.isclose(b[0], 1.4) and np.isclose(a[0], .0002)
    assert np.isclose(car[0], 251*.0002)
    r[300:302] = 100  # Signal day and entry partial day do not enter beta/CAR.
    b1, _, _, c1 = capm_event_arrays(r, t, x, rf, np.array([300]), np.array([0]), np.array([True]))
    assert np.isclose(b1[0], b[0]) and np.isclose(c1[0], car[0])


def test_terminal_cash_and_censoring():
    r, t, x, rf = fixture_arrays()
    t[350, 0] = True
    r[350, 0] = -.5
    r[351:] = np.nan
    b, _, _, car = capm_event_arrays(r, t, x, rf, np.array([300, 300]), np.array([0, 0]), np.array([True, False]))
    expected = (r[302:351, 0]-rf[302:351]-b[0]*x[302:351]).sum()-rf[351:553].sum()
    assert np.isclose(car[0], expected)
    assert np.isnan(car[1])


def test_minimum_estimation_observations():
    r, t, x, rf = fixture_arrays()
    r[48:101, 0] = np.nan  # Only 199 valid observations in trailing window.
    b, _, n, car = capm_event_arrays(r, t, x, rf, np.array([300]), np.array([0]), np.array([True]))
    assert n[0] == 199 and np.isnan(b[0]) and np.isnan(car[0])
    r[100, 0] = rf[100]+1.4*x[100]+.0002
    b, _, n, car = capm_event_arrays(r, t, x, rf, np.array([300]), np.array([0]), np.array([True]))
    assert n[0] == 200 and np.isclose(b[0], 1.4) and np.isfinite(car[0])


def test_constant_market_has_no_identifiable_beta():
    r, t, x, rf = fixture_arrays()
    x[:] = .001
    b, _, _, car = capm_event_arrays(r, t, x, rf, np.array([300]), np.array([0]), np.array([True]))
    assert np.isnan(b[0]) and np.isnan(car[0])
