import numpy as np
import pandas as pd

from ath_breakout.research.event_ranking import rank_events, common_dates, groups, contrast_matrix, balanced_draws


def test_same_date_scores_ties_caps_and_future_exclusion():
    f = pd.DataFrame({'date': [pd.Timestamp('2000-01-01')]*5, 'momentum_6_1': range(5),
        'volume_ratio_63': [1., 1.5, 2., 3., 10.], 'contraction_42': [1., .9, .8, .7, .6]})
    z = rank_events(f)
    assert z.component_V.iloc[2:].nunique() == 1
    assert z.quintile_M.tolist() == [1, 2, 3, 4, 5]
    future = f.assign(date=pd.Timestamp('2000-01-02'), momentum_6_1=999.)
    both = rank_events(pd.concat([f, future], ignore_index=True))
    assert np.allclose(z.score_MVC, both.score_MVC.iloc[:5])
    # Removing an unavailable annual outcome must not alter the precomputed rank.
    annual = z.iloc[:-1]
    assert annual.quintile_M.tolist() == [1, 2, 3, 4]
    assert len(common_dates(annual)) == 0


def test_contrast_counts_and_constant_score_ties():
    f = pd.DataFrame({'date': pd.Timestamp('2000-01-01'), 'momentum_6_1': [1.]*5,
        'volume_ratio_63': [2.]*5, 'contraction_42': [.5]*5})
    z = rank_events(f)
    assert z.quintile_MVC.eq(3).all() and len(common_dates(z)) == 0
    names, masks = groups(z)
    definitions, coefficients = contrast_matrix(names)
    assert len(definitions) == 24 and masks.shape == (5, 16)
    assert np.allclose(coefficients.sum(axis=1), 0)
    assert definitions.kind.eq('incremental_top').sum() == 3


def test_equal_date_estimate_is_not_event_weighted():
    cal = pd.bdate_range('2000-01-01', periods=20)
    f = pd.DataFrame({'date': [cal[0]]*5+[cal[-1]]*10, 'permco': 1,
        'excess_spy': [.01]*5+[.03]*10})
    points, _ = balanced_draws(f, np.ones((15, 1), bool), cal, block=5, draws=10)
    assert np.isclose(points[0], .02)
    assert not np.isclose(points[0], f.excess_spy.mean())
