"""The selected SMA alone controls the close trigger and next-open exit."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/research'))
from sma_exit_grid import SMAExitPortfolio, WINDOWS  # noqa: E402


@pytest.mark.parametrize('window', WINDOWS)
def test_selected_window_strict_trigger_and_next_open(window):
    p = SMAExitPortfolio('drift', 10, f'sma{window}')
    previous = pd.Timestamp('2008-01-02')
    date = pd.Timestamp('2008-01-03')
    candidate = dict(permno=1, permco=10, ticker='A', date=previous)

    def rows(close, opening, prior):
        d = {k: np.array([v]) for k, v in dict(
            open=opening, close=close, previous_close=prior,
            dividend=0., terminal=False, observed=True, company=10).items()}
        d['return'] = np.array([close / prior - 1])
        for w in WINDOWS:
            d[f'sma{w}'] = np.array([100. if w == window else 110.])
        d['sma'] = d['sma50']
        return d

    p.session(date, previous, rows(100., 100., 100.), {1: 0}, [candidate])
    assert p.positions[1].pending_since is None
    p.session(pd.Timestamp('2008-01-04'), date, rows(99., 100., 100.), {1: 0}, [])
    assert p.exit_decisions[-1]['reason'] == f'SMA{window}_EXIT'
    assert p.exit_decisions[-1]['window'] == window
    assert 1 in p.positions
    p.session(pd.Timestamp('2008-01-07'), pd.Timestamp('2008-01-04'),
              rows(80., 80., 99.), {1: 0}, [])
    assert 1 not in p.positions
    assert p.closed[-1]['reason'] == f'SMA{window}_EXIT'
    assert p.closed[-1]['cashflow_profit_ratio'] < -.19
