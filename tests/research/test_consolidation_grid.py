import numpy as np
import pandas as pd

from ath_breakout.research.consolidation_grid import past_width, membership, grid_intervals, LENGTHS


def test_past_range_excludes_signal_and_requires_scheduled_prices():
    p = pd.DataFrame({'x': [10., 11., 10., 100., 0., 12.]})
    result = past_width(p, 3)
    assert np.isnan(result.iloc[2, 0])
    assert np.isclose(result.iloc[3, 0], .1)
    assert np.isclose(result.iloc[4, 0], 9.)
    assert np.isnan(result.iloc[5, 0])
    p.iloc[3:] = 999
    assert np.isclose(past_width(p, 3).iloc[3, 0], .1)


def test_nested_thresholds_and_empty_sparse_bootstrap_cells():
    f = pd.DataFrame({'date': pd.bdate_range('2020-01-01', periods=600), 'permco': np.tile([1, 2, 3], 200),
                      'excess_spy': np.full(600, .02)})
    for length in LENGTHS:
        f[f'width_{length}'] = .12
    m = membership(f)
    assert (m[:, 1:6].sum(axis=0) == [0, 0, 600, 600, 600]).all()
    rows = pd.DataFrame(grid_intervals(f, f.date, draws=40, block=252))
    assert np.allclose(rows.query("contrast=='level' and width==0.15").estimate, .02)
    assert rows.query("contrast=='minus_baseline_simultaneous25'").lower95.isna().all()


def test_joint_band_constant_returns_and_long_calendar():
    f = pd.DataFrame({'date': pd.bdate_range('1994-01-01', periods=8000), 'permco': np.tile([1, 2], 4000),
                      'excess_spy': np.full(8000, .03)})
    for length in LENGTHS:
        f[f'width_{length}'] = .01
    rows = pd.DataFrame(grid_intervals(f, f.date, draws=30, block=504))
    joint = rows.query("contrast=='minus_baseline_simultaneous25'")
    assert len(joint) == 25 and np.allclose(joint[['estimate', 'lower95', 'upper95']], 0)
