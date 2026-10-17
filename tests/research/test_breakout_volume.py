import numpy as np
import pandas as pd

from ath_breakout.research.breakout_volume import breakout_volume_features, mask
from ath_breakout.research.volume_dryup import comparable_volume


def test_signal_in_numerator_but_not_denominator_no_future():
    p = pd.DataFrame({'x': [100., 100., 200., 100000.]})
    prior, current, ratio = breakout_volume_features(p, 2)
    assert prior.iloc[2, 0] == 100. and current.iloc[2, 0] == 200.
    assert ratio.iloc[2, 0] == 2.
    p.iloc[3] = 1.
    assert breakout_volume_features(p, 2)[2].iloc[2, 0] == 2.
    p.iloc[2] = 300.
    assert breakout_volume_features(p, 2)[0].iloc[2, 0] == 100.
    assert breakout_volume_features(p, 2)[2].iloc[2, 0] == 3.


def test_split_adjustment_and_scale_invariance():
    raw = pd.DataFrame({'x': [100., 100., 200.]})
    factor = pd.DataFrame({'x': [2., 2., 1.]})
    adjusted = comparable_volume(raw, factor)
    assert breakout_volume_features(adjusted, 2)[2].iloc[2, 0] == 1.
    assert np.isclose(breakout_volume_features(adjusted*1.73, 2)[2].iloc[2, 0], 1.)


def test_full_schedule_zero_mean_zero_current_invalid_and_nested_thresholds():
    p = pd.DataFrame({'x': [0., 0., 10.], 'y': [10., 10., 0.], 'z': [10., np.nan, 30.]})
    ratio = breakout_volume_features(p, 2)[2]
    assert np.isnan(ratio.iloc[2, 0]) and ratio.iloc[2, 1] == 0.
    assert np.isnan(ratio.iloc[2, 2])
    p.iloc[2, 1] = -1.
    assert np.isnan(breakout_volume_features(p, 2)[2].iloc[2, 1])
    f = pd.DataFrame({'ratio_5': [0., 1., 1.5, 2., 3., np.nan]})
    assert mask(f, 5, 1.5).tolist() == [False, False, True, True, True, False]
    assert mask(f, 5, 3.).sum() <= mask(f, 5, 2.).sum()
