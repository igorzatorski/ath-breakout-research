import numpy as np
import pandas as pd

from ath_breakout.research.sma_trend import signal_sma, greater, memberships


def test_current_close_included_future_excluded_and_missing_not_skipped():
    p = pd.DataFrame({'a': [1., 2., 3., 100.]})
    assert signal_sma(p, 3).iloc[2, 0] == 2.
    p.iloc[3] = 999.
    assert signal_sma(p, 3).iloc[2, 0] == 2.
    p.iloc[1] = np.nan
    assert np.isnan(signal_sma(p, 3).iloc[2, 0])


def test_strict_ties_and_trend_hierarchy_are_not_price_position():
    assert not greater(100., 100.)
    assert not greater(100.+1e-11, 100.)
    assert greater(100.001, 100.)
    f = pd.DataFrame({'signal_close': [110., 110., 110.], 'sma_20': [100., 100., np.nan],
        'sma_50': [105., 90., 105.], 'sma_100': [100., 100., 100.], 'sma_200': [95., 95., 100.]})
    m = memberships(f)
    assert m['price_gt200'].tolist() == [True, True, True]
    assert m['sma100_gt200'].tolist() == [True, True, False]
    assert m['sma50_gt100_gt200'].tolist() == [True, False, False]
    assert m['price_gt20'].tolist() == [True, True, False]
