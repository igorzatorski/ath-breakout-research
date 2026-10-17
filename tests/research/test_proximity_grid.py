import numpy as np
import pandas as pd

from ath_breakout.research.proximity_grid import proximity_features, selected, joint_intervals, LENGTHS


def test_fixed_anchor_excludes_window_highs_and_signal_price():
    prices = pd.DataFrame({'a': [80., 95., 98., 200.]})
    prior = pd.DataFrame({'a': [100., 100., 120., 130.]})
    anchor, low, high, depth = proximity_features(prices, prior, 2)
    assert anchor.iloc[3, 0] == 100.
    assert low.iloc[3, 0] == 95. and high.iloc[3, 0] == 98.
    assert np.isclose(depth.iloc[3, 0], .05)
    prices.iloc[3, 0] = 1.
    assert np.isclose(proximity_features(prices, prior, 2)[3].iloc[3, 0], .05)


def test_missing_prices_upper_breakout_and_threshold_boundaries():
    p = pd.DataFrame({'a': [100., np.nan, 98., 99.]})
    anchor, low, high, depth = proximity_features(p, p.fillna(100.), 2)
    assert np.isnan(depth.iloc[3, 0])
    f = pd.DataFrame({'upper_10': [True, True, False], 'depth_10': [.05, .051, -.01]})
    assert selected(f, 10, .05).tolist() == [True, False, False]
    assert selected(f, 10, -1).tolist() == [True, True, False]


def test_bootstrap_full_family_and_anchor_reference_indices():
    f = pd.DataFrame({'date': pd.bdate_range('1994-01-01', periods=8000), 'permco': np.tile([1, 2], 4000),
                      'excess_spy': np.full(8000, .02)})
    for n in LENGTHS:
        f[f'upper_{n}'] = True
        f[f'depth_{n}'] = .01
    rows = pd.DataFrame(joint_intervals(f, f.date, draws=30, block=504))
    joint = rows.query("contrast=='minus_baseline_simultaneous16'")
    assert len(joint) == 16 and np.allclose(joint[['estimate', 'lower95', 'upper95']], 0)
    assert np.allclose(rows.query("contrast=='minus_anchor_only'").estimate, 0)
    f.upper_63 = False
    rows = pd.DataFrame(joint_intervals(f, f.date, draws=30, block=504))
    assert rows.query("contrast=='minus_baseline_simultaneous16'").lower95.isna().all()
