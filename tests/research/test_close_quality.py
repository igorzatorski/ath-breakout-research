import numpy as np
import pandas as pd

from ath_breakout.research.close_quality import closing_location, mask, band_codes


def test_extrema_midpoint_and_scale_invariance():
    p = pd.DataFrame({'high': [20., 20., 20.], 'low': [10., 10., 10.], 'close': [10., 15., 20.]})
    q = closing_location(p)
    assert q.close_quality.tolist() == [0., .5, 1.] and q.quality_status.eq('ok').all()
    np.testing.assert_allclose(closing_location(p/4).close_quality, q.close_quality)
    p.loc[2, 'close'] = 11.
    assert closing_location(p).loc[1, 'close_quality'] == .5


def test_flat_invalid_prices_and_inconsistent_ranges_are_not_clipped():
    p = pd.DataFrame({'high': [10., 10., 10., 10., np.inf, 10.], 'low': [10., 9., 11., 9., 9., 0.],
                      'close': [10., 11., 10., 8., 9.5, 9.]})
    q = closing_location(p)
    assert q.close_quality.isna().all()
    assert q.quality_status.tolist() == ['zero_range', 'inconsistent_ohlc', 'inconsistent_ohlc',
        'inconsistent_ohlc', 'missing_or_nonpositive', 'missing_or_nonpositive']


def test_inclusive_thresholds_and_missing_not_passed():
    f = pd.DataFrame({'close_quality': [.49, .5, .7, .85, .95, 1., np.nan]})
    assert mask(f, .95).tolist() == [False, False, False, False, True, True, False]
    assert mask(f, .5).sum() == 5


def test_disjoint_bands_match_inclusive_threshold_tolerance():
    f = pd.DataFrame({'close_quality': [.5-5e-13, .7-5e-13, .85-5e-13, .95-5e-13, .2]})
    codes = band_codes(f)
    assert codes.tolist() == [1, 2, 3, 4, 0]
    for i, threshold in enumerate([.5, .7, .85, .95]):
        assert (codes > i).sum() == mask(f, threshold).sum()
