import numpy as np
import pandas as pd

from scripts.research.study_mean_reversion import equity, prepare, rsi, select_nonoverlap


def fixture():
    c = 100 + np.arange(400)*.03 + 3*np.sin(np.arange(400)/4)
    return pd.DataFrame(dict(date=pd.bdate_range('2000-01-01',periods=400),
        open=c-.2,high=c+1,low=c-1,close=c,adj_close=c*.8))


def test_signal_prefix_invariance():
    raw=fixture()
    a=prepare(raw)
    raw.loc[351:,['open','high','low','close','adj_close']] *= 4
    b=prepare(raw)
    pd.testing.assert_frame_equal(a.loc[:350,['z','rsi','shock','trend','vol_ratio']],b.loc[:350,['z','rsi','shock','trend','vol_ratio']])


def test_rsi_wilder_seed_and_recursion():
    actual=rsi(pd.Series([100.,102.,101.,100.]))
    assert np.isclose(actual.iloc[2],100*1/1.5)
    assert np.isclose(actual.iloc[3],100*.5/1.25)


def test_path_extremes_and_forward_return():
    raw=fixture()
    p=prepare(raw)
    entry=raw.open.iloc[301]*.8
    assert np.isclose(p.r5.iloc[300],raw.adj_close.iloc[305]/entry-1)
    assert np.isclose(p.mae5.iloc[300],min(0,raw.low.iloc[301:306].min()*.8/entry-1))
    assert np.isclose(p.mfe5.iloc[300],max(0,raw.high.iloc[301:306].max()*.8/entry-1))


def test_equity_includes_held_overnight_gap_and_costs():
    p=pd.DataFrame(dict(date=pd.bdate_range('2000-01-01',periods=4),
        a_open=[100.,100.,80.,100.],adj_close=[100.,100.,90.,100.]))
    eq,_=equity(p,np.array([0]),2,1,3)
    assert np.isclose(eq.equity.iloc[-1],.9*.999**2)
    assert eq.held.sum()==2
    assert eq.equity.iloc[-1]==eq.equity.iloc[-2]
    np.testing.assert_array_equal(select_nonoverlap([0,1,2,4,5],2),[0,2,4])
