import numpy as np
import pandas as pd

from ath_breakout.research.range_contraction import contraction_features, mask
from ath_breakout.research.filter_grid import joint_grid_intervals


def test_equal_nonoverlapping_halves_exclude_signal_and_future():
    p = pd.DataFrame({'a': [100., 120., 110., 115., 999., 1.]})
    early, recent, ratio = contraction_features(p, 2)
    assert np.isclose(early.iloc[4, 0], .2)
    assert np.isclose(recent.iloc[4, 0], 115/110-1)
    assert np.isclose(ratio.iloc[4, 0], (115/110-1)/.2)
    p.iloc[4:] = 10.
    assert np.isclose(contraction_features(p, 2)[2].iloc[4, 0], ratio.iloc[4, 0])


def test_flat_denominator_missing_price_and_zero_recent_range():
    p = pd.DataFrame({'a': [100., 100., 110., 110., 150.], 'b': [100., 120., 110., 110., 150.]})
    _, _, ratio = contraction_features(p, 2)
    assert np.isnan(ratio.iloc[4, 0])
    assert ratio.iloc[4, 1] == 0.
    p.iloc[1, 1] = np.nan
    assert np.isnan(contraction_features(p, 2)[2].iloc[4, 1])
    f = pd.DataFrame({'ratio_5': [.5, .75, 1., np.nan]})
    assert mask(f, 5, .5).tolist() == [True, False, False, False]


def test_generic_joint_bands_constant_returns_and_empty_family_member():
    f = pd.DataFrame({'date': pd.bdate_range('1994-01-01', periods=8000), 'permco': np.tile([1, 2], 4000),
                      'excess_spy': np.full(8000, .02)})
    labels = [dict(half=0, ratio=0.), dict(half=5, ratio=.5), dict(half=5, ratio=.75)]
    groups = np.ones((len(f), 3), dtype=bool)
    result = pd.DataFrame(joint_grid_intervals(f, groups, labels, f.date, draws=30, block=504))
    joint = result.query("contrast=='minus_baseline_simultaneous2'")
    assert len(joint) == 2 and np.allclose(joint[['estimate', 'lower95', 'upper95']], 0)
    groups[:, 2] = False
    result = pd.DataFrame(joint_grid_intervals(f, groups, labels, f.date, draws=30, block=504))
    assert result.query("contrast=='minus_baseline_simultaneous2'").lower95.isna().all()
