import numpy as np

from ath_breakout.research.exit_diagnostic import price_components, unit_path


def path(close, dividend=None, terminal=None, ret=None, previous=None, opening=None, exit_index=1):
    n = len(close)
    return unit_path(np.array(opening if opening is not None else close, float), np.array(close, float),
        np.array(dividend if dividend is not None else [0]*n, float),
        np.array(terminal if terminal is not None else [False]*n),
        np.array(ret if ret is not None else [0]*n, float),
        np.array(previous if previous is not None else [100]*n, float),100.,exit_index,cost=0.)


def test_entry_exdate_excluded_exit_exdate_included_and_endpoint_not_maximum():
    r = path([100, 90, 150, 95], dividend=[10, 2, 0, 0])
    assert np.isclose(r['sale_return'], -.08)
    assert np.isclose(r['hold_return'], -.03)
    assert np.isclose(r['hold_minus_sale'], .05)
    assert np.isclose(r['max_post_exit_price_return'], 150/90-1)


def test_terminal_settles_once_then_cash_and_future_missing_prices_allowed():
    r = path([100, 90, np.nan, np.nan], terminal=[False,False,True,False],
        ret=[0,0,-.5,0], previous=[100,100,90,np.nan], dividend=[0,0,0,np.nan])
    assert np.isclose(r['hold_return'], -.55)
    assert r['terminal_before_endpoint']


def test_missing_regular_close_invalidates_pair():
    assert path([100,90,np.nan,110]) is None


def test_all_holding_gaps_distinct_from_final_execution_gap():
    r = price_components(np.array([100.,70.,75.]),np.array([100.,80.,999.]),100.,75.)
    assert np.isclose(r['all_holding_gap_return'], -.35)
    assert np.isclose(r['all_holding_intraday_return'], .1)
    assert np.isclose(r['worst_overnight_gap'], -.3)
