"""Signal definition checks independent of any portfolio filters."""
import numpy as np
import pandas as pd

from scripts.research.audit_ath_events import previous_high


def test_prior_high_excludes_today_and_keeps_missing_history_state():
    values = previous_high(pd.Series([10., 12., np.nan, 11., 15.]))
    np.testing.assert_allclose(values, [np.nan, 10., 12., 12., 12.], equal_nan=True)


def test_preperiod_seed_is_not_replaced_by_lower_current_highs():
    values = previous_high(pd.Series([10., 12., 21., 22.]), seed=20.)
    np.testing.assert_allclose(values, [20., 20., 20., 21.])


def test_split_does_not_create_artificial_breakout():
    nominal_high = pd.Series([100., 51., 53.])
    factor = pd.Series([2., 1., 1.])
    close = pd.Series([98., 50., 52.]) / factor
    assert close.gt(previous_high(nominal_high / factor)).tolist() == [False, False, True]
