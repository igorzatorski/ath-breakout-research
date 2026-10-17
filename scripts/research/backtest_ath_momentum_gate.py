"""ATH38: six maxima, original gain stages and clean 2008 start."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from stepped_sma import SteppedPortfolio as RiskTrendPortfolio  # noqa: E402
from prepare_ath_momentum_gate import RULES  # noqa: E402
from ath_breakout.research.sma50_portfolio import performance  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402
from backtest_ath_sma50_portfolio import benchmark  # noqa: E402

SOURCE = ROOT/'outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z'
FEATURE_SOURCE = ROOT/'outputs/backtests/ath_30_initial_risk_trend_v001/20261017T154917914966Z'


def main():
    out = Path(sys.argv[1]).resolve()
    (out/'panels').mkdir(exist_ok=True)
    (out/'features').mkdir(exist_ok=True)
    prepared = json.loads((out/'preparation.json').read_text())
    inputs = dict(prepared['inputs'])
    print('BACKTEST:',out,flush=True)
    signals = pd.read_parquet(out/'signals.parquet')
    assert signals.event_id.is_unique
    by_date = {(label,date):f.to_dict('records') for (label,date),f in signals.groupby(['definition','date'],sort=False)}
    ids = np.load(out/'security_ids.npy')
    index = {int(sid):i for i,sid in enumerate(ids)}
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    tail = None
    states = {}
    for rule in RULES:
        for policy in ['drift','monthly_equal']:
            states[f'{rule}__{policy}_10bps'] = RiskTrendPortfolio(policy,10,'step50_100')
    assert all(s.cash==100000. and not s.positions and not s.entry_prices and not s.pending_reasons for s in states.values())
    previous_date = pd.Timestamp('2007-12-31')
    for year in range(2007,2027):
        raw_path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        digest = sha256(raw_path)
        assert digest==inputs[str(raw_path.relative_to(ROOT))]
        columns = ['permno','permco','date','open','close','price_adjustment_factor','ordinary_dividend',
            'nonordinary_dividend','total_return','delisting_flag','period_price_factor']
        d = pd.read_parquet(raw_path,columns=columns,filters=[('permno','in',ids.tolist())])
        factor = d.price_adjustment_factor.where(np.isfinite(d.price_adjustment_factor)&d.price_adjustment_factor.gt(0))
        d['c'] = (d.close/factor).where(np.isfinite(d.close)&d.close.gt(0))
        d['o'] = (d.open/factor).where(np.isfinite(d.open)&d.open.gt(0))
        distribution_factor = factor*d.period_price_factor
        d['div'] = (d.ordinary_dividend+d.nonordinary_dividend)/distribution_factor
        terminal = d.delisting_flag.eq('Y')
        ordinary = (d.ordinary_dividend/distribution_factor).where(d.ordinary_dividend.ne(0),0.)
        d.loc[terminal,'div'] = ordinary.loc[terminal]
        dates = valid_nyse_sessions(f'{year}-01-01',min(pd.Timestamp(f'{year}-12-31'),pd.Timestamp('2026-06-30')))
        def pivot(col):
            return d.pivot(index='date',columns='permno',values=col).reindex(index=dates,columns=ids)
        close = pivot('c')
        if tail is None:
            tail = close.tail(149)
            continue
        complete = pd.concat([tail,close])
        features = {f'sma{w}':complete.rolling(w,min_periods=w).mean().reindex(dates).to_numpy() for w in [50,100,150]}
        d['terminal'],d['observed'] = terminal,True
        panel = dict(open=pivot('o').to_numpy(),close=close.to_numpy(),dividend=pivot('div').to_numpy(),
            company=pivot('permco').to_numpy(),terminal=pivot('terminal').eq(True).to_numpy(),
            observed=pivot('observed').eq(True).to_numpy(),previous_close=complete.shift(1).reindex(dates).to_numpy(),
            sma=features['sma50'])
        panel['return'] = pivot('total_return').to_numpy()
        np.savez_compressed(out/f'panels/{year}.npz',dates=dates.to_numpy(),**panel)
        np.savez_compressed(out/f'features/{year}.npz',dates=dates.to_numpy(),**features)
        panel.update(features)
        tail = close.tail(149)
        for i,date in enumerate(dates):
            rows = {k:v[i] for k,v in panel.items()}
            for name,state in states.items():
                candidates = by_date.get((name.split('__')[0],previous_date),[])
                state.session(date,previous_date,rows,index,candidates)
            previous_date = date
        print(f'Year{year}: '+', '.join(f'{n}={p.nav():.0f}' for n,p in states.items() if n.endswith('drift_10bps')),flush=True)
    sessions = valid_nyse_sessions('2008-01-02','2026-06-30')
    spy_path = ROOT/'data/raw/yfinance/SPY.parquet'
    assert sha256(spy_path)==manifest['inputs'][str(spy_path.relative_to(ROOT))]
    inputs[str(spy_path.relative_to(ROOT))]=sha256(spy_path)
    stats, boundary_checks = [], {}
    for name,state in states.items():
        directory = out/name
        directory.mkdir()
        eq = pd.DataFrame(state.equity)
        holdings = pd.DataFrame(state.holdings)
        tx = pd.DataFrame(state.transactions)
        closed = pd.DataFrame(state.closed)
        opened = state.ending_positions()
        spy_curve,spy_returns = benchmark(spy_path,sessions,state.rate*10000)
        eq['spy_nav'],eq['spy_return'] = spy_curve.to_numpy(),spy_returns.to_numpy()
        eq['drawdown'] = eq.nav/np.maximum.accumulate(np.r_[state.initial,eq.nav])[1:]-1
        assert tx.date.ge('2008-01-02').all()
        assert closed.entry_date.ge('2008-01-02').all()
        assert opened.entry_date.ge('2008-01-02').all()
        entries = tx.loc[tx.kind.eq('ENTRY')]
        assert entries.quantity_before.eq(0).all()
        assert entries.decision_date.ge('2007-12-31').all()
        boundary_checks[name] = dict(initial_cash=100000.,inherited_positions=0,pending_pre2008_orders=0,
            first_entry=str(entries.date.min().date()),earliest_signal=str(entries.decision_date.min().date()),passed=True)
        eq.to_csv(directory/'equity.csv',index=False)
        tx.to_parquet(directory/'transactions.parquet',index=False)
        closed.to_csv(directory/'closed_positions.csv',index=False)
        opened.to_csv(directory/'open_positions.csv',index=False)
        holdings.to_parquet(directory/'holdings.parquet',index=False)
        pd.DataFrame(state.transitions,columns=['date','permno','entry_price','close','prior_stage','stage','previous_sma','selected_sma','numerically_lower']).to_parquet(directory/'transitions.parquet',index=False)
        pd.DataFrame(state.exit_decisions).to_parquet(directory/'exit_decisions.parquet',index=False)
        pd.DataFrame(state.skips).to_csv(directory/'skips.csv',index=False)
        pnl = closed.pnl.sum()+opened.unrealized_total_pnl.sum()
        assert np.isclose(pnl,state.nav()-state.initial,atol=max(1e-5,state.nav()*1e-10))
        audit = dict(rule=name.split('__')[0],policy=state.policy,cost_bps=state.rate*10000,
            missing_trend_position_days=state.missing_trend_days,stale_position_days=state.stale_marks,
            deferred_exit_days=state.deferred_exits,fees=state.fees,weight_resets=state.rebalance_count,
            held_return_checks=state.return_checks,max_return_error=state.max_return_error,
            final_nav=state.nav(),cashflow_pnl=pnl,closed_positions=len(closed),open_positions=len(opened),
            floor_anchor='first actual entry opening; unchanged by rebalance')
        (directory/'accounting_audit.json').write_text(json.dumps(audit,indent=2))
        periods = [('all',eq),('2008_2017',eq.loc[eq.date.dt.year.le(2017)]),
            ('2018_2022',eq.loc[eq.date.dt.year.between(2018,2022)]),('2018_end',eq.loc[eq.date.dt.year.ge(2018)]),
            ('2021_2022',eq.loc[eq.date.dt.year.between(2021,2022)]),
            ('2023_end',eq.loc[eq.date.dt.year.ge(2023)]),*[(str(y),f) for y,f in eq.groupby(eq.date.dt.year)]]
        for period,f in periods:
            start_index = f.index[0]
            initial = state.initial if start_index==0 else eq.nav.iloc[start_index-1]
            benchmark_initial = state.initial if start_index==0 else eq.spy_nav.iloc[start_index-1]
            reference = pd.DataFrame(dict(nav=f.spy_nav,daily_return=f.spy_return,exposure=1.,positions=1.))
            a,b = performance(f,initial),performance(reference,benchmark_initial)
            stats.append(dict(run=name,rule=name.split('__')[0],policy=state.policy,cost_bps=state.rate*10000,
                period=period,start=str(f.date.min().date()),end=str(f.date.max().date()),**a,
                spy_cagr=b['cagr'],spy_max_drawdown=b['max_drawdown'],cagr_gap=a['cagr']-b['cagr'],
                maximum_weight=holdings.loc[holdings.date.between(f.date.min(),f.date.max()),'weight'].max()))
        print('Saved',name,flush=True)
    summary = pd.DataFrame(stats)
    summary.to_csv(out/'summary.csv',index=False)
    (out/'clean_boundary_checks.json').write_text(json.dumps(boundary_checks,indent=2))
    code = [Path(__file__),ROOT/'scripts/research/stepped_sma.py',ROOT/'scripts/research/prepare_ath_momentum_gate.py',ROOT/'src/ath_breakout/research/initial_risk_trend.py',ROOT/'src/ath_breakout/research/sma50_portfolio.py',ROOT/'scripts/research/backtest_ath_sma50_portfolio.py']
    result = dict(study_id='ath_39_momentum_gate_v001',source=str(SOURCE.relative_to(ROOT)),inputs=inputs,
        feature_source='raw split-adjusted close; 149-session warmup',start='2008-01-02',end='2026-06-30',initial_cash=100000.,inherited_positions=0,
        protocol_sha256=sha256(ROOT/'research/ath/ATH_MOMENTUM_GATE_PLAN.md'),
        code={str(p.relative_to(ROOT)):sha256(p) for p in code},
        artifacts={str(p.relative_to(out)):sha256(p) for p in out.rglob('*') if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    print(summary.loc[summary.period.eq('all')].to_string(index=False),flush=True)
    print(out,flush=True)


if __name__=='__main__':
    main()
