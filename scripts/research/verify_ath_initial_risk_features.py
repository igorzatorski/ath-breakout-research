"""Raw SMA200 reconstruction, benchmark and calendar-summary checks for ATH30."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402


def main(path):
    path = Path(path)
    ids = np.load(path/'security_ids.npy')
    tail,checked = None,0
    for year in range(1993,2027):
        d = pd.read_parquet(ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet',
            columns=['date','permno','close','price_adjustment_factor'],filters=[('permno','in',ids.tolist())])
        d['adjusted'] = d.close/d.price_adjustment_factor
        d.loc[~np.isfinite(d.adjusted)|d.adjusted.le(0),'adjusted'] = np.nan
        calendar = valid_nyse_sessions(f'{year}-01-01',min(pd.Timestamp(f'{year}-12-31'),pd.Timestamp('2026-06-30')))
        raw = d.pivot(index='date',columns='permno',values='adjusted').reindex(index=calendar,columns=ids)
        if tail is not None:
            expected = pd.concat([tail,raw]).rolling(200,min_periods=200).mean().reindex(calendar)
            with np.load(path/f'features/{year}.npz') as z:
                assert np.allclose(expected.to_numpy(),z['sma200'],equal_nan=True)
                checked += expected.size
        tail = raw.tail(199)
    summary = pd.read_csv(path/'summary.csv')
    spy = pd.read_parquet(ROOT/'data/raw/yfinance/SPY.parquet').set_index('date')
    count = 0
    for directory in path.glob('*bps'):
        eq = pd.read_csv(directory/'equity.csv',parse_dates=['date'])
        z = spy.reindex(eq.date)
        cost = .001 if directory.name.endswith('_10bps') else 0.
        shares = 100000/(z.open.iloc[0]*(1+cost))
        expected = shares*z.close.iloc[0]*z.adj_close/z.adj_close.iloc[0]
        assert np.allclose(eq.spy_nav,expected)
        for row in summary.loc[summary.run.eq(directory.name)].itertuples():
            f = eq.loc[eq.date.between(row.start,row.end)]
            first = f.index[0]
            initial = 100000 if first==0 else eq.nav.iloc[first-1]
            curve = np.r_[initial,f.nav.to_numpy()]
            assert len(f)==row.sessions
            assert np.isclose(row.cagr,(curve[-1]/curve[0])**(252/len(f))-1)
            assert np.isclose(row.max_drawdown,(curve/np.maximum.accumulate(curve)-1).min())
            assert np.isclose(row.average_exposure,f.exposure.mean())
            count += 1
    result = dict(raw_sma200_cells=checked,calendar_summaries=count,benchmark_variants=10,passed=True)
    (path/'raw_feature_summary_verification.json').write_text(json.dumps(result,indent=2))
    print(result)


if __name__=='__main__':
    main(sys.argv[1])
