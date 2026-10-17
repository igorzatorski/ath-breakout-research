import numpy as np
import pandas as pd

from ath_breakout.research.record_age import previous_record_positions, classified, mask, band_codes


def test_touches_do_not_reset_and_signal_record_is_excluded():
    f = pd.DataFrame({'permno': [1]*5, 'observed_bound': [10., 12., 12., 11., 13.],
                      'prior_ath': [9., 10., 12., 12., 12.]})
    before, carry = previous_record_positions(f, np.arange(5), {})
    np.testing.assert_allclose(before.to_numpy(), [np.nan, 0., 1., 1., 1.], equal_nan=True)
    assert carry[1] == 4
    # Any later price change must not alter the prior record date for row 3.
    f.loc[4, 'observed_bound'] = 1000.
    assert previous_record_positions(f, np.arange(5), {})[0].iloc[3] == 1.


def test_carry_cross_year_and_unknown_seed_date():
    f = pd.DataFrame({'permno': [1, 1, 2, 2], 'observed_bound': [9., 11., 18., 21.],
                      'prior_ath': [10., 10., 20., 20.]})
    before, carry = previous_record_positions(f, np.array([300, 301, 300, 301]), {1: 250})
    assert before.iloc[:2].tolist() == [250., 250.]
    assert before.iloc[2:].isna().all() and carry[2] == 301
    g = pd.DataFrame({'age_exact': [np.nan, np.nan, 1., 21.], 'age_lower_bound': [253., 100., 1., 21.]})
    assert classified(g).tolist() == [True, False, True, True]
    assert mask(g, 252).tolist() == [True, False, False, False]
    assert band_codes(g.loc[classified(g)]).tolist() == [5, 0, 2]
