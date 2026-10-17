import numpy as np
import pandas as pd

from ath_breakout.research.initial_risk_trend import RiskTrendPortfolio


def test_preboundary_indicator_context_never_imports_positions_or_anchors():
    p=RiskTrendPortfolio('drift',10,'floor5_sma200')
    data={k:np.array([v]) for k,v in {'open':100.,'close':95.,'sma':110.,'sma200':120.,
        'previous_close':140.,'return':95/140-1,'dividend':0.,'terminal':False,'observed':True,'company':10}.items()}
    p.session(pd.Timestamp('2008-01-02'),pd.Timestamp('2007-12-31'),data,{1:0},[])
    assert p.cash==100000. and p.nav()==100000. and not p.positions
    assert not p.entry_prices and not p.pending_reasons and not p.transactions
    data.update(open=np.array([100.]),close=np.array([101.]),sma=np.array([90.]),sma200=np.array([80.]))
    p.session(pd.Timestamp('2008-01-03'),pd.Timestamp('2008-01-02'),data,{1:0},
        [dict(permno=1,permco=10,ticker='A',date=pd.Timestamp('2008-01-02'))])
    assert p.positions[1].entry_date==pd.Timestamp('2008-01-03')
    assert p.entry_prices[1]==100.
