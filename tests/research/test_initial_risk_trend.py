import numpy as np
import pandas as pd

from ath_breakout.research.initial_risk_trend import RiskTrendPortfolio


def rows(opening=100., close=100., sma50=90., sma200=80., previous=100., ret=0.):
    return {k:np.array([v]) for k,v in dict(open=opening,close=close,sma=sma50,sma200=sma200,
        previous_close=previous,return_=ret,dividend=0.,terminal=False,observed=True,company=10).items()} | {'return': np.array([ret])}


def signal(date):
    return dict(permno=1,permco=10,ticker='A',date=pd.Timestamp(date))


def day(p, date, previous, data, entry=False):
    p.session(pd.Timestamp(date),pd.Timestamp(previous),data,{1:0},[signal(previous)] if entry else [])


def test_fixed_floor_strict_equality_then_gap_next_open():
    p = RiskTrendPortfolio('drift',10,'floor5_sma200')
    day(p,'2000-01-04','2000-01-03',rows(close=95.),True)
    assert p.positions[1].pending_since is None
    day(p,'2000-01-05','2000-01-04',rows(close=94.,previous=95.,ret=94/95-1))
    assert p.exit_decisions[-1]['reason']=='INITIAL_5_EXIT'
    day(p,'2000-01-06','2000-01-05',rows(opening=80.,close=82.,previous=94.,ret=82/94-1))
    assert p.closed[-1]['reason']=='INITIAL_5_EXIT'
    assert p.closed[-1]['cashflow_profit_ratio'] < -.2


def test_longer_trend_does_not_sell_at_sma50_break():
    p = RiskTrendPortfolio('drift',0,'floor5_sma200')
    day(p,'2000-01-04','2000-01-03',rows(close=120.,sma50=125.,sma200=90.),True)
    assert p.positions[1].pending_since is None
    day(p,'2000-01-05','2000-01-04',rows(close=110.,previous=120.,ret=110/120-1,sma200=115.))
    assert p.exit_decisions[-1]['reason']=='SMA200_EXIT'


def test_monthly_buy_preserves_original_anchor_and_missing_trend_keeps_floor():
    p = RiskTrendPortfolio('monthly_equal',0,'floor5_sma200')
    day(p,'2000-01-31','2000-01-28',rows(),True)
    day(p,'2000-02-01','2000-01-31',rows(opening=110.,close=110.,ret=.1))
    assert p.entry_prices[1]==100.
    day(p,'2000-02-02','2000-02-01',rows(close=94.,previous=110.,ret=94/110-1,sma200=np.nan))
    assert p.exit_decisions[-1]['floor']==95.
    assert p.exit_decisions[-1]['reason']=='INITIAL_5_EXIT'
    assert p.missing_trend_days==1


def test_both_triggers_and_terminal_no_extra_exit():
    p = RiskTrendPortfolio('drift',0,'floor5_sma50')
    day(p,'2000-01-04','2000-01-03',rows(close=94.,sma50=96.),True)
    assert p.exit_decisions[-1]['reason']=='BOTH_EXIT'
    d=rows(opening=np.nan,close=np.nan,previous=94.,ret=-.5)
    d['terminal']=np.array([True])
    day(p,'2000-01-05','2000-01-04',d)
    assert p.closed[-1]['reason']=='CIZ_TERMINAL'
    assert not p.entry_prices and not p.pending_reasons


def test_same_open_exit_and_reentry_uses_new_anchor_not_previous_floor():
    p = RiskTrendPortfolio('drift',0,'floor5_sma200')
    day(p,'2000-01-04','2000-01-03',rows(close=94.),True)
    day(p,'2000-01-05','2000-01-04',rows(opening=90.,close=89.,previous=94.,ret=89/94-1),True)
    assert p.entry_prices[1]==90.
    assert p.positions[1].pending_since is None
    assert len(p.exit_decisions)==1
