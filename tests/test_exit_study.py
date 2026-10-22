import numpy as np
import pandas as pd

from scripts.research.study_exits import simulate


def prices(opens,lows,highs,closes):
    return pd.DataFrame(dict(date=pd.bdate_range('2020-01-02',periods=len(opens)),
        a_open=opens,a_low=lows,a_high=highs,adj_close=closes,recovered=False))


def test_stop_gap_fills_at_open():
    p=prices([100,100,95],[100,99,94],[100,101,96],[100,100,95])
    _,t,_=simulate(p,{0},2,'stop2',1,0,1,2)
    assert t.iloc[0].reason=='stop'
    assert t.iloc[0].gap
    assert np.isclose(t.iloc[0].underlying_return,-.05)


def test_same_bar_stop_target_uses_stop():
    p=prices([100,100],[100,97],[100,105],[100,104])
    _,t,_=simulate(p,{0},1,'stop2_tp4',1,0,1,1)
    assert t.iloc[0].ambiguous
    assert np.isclose(t.iloc[0].underlying_return,-.02)


def test_recovery_exit_next_open():
    p=prices([100,100,103],[100,99,102],[100,102,104],[100,101,103])
    p.loc[1,'recovered']=True
    _,t,_=simulate(p,{0},2,'recovery',1,0,1,2)
    assert t.iloc[0].reason=='recovery'
    assert t.iloc[0].exit_date==p.date.iloc[2]
    assert np.isclose(t.iloc[0].underlying_return,.03)


def test_fixed_units_not_daily_reset_and_financing():
    p=prices([100,100,102],[100,99,101],[100,103,105],[100,102,104])
    _,t,_=simulate(p,{0},2,'time',5,.06,1,2)
    nights=(p.date.iloc[2]-p.date.iloc[1]).days
    expected=5*.04-5*.001-5*1.04*.001-5*.06*nights/365.25
    assert np.isclose(t.iloc[0].account_return,expected)


def test_margin_and_gap_insolvency():
    p=prices([100,100,80,100],[100,99,79,99],[100,101,81,101],[100,100,80,100])
    m,t,c=simulate(p,{0,2},2,'time',10,0,1,3)
    assert t.iloc[0].reason=='margin'
    assert m['insolvent']
    assert len(t)==1
    assert c.equity.iloc[-1]==0
