import numpy as np
import pandas as pd

from ath_breakout.research.breakout_strength import prior_atr, mask, band_codes


def test_gap_true_range_signal_and_future_excluded():
    c = pd.DataFrame({'a': [100., 110., 112., 900., 1.]})
    h, l = c+1, c-1
    a = prior_atr(h, l, c, 2)
    assert a.iloc[3, 0] == 7.  # TR at1=11, at2=3
    h.iloc[3:] = 9999.
    l.iloc[3:] = .01
    c.iloc[3:] = 999.
    assert prior_atr(h, l, c, 2).iloc[3, 0] == 7.
    assert np.isclose(prior_atr(h/2, l/2, c/2, 2).iloc[3, 0], 3.5)


def test_missing_sessions_invalid_ohlc_and_previous_close():
    c = pd.DataFrame({'a': [100., 110., 112., 115.]})
    h, l = c+1, c-1
    h.iloc[0] = np.nan  # Only close0 is needed for TR1.
    assert prior_atr(h, l, c, 2).iloc[3, 0] == 7.
    h.iloc[2] = 100.
    assert np.isnan(prior_atr(h, l, c, 2).iloc[3, 0])
    h, l = c+1, c-1
    c.iloc[0] = np.nan
    assert np.isnan(prior_atr(h, l, c, 2).iloc[3, 0])
    c.iloc[1] = np.nan
    assert np.isnan(prior_atr(h, l, c, 2).iloc[3, 0])


def test_band_partition_matches_tolerant_cutoffs():
    f = pd.DataFrame({'breakout_strength': [.01, .1-5e-13, .25, .5, 1., 2.]})
    assert band_codes(f).tolist() == [0, 1, 2, 3, 4, 5]
    assert mask(f, .25).tolist() == [False, False, True, True, True, True]
