import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.sma50_portfolio import Portfolio


def rows(opening=100., close=100., dividend=0., ret=0., sma=90., terminal=False, previous=100.):
    return {k: np.array([v]) for k, v in {'open': opening, 'close': close, 'dividend': dividend,
        'return': ret, 'sma': sma, 'terminal': terminal, 'observed': True, 'previous_close': previous, 'company': 10}.items()}


def signal(date):
    return {'permno': 1, 'permco': 10, 'ticker': 'A', 'date': pd.Timestamp(date), 'score_MV': .8}


def test_close_trigger_executes_next_open_including_gap_and_no_lookahead():
    p = Portfolio('drift', 0)
    p.session(pd.Timestamp('2000-01-04'), pd.Timestamp('2000-01-03'), rows(close=95., sma=96.), {1: 0}, [signal('2000-01-03')])
    assert 1 in p.positions and p.positions[1].pending_since == pd.Timestamp('2000-01-04')
    p.session(pd.Timestamp('2000-01-05'), pd.Timestamp('2000-01-04'), rows(opening=80., close=85., previous=95., ret=85/95-1), {1: 0}, [])
    assert not p.positions
    assert p.transactions[-1]['price'] == 80.
    assert p.closed[0]['pnl'] == -1000.
    with pytest.raises(ValueError, match='previous session'):
        Portfolio('drift', 0).session(pd.Timestamp('2000-01-04'), pd.Timestamp('2000-01-03'), rows(), {1: 0}, [signal('2000-01-04')])


def test_distribution_only_overnight_holders_and_terminal_once():
    p = Portfolio('drift', 0)
    p.session(pd.Timestamp('2000-01-04'), pd.Timestamp('2000-01-03'), rows(dividend=2.), {1: 0}, [signal('2000-01-03')])
    assert p.positions[1].dividends == 0
    p.session(pd.Timestamp('2000-01-05'), pd.Timestamp('2000-01-04'), rows(close=98., dividend=2., ret=0.), {1: 0}, [])
    assert p.positions[1].dividends == 100.
    assert np.isclose(p.nav(), 100000.)
    p.session(pd.Timestamp('2000-01-06'), pd.Timestamp('2000-01-05'), rows(opening=np.nan, close=np.nan, previous=98., ret=-.5, terminal=True), {1: 0}, [])
    assert not p.positions and p.transactions[-1]['kind'] == 'CIZ_TERMINAL'
    assert np.isclose(p.nav(), 97550.)
    p.session(pd.Timestamp('2000-01-07'), pd.Timestamp('2000-01-06'), rows(terminal=True), {1: 0}, [])
    assert np.isclose(p.nav(), 97550.)


def test_monthly_targets_costs_and_distinct_companies():
    p = Portfolio('monthly_equal', 10, maximum=1, weight=1.)
    p.session(pd.Timestamp('2000-01-31'), pd.Timestamp('2000-01-28'), rows(), {1: 0}, [signal('2000-01-28')])
    p.session(pd.Timestamp('2000-02-01'), pd.Timestamp('2000-01-31'), rows(opening=110., close=110., ret=.1), {1: 0}, [signal('2000-01-31')])
    assert len(p.positions) == 1 and p.cash >= -1e-6
    assert any(s['reason'] == 'already_held_company' for s in p.skips)
    assert np.isclose(p.positions[1].quantity*110/p.nav(), 1.)
    for t in p.transactions:
        if t['kind'] != 'DIVIDEND':
            assert np.isclose(t['nav_after'], t['nav_before']-t['fee'])


def test_missing_exit_open_defers_and_inconsistent_return_blocks():
    p = Portfolio('drift', 0)
    p.session(pd.Timestamp('2000-01-04'), pd.Timestamp('2000-01-03'), rows(close=95., sma=96.), {1: 0}, [signal('2000-01-03')])
    p.session(pd.Timestamp('2000-01-05'), pd.Timestamp('2000-01-04'), rows(opening=np.nan, close=95., previous=95., ret=0.), {1: 0}, [])
    assert 1 in p.positions and p.deferred_exits == 1
    with pytest.raises(ValueError, match='Unexplained CIZ'):
        p.session(pd.Timestamp('2000-01-06'), pd.Timestamp('2000-01-05'), rows(close=95., previous=95., ret=.5), {1: 0}, [])


def test_stale_mark_not_compared_with_unmatched_source_return():
    p = Portfolio('drift', 0)
    p.session(pd.Timestamp('2000-01-04'), pd.Timestamp('2000-01-03'), rows(), {1: 0}, [signal('2000-01-03')])
    p.session(pd.Timestamp('2000-01-05'), pd.Timestamp('2000-01-04'), rows(opening=np.nan, close=np.nan, ret=.01), {1: 0}, [])
    assert p.nav() == 100000 and p.stale_marks == 1
    p.session(pd.Timestamp('2000-01-06'), pd.Timestamp('2000-01-05'), rows(opening=102., close=102., previous=np.nan, ret=102/101-1), {1: 0}, [])
    assert p.nav() == 100100
    assert p.skips[-1]['reason'] == 'return_check_unmatched_previous_mark'


def test_adjusted_units_preserve_split_economic_value():
    p = Portfolio('drift', 0)
    p.session(pd.Timestamp('2000-01-04'), pd.Timestamp('2000-01-03'), rows(), {1: 0}, [signal('2000-01-03')])
    # A 2-for-1 split: raw 50 / cumulative adjustment .5 = adjusted 100.
    p.session(pd.Timestamp('2000-01-05'), pd.Timestamp('2000-01-04'), rows(opening=50/.5, close=50/.5), {1: 0}, [])
    assert p.positions[1].quantity == 50 and p.nav() == 100000


def test_simultaneous_split_cash_distribution_reconciles_ciz_example():
    p = Portfolio('drift', 0)
    prior = 55.96/1.5
    p.session(pd.Timestamp('2005-12-12'), pd.Timestamp('2005-12-09'),
        rows(opening=prior, close=prior, sma=30.), {1: 0}, [signal('2005-12-09')])
    p.session(pd.Timestamp('2005-12-13'), pd.Timestamp('2005-12-12'),
        rows(opening=37.71, close=37.53, previous=prior, sma=30., dividend=.16875/1.5, ret=.009002), {1: 0}, [])
    assert p.max_return_error < 1e-6
    assert np.isclose(p.nav(), 95000+5000*(37.53+.1125)/prior)
