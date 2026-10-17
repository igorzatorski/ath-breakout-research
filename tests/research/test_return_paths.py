import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.return_paths import path_metrics, distribution


def test_winner_can_cross_loss_before_first_doubling():
    m = path_metrics(np.array([[.75, 1.2, 2., 3.2], [2., .6, 2.5, 2.1]]))
    assert np.isclose(m.loc[0, 'mae'], -.25)
    assert np.isclose(m.loc[0, 'mae_before_100'], -.25)
    assert m.loc[0, 'first_100'] == 3
    assert m.loc[1, 'first_100'] == 1 and m.loc[1, 'mae_before_100'] == 0
    assert np.isclose(m.loc[1, 'max_drawdown'], -.7)


def test_ever_hitting_is_not_final_return_and_complete_loss_is_valid():
    m = path_metrics(np.array([[1., 4.5, 1.1], [1., 0., 0.]]))
    assert m.loc[0, 'ever_300'] and m.loc[0, 'first_300'] == 2
    assert np.isclose(m.loc[0, 'mfe'], 3.5)
    assert not m.loc[1, 'ever_50'] and np.isnan(m.loc[1, 'mae_before_50'])
    assert m.loc[1, 'mae'] == m.loc[1, 'max_drawdown'] == -1
    with pytest.raises(ValueError):
        path_metrics(np.array([[np.nan]]))


def test_bins_include_boundaries_overflow_and_reconcile_mean():
    f = pd.DataFrame({'r': [-1., -.5, -.2, 0., .2, .5, 1., 2., 3., 10.]})
    d = pd.DataFrame(distribution(f, 'r'))
    assert d.events.sum() == len(f) and d.iloc[-1].events == 2
    assert np.isclose(d.fraction.sum(), 1.)
    assert np.isclose(d.contribution.sum(), f.r.mean())
