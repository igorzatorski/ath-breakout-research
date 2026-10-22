"""One-factor extensions of the frozen Z-score index study."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/zscore/v003'


def rsi(close, length=2):
    delta = close.diff().to_numpy()
    result = np.full(len(close), np.nan)
    gain = np.maximum(delta[1:length+1], 0).mean()
    loss = np.maximum(-delta[1:length+1], 0).mean()
    for i in range(length, len(close)):
        if i > length:
            gain = (gain * (length-1) + max(delta[i], 0)) / length
            loss = (loss * (length-1) + max(-delta[i], 0)) / length
        result[i] = 100 * gain / (gain+loss) if gain+loss else 50
    return pd.Series(result, index=close.index)


def prepare(raw):
    p = raw.sort_values('date').reset_index(drop=True).copy()
    if p.date.duplicated().any():
        raise ValueError('Duplicate dates')
    cols = ['open', 'high', 'low', 'close', 'adj_close']
    if not np.isfinite(p[cols]).all().all() or (p[cols] <= 0).any().any():
        raise ValueError('Invalid OHLC')
    if ((p.high < p[['open','close','low']].max(axis=1)) | (p.low > p[['open','close','high']].min(axis=1))).any():
        raise ValueError('Inconsistent OHLC')
    for col in ['open', 'high', 'low']:
        p['a_'+col] = p[col] * p.adj_close / p.close
    roll = p.close.rolling(30)
    p['z'] = (p.close-roll.mean()) / roll.std(ddof=1)
    p['rsi'] = rsi(p.adj_close)
    ret = p.adj_close.pct_change(fill_method=None)
    p['shock'] = p.adj_close.pct_change(5, fill_method=None) / (ret.rolling(60).std().shift(5)*np.sqrt(5))
    p['trend'] = p.close / p.close.rolling(200).mean() - 1
    vol = ret.rolling(20).std()
    p['vol_ratio'] = vol.shift(1) / vol.rolling(252).median().shift(1)
    for h in [1,3,5,10]:
        entry = p.a_open.shift(-1)
        p[f'r{h}'] = p.adj_close.shift(-h)/entry-1
        lows = pd.concat([p.a_low.shift(-j) for j in range(1,h+1)],axis=1)
        highs = pd.concat([p.a_high.shift(-j) for j in range(1,h+1)],axis=1)
        p[f'mae{h}'] = (lows.min(axis=1)/entry-1).clip(upper=0)
        p[f'mfe{h}'] = (highs.max(axis=1)/entry-1).clip(lower=0)
    return p


def select_nonoverlap(indices, horizon):
    selected, exit_index = [], -1
    for i in indices:
        if i >= exit_index:
            selected.append(i)
            exit_index = i+horizon
    return np.array(selected, dtype=int)


def intervals(r, signal, control, block):
    rng = np.random.default_rng(42)
    n = len(r)
    differences = []
    for _ in range(2000):
        starts = rng.integers(0,n-block+1,int(np.ceil(n/block)))
        ix = (starts[:,None]+np.arange(block)).ravel()[:n]
        a, b = r[ix][signal[ix]], r[ix][control[ix]]
        if len(a) and len(b):
            differences.append(a.mean()-b.mean())
    return np.quantile(differences,[.025,.975])


def equity(p, selected, h, first, last):
    daily = np.zeros(last-first+1)
    held = np.zeros(len(daily), bool)
    for i in selected:
        for j in range(i+1,i+h+1):
            denominator = p.a_open.iloc[j] if j == i+1 else p.adj_close.iloc[j-1]
            factor = p.adj_close.iloc[j]/denominator
            if j == i+1:
                factor *= 1-.001
            if j == i+h:
                factor *= 1-.001
            daily[j-first] = factor-1
            held[j-first] = True
    curve = np.cumprod(1+daily)
    peak = np.maximum.accumulate(np.r_[1,curve])[1:]
    years = (p.date.iloc[last]-p.date.iloc[first]).days/365.25
    return pd.DataFrame(dict(date=p.date.iloc[first:last+1].to_numpy(),equity=curve,held=held)), dict(
        cagr=curve[-1]**(1/years)-1, max_drawdown=(curve/peak-1).min(), exposure=held.mean())


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data, sources = {}, {}
    for ticker, filename in [('SPY','SPY.parquet'),('QQQ','QQQ_zscore.parquet')]:
        path = ROOT/'data/raw/yfinance'/filename
        data[ticker] = prepare(pd.read_parquet(path))
        sources[ticker] = dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    dates = None
    for p in data.values():
        valid = p[['z','rsi','shock','trend','vol_ratio','r10']].notna().all(axis=1)
        ds = pd.Index(p.loc[valid,'date'])
        dates = ds if dates is None else dates.intersection(ds)
    rows, cis, portfolios, ledgers = [], [], [], []
    for ticker,p in data.items():
        d = p[p.date.isin(dates)].copy()
        base = d.z <= -2
        previous_z = p.z.shift(1).loc[d.index]
        all_days = np.ones(len(d),bool)
        variants = [(f'hold_{h}',h,base,all_days) for h in [1,3,5,10]]
        variants += [('trend_above',5,base & (d.trend>=0),d.trend>=0),
                     ('trend_below',5,base & (d.trend<0),d.trend<0),
                     ('vol_low',5,base & (d.vol_ratio<=1),d.vol_ratio<=1),
                     ('vol_high',5,base & (d.vol_ratio>1),d.vol_ratio>1),
                     ('first_cross',5,base & (previous_z>-2),all_days),
                     ('recovery',5,(d.z>-2)&(previous_z<=-2),all_days),
                     ('rsi2_10',5,d.rsi<=10,all_days),
                     ('shock5_minus2',5,d.shock<=-2,all_days)]
        first, last = d.index.min()+1, d.index.max()+10
        bh = p.adj_close.iloc[first:last+1]/p.a_open.iloc[first]
        bh_peak = np.maximum.accumulate(np.r_[1,bh])[1:]
        years = (p.date.iloc[last]-p.date.iloc[first]).days/365.25
        portfolios.append(dict(ticker=ticker,variant='buy_hold',n=1,cagr=bh.iloc[-1]**(1/years)-1,max_drawdown=(bh/bh_peak-1).min(),exposure=1))
        for name,h,signal,control in variants:
            signal,control = np.asarray(signal),np.asarray(control)
            selected = select_nonoverlap(d.index[signal],h)
            eq, metrics = equity(p,selected,h,first,last)
            expected = np.prod((1+p.loc[selected,f'r{h}'])*(.999**2))
            assert np.isclose(eq.equity.iloc[-1],expected), 'Trade/equity reconciliation'
            eq.to_csv(OUT/f'{ticker}_{name}_equity.csv',index=False)
            portfolios.append(dict(ticker=ticker,variant=name,n=len(selected),**metrics))
            for block in [20,60]:
                low,high = intervals(d[f'r{h}'].to_numpy(),signal,control,block)
                cis.append(dict(ticker=ticker,variant=name,block=block,low=low,high=high))
            for sample,ix in [('all',d.index[signal]),('nonoverlap',selected),('control',d.index[control])]:
                x = p.loc[ix].copy()
                if sample != 'control':
                    ledger = x[['date',f'r{h}',f'mae{h}',f'mfe{h}']].copy()
                    ledger.columns = ['signal_date','gross_return','mae','mfe']
                    ledger['entry_date'] = p.date.shift(-1).loc[ix].to_numpy()
                    ledger['exit_date'] = p.date.shift(-h).loc[ix].to_numpy()
                    ledger['ticker'],ledger['variant'],ledger['sample'] = ticker,name,sample
                    ledgers.append(ledger)
                for period,mask in [('full',np.ones(len(x),bool)),('1999-2009',x.date.dt.year<=2009),('2010-2017',x.date.dt.year.between(2010,2017)),('2018-end',x.date.dt.year>=2018)]:
                    part=x.loc[mask]
                    r=part[f'r{h}']
                    rows.append(dict(ticker=ticker,variant=name,horizon=h,sample=sample,period=period,n=len(r),
                        mean=r.mean(),median=r.median(),win_rate=(r>0).mean(),avg_win=r[r>0].mean(),avg_loss=r[r<0].mean(),sd=r.std(),
                        p05=r.quantile(.05),worst=r.min(),mae_median=part[f'mae{h}'].median(),mae_p05=part[f'mae{h}'].quantile(.05),mfe_median=part[f'mfe{h}'].median(),
                        net10=((1+r)*(.9995**2)-1).mean(),net20=((1+r)*(.999**2)-1).mean(),net40=((1+r)*(.998**2)-1).mean()))
    summary,ci,portfolio = pd.DataFrame(rows),pd.DataFrame(cis),pd.DataFrame(portfolios)
    summary.to_csv(OUT/'summary.csv',index=False)
    ci.to_csv(OUT/'intervals.csv',index=False)
    portfolio.to_csv(OUT/'portfolio.csv',index=False)
    pd.concat(ledgers).to_csv(OUT/'events.csv',index=False)
    (OUT/'manifest.json').write_text(json.dumps(dict(sources=sources,signal_start=str(dates.min()),signal_end=str(dates.max()),common_dates=len(dates),bootstrap_draws=2000,blocks=[20,60],seed=42,plan='research/zscore/EXTENDED_PLAN.md'),indent=2),encoding='utf-8')
    report = '# Extended mean-reversion research\n\nExploratory, pointwise intervals; no multiple-testing correction. See EXTENDED_PLAN.md.\n\n'
    report += f'Common signal dates: {dates.min().date()} to {dates.max().date()}, N={len(dates)}.\n\n'
    for title,frame in [('All signal days',summary.query("period=='full' and sample=='all'")),('Non-overlapping trades',summary.query("period=='full' and sample=='nonoverlap'")),('Period stability',summary.query("period!='full' and sample=='nonoverlap'")),('Bootstrap excess over matched control',ci),('Stylized ETF portfolios',portfolio)]:
        report += f'## {title}\n\n'+frame.to_markdown(index=False,floatfmt='.5f')+'\n\n'
    (ROOT/'research/zscore/EXTENDED_RESULTS.md').write_text(report,encoding='utf-8')
    print(summary.query("period=='full' and sample=='nonoverlap'")[['ticker','variant','n','mean','win_rate','net20','worst','mae_median']].to_string(index=False))
    print(portfolio.to_string(index=False))


if __name__ == '__main__':
    main()
