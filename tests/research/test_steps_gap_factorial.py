"""Combined entry cap and early gain stages remain separable."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/research'))
from steps_gap_factorial import FactorialPortfolio  # noqa: E402


def data(opening, close, smas=(90., 110., 120.)):
    d = {k: np.array([v]) for k, v in dict(open=opening, close=close, previous_close=100.,
        dividend=0., terminal=False, observed=True, company=10).items()}
    for window, value in zip([150, 100, 50], smas):
        d[f'sma{window}'] = np.array([value])
    d['sma'], d['return'] = d['sma50'], np.array([close/100-1])
    return d


def enter(p, opening, close):
    signal = dict(event_id=1, permno=1, permco=10, ticker='A', date=pd.Timestamp('2008-01-02'),
        signal_close=100., atr20_prior=2.)
    p.session(pd.Timestamp('2008-01-03'), signal['date'], data(opening, close), {1: 0}, [signal])


def test_gap_rejection_precedes_gain_stage_processing():
    p = FactorialPortfolio('drift', 10, 'combined')
    enter(p, 102., 200.)
    assert not p.positions and not p.transitions
    assert not p.entry_screens[-1]['eligible']


def test_combined_fills_cap_equality_and_activates_early_stage():
    p = FactorialPortfolio('drift', 10, 'combined')
    enter(p, 101., 151.5)
    assert p.stages[1] == 2 and p.entry_screens[-1]['eligible']
    assert p.entry_prices[1] == 101.


def test_same_fill_constant_control_does_not_activate_stages():
    p = FactorialPortfolio('drift', 10, 'gap')
    enter(p, 101., 151.5)
    assert p.stages[1] == 0 and not p.transitions
