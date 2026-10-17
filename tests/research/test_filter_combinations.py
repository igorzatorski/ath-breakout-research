import numpy as np
import pandas as pd

from ath_breakout.research.filter_combinations import STATES, contrasts, memberships, contrast_intervals


def test_all_intersections_and_edge_counts_with_nonnested_neighbors():
    f = pd.DataFrame({'contraction_42': [.5, 1.], 'contraction_63': [1., .5],
        'volume_ratio_63': [1., 3.], 'age_exact': [130., np.nan], 'age_lower_bound': [130., 300.],
        'breakout_strength': [.7, 1.5]})
    g = memberships(f)
    assert g.shape == (2, 81) and g[:, 0].all()
    assert g[:, STATES.index((1, 0, 0, 0))].tolist() == [True, False]
    assert g[:, STATES.index((2, 2, 2, 2))].tolist() == [False, True]
    e = contrasts()
    assert e.kind.value_counts().to_dict() == {'addition': 216, 'neighbor': 108, 'baseline': 80}
    assert len(e.loc[e.kind.eq('addition') & e.main]) == 32
    for r in e.loc[e.kind.eq('addition')].itertuples():
        assert (~g[:, r.child] | g[:, r.parent]).all()


def test_shared_contrasts_and_family_unavailability():
    e = contrasts()
    points = np.arange(81, dtype=float)/100
    samples = np.tile(points, (30, 1))
    a = contrast_intervals(points, samples, e)
    assert np.allclose(a.lower95, a.estimate) and np.allclose(a.upper95, a.estimate)
    assert np.allclose(a.all404_lower, a.estimate)
    samples[:, -1] = np.nan
    a = contrast_intervals(points, samples, e)
    assert a.all404_lower.isna().all()
    assert a.loc[a.child.eq(80), 'lower95'].isna().all()
