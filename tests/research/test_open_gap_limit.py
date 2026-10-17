"""Pre-submitted opening cap eligibility and unchanged SMA150 exits."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/research'))
from open_gap_limit import GapLimitPortfolio, eligible  # noqa: E402


@pytest.mark.parametrize('limit', [.5, 1., 2.])
def test_strictly_above_cap_rejected_equality_fills(limit):
    cap = 100. + 2. * limit
    assert eligible(cap, 100., 2., limit)
    assert not eligible(cap + .01, 100., 2., limit)
    assert eligible(90., 100., 2., limit)
    assert not eligible(np.nan, 100., 2., limit)
    assert not eligible(100., 100., 0., limit)


def data(opening=102., close=102., previous=100.):
    return {k: np.array([v]) for k, v in dict(open=opening, close=close,
        previous_close=previous, sma=80., sma150=90., dividend=0.,
        terminal=False, observed=True, company=10).items()} | {'return': np.array([close / previous - 1])}


def test_no_intraday_fill_or_later_chasing():
    p = GapLimitPortfolio('drift', 10, 'gap05')
    signal = dict(event_id=1, permno=1, permco=10, ticker='A',
        date=pd.Timestamp('2008-01-02'), signal_close=100., atr20_prior=2.)
    p.session(pd.Timestamp('2008-01-03'), signal['date'], data(close=99.), {1: 0}, [signal])
    assert not p.positions and not p.entry_screens[-1]['eligible']
    p.session(pd.Timestamp('2008-01-04'), pd.Timestamp('2008-01-03'), data(opening=100.), {1: 0}, [])
    assert not p.positions


def test_cap_entry_then_sma150_next_open_exit():
    p = GapLimitPortfolio('drift', 10, 'gap10')
    signal = dict(event_id=1, permno=1, permco=10, ticker='A',
        date=pd.Timestamp('2008-01-02'), signal_close=100., atr20_prior=2.)
    p.session(pd.Timestamp('2008-01-03'), signal['date'], data(close=89.), {1: 0}, [signal])
    assert p.positions[1].pending_since == pd.Timestamp('2008-01-03')
    assert p.exit_decisions[-1]['window'] == 150
    p.session(pd.Timestamp('2008-01-04'), pd.Timestamp('2008-01-03'),
        data(opening=80., close=82., previous=89.), {1: 0}, [])
    assert not p.positions and p.closed[-1]['reason'] == 'SMA150_EXIT'


def test_unrestricted_does_not_require_atr():
    assert eligible(500., np.nan, np.nan, None)
    assert not eligible(-1., 100., 2., None)


def test_rejected_top_candidate_allows_next_ranked_entry():
    p = GapLimitPortfolio('drift', 0, 'gap05', maximum=1)
    previous = pd.Timestamp('2008-01-02')
    candidates = [dict(event_id=sid, permno=sid, permco=10*sid, ticker=str(sid),
        date=previous, signal_close=100., atr20_prior=2.) for sid in (1, 2)]
    d = {k: np.repeat(v, 2) for k, v in data(opening=100., close=100.).items()}
    d['open'][0] = 102.
    d['company'] = np.array([10., 20.])
    p.session(pd.Timestamp('2008-01-03'), previous, d, {1: 0, 2: 1}, candidates)
    assert set(p.positions) == {2}
