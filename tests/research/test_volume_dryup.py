import numpy as np
import pandas as pd

from ath_breakout.research.volume_dryup import comparable_volume, volume_features, mask


def test_disjoint_halves_means_signal_and_future_exclusion():
    p = pd.DataFrame({'x': [100., 200., 50., 100., 100000., 0.]})
    a, b, ratio = volume_features(p, 2)
    assert a.iloc[4, 0] == 150. and b.iloc[4, 0] == 75.
    assert ratio.iloc[4, 0] == .5
    p.iloc[4:] = 1.
    assert volume_features(p, 2)[2].iloc[4, 0] == .5
    assert mask(pd.DataFrame({'ratio_5': [.5, .51, np.nan]}), 5, .5).tolist() == [True, False, False]


def test_split_adjustment_and_common_scale_invariance():
    raw = pd.DataFrame({'x': [100., 100., 200., 200., 300.]})
    factor = pd.DataFrame({'x': [2., 2., 1., 1., 1.]})
    p = comparable_volume(raw, factor)
    assert volume_features(p, 2)[2].iloc[4, 0] == 1.
    assert np.isclose(volume_features(p*7.3, 2)[2].iloc[4, 0], 1.)


def test_missing_invalid_and_zero_volumes():
    p = pd.DataFrame({'x': [0., 0., 10., 10., 100.], 'y': [10., 10., 0., 0., 100.]})
    ratio = volume_features(p, 2)[2]
    assert np.isnan(ratio.iloc[4, 0]) and ratio.iloc[4, 1] == 0.
    p.iloc[1, 1] = np.nan
    assert np.isnan(volume_features(p, 2)[2].iloc[4, 1])
    raw = pd.Series([1., -1., np.inf, 0.])
    factor = pd.Series([0., 1., 1., 2.])
    adjusted = comparable_volume(raw, factor)
    assert adjusted.iloc[:3].isna().all() and adjusted.iloc[3] == 0.
