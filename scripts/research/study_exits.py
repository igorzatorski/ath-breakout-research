"""Stylized fixed-unit CFD exit/sizing scenarios, not broker execution forecasts."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.research.study_mean_reversion import prepare

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/zscore/v004'
RULES={'time':(None,None,False),'stop1':(.01,None,False),
       'stop2':(.02,None,False),'stop3':(.03,None,False),'stop5':(.05,None,False),
       'tp2':(None,.02,False),'tp4':(None,.04,False),
       'recovery':(None,None,True),'stop2_tp4':(.02,.04,False)}


def simulate(p,signal,h,rule,exposure,rate,first,last):
    stop,tp,recovery=RULES[rule]
    cash=1.; active=None; trades=[]; daily=[]
    for j in range(first,last+1):
        o,lo,hi,c=(float(p[col].iloc[j]) for col in ['a_open','a_low','a_high','adj_close'])
        if active is None and cash>0 and j-1 in signal:
            active=dict(start=j,entry=o,equity=cash,notional=cash*exposure,units=cash*exposure/o)
        if active is not None:
            a=active
            nights=(p.date.iloc[j]-p.date.iloc[a['start']]).days
            fees=a['notional']*.001
            funding=a['notional']*rate*nights/365.25
            # Solve net liquidation equity at price x = half initial margin.
            floor=a['notional']*.025
            barrier=(floor-a['equity']+a['notional']+fees+funding)/(a['units']*.999)
            stop_price=a['entry']*(1-stop) if stop else -np.inf
            lower=max(stop_price,barrier)
            lower_reason='margin' if barrier>=stop_price else 'stop'
            target=a['entry']*(1+tp) if tp else np.inf
            pending=(recovery and j>a['start'] and bool(p.recovered.iloc[j-1]))
            reason=None; price=None; ambiguous=False; gap=False
            if o<=lower:
                price,reason,gap=o,lower_reason,True
            elif pending:
                price,reason=o,'recovery'
            elif o>=target:
                price,reason=o,'target'
            elif lo<=lower:
                price,reason=lower,lower_reason
                ambiguous=hi>=target
            elif hi>=target:
                price,reason=target,'target'
            elif j==a['start']+h-1:
                price,reason=c,'time'
            if reason:
                ending=a['equity']+a['units']*(price-a['entry'])-fees-funding-a['units']*price*.001
                trades.append(dict(entry_date=p.date.iloc[a['start']],exit_date=p.date.iloc[j],
                    account_return=ending/a['equity']-1,underlying_return=price/a['entry']-1,
                    reason=reason,gap=gap,ambiguous=ambiguous,negative_balance=ending<0,
                    nights=nights,exposure=exposure))
                cash=max(0.,ending); active=None
                mark=cash
            else:
                mark=a['equity']+a['units']*(c-a['entry'])-fees-funding
        else:
            mark=cash
        daily.append(dict(date=p.date.iloc[j],equity=mark))
    ledger=pd.DataFrame(trades)
    curve=pd.DataFrame(daily)
    peak=np.maximum.accumulate(np.r_[1.,curve.equity])[1:]
    years=(p.date.iloc[last]-p.date.iloc[first]).days/365.25
    metrics=dict(n=len(ledger),cagr=curve.equity.iloc[-1]**(1/years)-1 if years>0 else np.nan,
        max_drawdown=(curve.equity/peak-1).min(),mean=ledger.account_return.mean(),
        win_rate=(ledger.account_return>0).mean(),worst=ledger.account_return.min(),
        margin_exits=(ledger.reason=='margin').sum(),gap_exits=ledger.gap.sum(),
        ambiguous=ledger.ambiguous.sum(),insolvent=ledger.negative_balance.any(),final_equity=curve.equity.iloc[-1])
    return metrics,ledger,curve


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    old=json.loads((ROOT/'outputs/zscore/v003/manifest.json').read_text())
    summaries=[]; all_trades=[]; periods=[]; sources={}
    for ticker,filename in [('SPY','SPY.parquet'),('QQQ','QQQ_zscore.parquet')]:
        path=ROOT/'data/raw/yfinance'/filename
        sources[ticker]=hashlib.sha256(path.read_bytes()).hexdigest()
        p=prepare(pd.read_parquet(path))
        eligible=p.date.between(old['signal_start'],old['signal_end'])
        p['recovered']=(p.rsi>=50) if ticker=='SPY' else (p.z>=0)
        signals=set(p.index[eligible & ((p.rsi<=10) if ticker=='SPY' else (p.z<=-2))])
        first=p.index[eligible].min()+1; last=p.index[eligible].max()+10
        for h in ([5] if ticker=='SPY' else [5,10]):
            for rule in RULES:
                for exposure in [.25,1,5,10]:
                    for rate in ([0,.03,.06,.09] if rule in ['time','stop2','recovery'] else [.06]):
                        metrics,ledger,curve=simulate(p,signals,h,rule,exposure,rate,first,last)
                        spec=dict(ticker=ticker,horizon=h,rule=rule,exposure=exposure,financing=rate)
                        summaries.append(dict(**spec,**metrics))
                        for k,v in spec.items():
                            ledger[k]=v
                        all_trades.append(ledger)
                        for name,mask in [('2000-2009',ledger.entry_date.dt.year<=2009),('2010-2017',ledger.entry_date.dt.year.between(2010,2017)),('2018-end',ledger.entry_date.dt.year>=2018)]:
                            x=ledger.loc[mask,'account_return']
                            periods.append(dict(**spec,period=name,n=len(x),mean=x.mean(),win_rate=(x>0).mean()))
                        key=f'{ticker}_{h}_{rule}_{exposure}_{rate}'
                        curve.to_csv(OUT/f'{key}_equity.csv',index=False)
    summary=pd.DataFrame(summaries)
    summary.to_csv(OUT/'summary.csv',index=False)
    pd.concat(all_trades).to_csv(OUT/'trades.csv',index=False)
    pd.DataFrame(periods).to_csv(OUT/'periods.csv',index=False)
    (OUT/'manifest.json').write_text(json.dumps(dict(sources=sources,plan='research/zscore/EXITS_PLAN.md',signal_start=old['signal_start'],signal_end=old['signal_end'],scenarios=len(summary)),indent=2))
    report='# Exit and sizing scenarios\n\nStylized CFD proxy; see EXITS_PLAN.md. All account returns include costs and financing.\n\n'
    for name,x in [('Base financing 6%',summary[summary.financing==.06]),('Financing sensitivity',summary[summary.rule.isin(['time','stop2','recovery'])])]:
        report+=f'## {name}\n\n'+x.to_markdown(index=False,floatfmt='.5f')+'\n\n'
    (ROOT/'research/zscore/EXITS_RESULTS.md').write_text(report,encoding='utf-8')
    print(summary.query('financing==.06 and exposure==1').to_string(index=False))
    print(summary.query("financing==.06 and rule=='time'").to_string(index=False))


if __name__=='__main__':
    main()
