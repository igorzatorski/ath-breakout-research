"""Threshold timing, persistence, anchor and reentry tests for stepped exits."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/research'))
from stepped_sma import SteppedPortfolio  # noqa: E402


def rows(close=100., opening=100., prior=100., smas=(70., 80., 90.)):
    d = {k: np.array([v]) for k, v in dict(open=opening, close=close,
        previous_close=prior, dividend=0., terminal=False, observed=True, company=10).items()}
    d['return'] = np.array([close / prior - 1])
    for window, value in zip((150, 100, 50), smas):
        d[f'sma{window}'] = np.array([value])
    d['sma'] = d['sma50']
    return d


def day(p, date, previous, data, entry=False):
    candidates = [dict(permno=1, permco=10, ticker='A', date=pd.Timestamp(previous))] if entry else []
    p.session(pd.Timestamp(date), pd.Timestamp(previous), data, {1: 0}, candidates)


def test_equality_permanent_stage_and_next_open():
    p = SteppedPortfolio('drift', 10, 'step50_100')
    day(p, '2008-01-03', '2008-01-02', rows(), True)
    day(p, '2008-01-04', '2008-01-03', rows(150., prior=100.))
    assert p.stages[1] == 1
    day(p, '2008-01-07', '2008-01-04', rows(110., prior=150.))
    assert p.stages[1] == 1
    day(p, '2008-01-08', '2008-01-07', rows(200., prior=110.))
    assert p.stages[1] == 2
    day(p, '2008-01-09', '2008-01-08', rows(90., prior=200.))
    assert p.positions[1].pending_since is None
    day(p, '2008-01-10', '2008-01-09', rows(89., prior=90.))
    assert p.exit_decisions[-1]['window'] == 50
    assert 1 in p.positions
    day(p, '2008-01-11', '2008-01-10', rows(80., opening=80., prior=89.))
    assert 1 not in p.positions and 1 not in p.stages
    assert p.closed[-1]['reason'] == 'SMA50_EXIT'


def test_entry_day_jump_two_stages_and_same_close_trigger():
    p = SteppedPortfolio('drift', 0, 'step50_100')
    day(p, '2008-01-03', '2008-01-02', rows(200., smas=(70., 80., 201.)), True)
    assert p.stages[1] == 2
    assert p.exit_decisions[-1]['sma'] == 201.
    assert p.positions[1].pending_since == pd.Timestamp('2008-01-03')
    assert len(p.closed) == 0


def test_shorter_sma_can_be_lower_and_reentry_resets_stage():
    p = SteppedPortfolio('drift', 0, 'step50_100')
    day(p, '2008-01-03', '2008-01-02', rows(150., smas=(140., 130., 120.)), True)
    assert p.transitions[-1]['numerically_lower']
    day(p, '2008-01-04', '2008-01-03', rows(110., prior=150., smas=(90., 120., 125.)))
    day(p, '2008-01-07', '2008-01-04', rows(105., opening=100., prior=110.), True)
    assert p.entry_prices[1] == 100.
    assert p.stages[1] == 0
    assert p.positions[1].pending_since is None


def test_monthly_buy_preserves_anchor_and_stage():
    p = SteppedPortfolio('monthly_equal', 0, 'step50_100')
    day(p, '2008-01-30', '2008-01-29', rows(150.), True)
    assert p.stages[1] == 1
    day(p, '2008-01-31', '2008-01-30', rows(90., prior=150.))
    day(p, '2008-02-01', '2008-01-31', rows(90., opening=90., prior=90.))
    assert any(t['kind'] == 'REBAL_BUY' for t in p.transactions)
    assert p.entry_prices[1] == 100. and p.stages[1] == 1


def test_missing_selected_sma_does_not_fall_back():
    p = SteppedPortfolio('drift', 0, 'step50_100')
    day(p, '2008-01-03', '2008-01-02', rows(150., smas=(160., np.nan, 170.)), True)
    assert p.stages[1] == 1 and p.positions[1].pending_since is None
    assert p.missing_trend_days == 1


def test_decimal_fifty_percent_equality_activates_on_same_close():
    p = SteppedPortfolio('drift', 0, 'step50_100')
    day(p, '2008-01-03', '2008-01-02',
        rows(96.3, opening=64.2, prior=64.2, smas=(50., 60., 70.)), True)
    assert p.stages[1] == 1
    assert p.transitions[-1]['date'] == pd.Timestamp('2008-01-03')
