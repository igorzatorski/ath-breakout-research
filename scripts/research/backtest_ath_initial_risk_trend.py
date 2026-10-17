"""ATH30: frozen original-entry floor and long-trend portfolio comparison."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.initial_risk_trend import RULES, RiskTrendPortfolio  # noqa: E402
from ath_breakout.research.sma50_portfolio import performance  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402
from backtest_ath_sma50_portfolio import benchmark  # noqa: E402

SOURCE = ROOT/'outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z'


def main():
    out = ROOT/f'outputs/backtests/ath_30_initial_risk_trend_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    (out/'features').mkdir(parents=True)
    print(out,flush=True)
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    hashes = {k.replace('\\','/'):v for k,v in manifest['artifacts'].items()}
    inputs = {str((SOURCE/'manifest.json').relative_to(ROOT)):sha256(SOURCE/'manifest.json')}

    def verify(relative):
        p = SOURCE/relative
        digest = sha256(p)
        assert digest == hashes[relative.replace('\\','/')]
        inputs[str(p.relative_to(ROOT))] = digest

    for relative in ['signals.parquet','security_ids.npy']:
        verify(relative)
    signals = pd.read_parquet(SOURCE/'signals.parquet')
    assert len(signals)==25250 and signals.event_id.is_unique
    by_date = {date:f.to_dict('records') for date,f in signals.groupby('date',sort=False)}
    ids = np.load(SOURCE/'security_ids.npy')
    index = {int(sid):i for i,sid in enumerate(ids)}
    signals.to_parquet(out/'signals.parquet',index=False)
    np.save(out/'security_ids.npy',ids)
    warm_path = ROOT/'data/raw/crsp/daily_by_year/daily_1993.parquet'
    warm_digest = sha256(warm_path)
    assert warm_digest == manifest['inputs'][str(warm_path.relative_to(ROOT))]
    inputs[str(warm_path.relative_to(ROOT))] = warm_digest
    d = pd.read_parquet(warm_path,columns=['date','permno','close','price_adjustment_factor'],filters=[('permno','in',ids.tolist())])
    d['adjusted'] = d.close/d.price_adjustment_factor
    d.loc[~np.isfinite(d.adjusted)|d.adjusted.le(0),'adjusted'] = np.nan
    tail = d.pivot(index='date',columns='permno',values='adjusted').reindex(
        index=valid_nyse_sessions('1993-01-01','1993-12-31'),columns=ids).tail(199)
    states = {}
    for rule in RULES:
        for policy in ['drift','monthly_equal']:
            states[f'{rule}__{policy}_10bps'] = RiskTrendPortfolio(policy,10,rule)
    for policy in ['drift','monthly_equal']:
        states[f'floor5_sma200__{policy}_0bps'] = RiskTrendPortfolio(policy,0,'floor5_sma200')
    previous_date = None
    for year in range(1994,2027):
        relative = f'panels/{year}.npz'
        verify(relative)
        with np.load(SOURCE/relative) as z:
            dates = pd.DatetimeIndex(z['dates'])
            panel = {k:z[k] for k in z.files if k!='dates'}
        close = pd.DataFrame(panel['close'],index=dates,columns=ids)
        combined = pd.concat([tail,close])
        sma200 = combined.rolling(200,min_periods=200).mean().reindex(dates).to_numpy()
        np.savez_compressed(out/f'features/{year}.npz',dates=dates.to_numpy(),sma200=sma200)
        panel['sma200'] = sma200
        for i,date in enumerate(dates):
            rows = {k:v[i] for k,v in panel.items()}
            candidates = by_date.get(previous_date,[]) if previous_date is not None else []
            for state in states.values():
                state.session(date,previous_date,rows,index,candidates)
            previous_date = date
        tail = close.tail(199)
        print(f'Year{year}: '+', '.join(f'{n}={p.nav():.0f}' for n,p in states.items() if n.endswith('drift_10bps')),flush=True)
    sessions = valid_nyse_sessions('1994-01-03','2026-06-30')
    spy_path = ROOT/'data/raw/yfinance/SPY.parquet'
    assert sha256(spy_path)==manifest['inputs'][str(spy_path.relative_to(ROOT))]
    inputs[str(spy_path.relative_to(ROOT))]=sha256(spy_path)
    stats, baseline_checks = [], {}
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
        if state.rule=='sma50':
            original = SOURCE/f'{state.policy}_10bps'
            for file in ['equity.csv','transactions.parquet']:
                verify(str((original/file).relative_to(SOURCE)).replace('\\','/'))
            old = pd.read_csv(original/'equity.csv',parse_dates=['date'])
            assert eq.date.equals(old.date)
            for col in ['nav','cash','positions','fees_cumulative','spy_nav']:
                assert np.allclose(eq[col],old[col],rtol=1e-12,atol=1e-7)
            pd.testing.assert_frame_equal(tx,pd.read_parquet(original/'transactions.parquet'))
            baseline_checks[name] = dict(daily_rows=len(eq),transactions=len(tx),passed=True)
        eq.to_csv(directory/'equity.csv',index=False)
        tx.to_parquet(directory/'transactions.parquet',index=False)
        closed.to_csv(directory/'closed_positions.csv',index=False)
        opened.to_csv(directory/'open_positions.csv',index=False)
        holdings.to_parquet(directory/'holdings.parquet',index=False)
        pd.DataFrame(state.exit_decisions).to_parquet(directory/'exit_decisions.parquet',index=False)
        pd.DataFrame(state.skips).to_csv(directory/'skips.csv',index=False)
        pnl = closed.pnl.sum()+opened.unrealized_total_pnl.sum()
        assert np.isclose(pnl,state.nav()-state.initial,atol=max(1e-5,state.nav()*1e-10))
        audit = dict(rule=state.rule,policy=state.policy,cost_bps=state.rate*10000,
            missing_trend_position_days=state.missing_trend_days,stale_position_days=state.stale_marks,
            deferred_exit_days=state.deferred_exits,fees=state.fees,weight_resets=state.rebalance_count,
            held_return_checks=state.return_checks,max_return_error=state.max_return_error,
            final_nav=state.nav(),cashflow_pnl=pnl,closed_positions=len(closed),open_positions=len(opened),
            floor_anchor='first actual entry opening; unchanged by rebalance')
        (directory/'accounting_audit.json').write_text(json.dumps(audit,indent=2))
        periods = [('all',eq),('1994_2009',eq.loc[eq.date.dt.year.le(2009)]),
            ('2010_2017',eq.loc[eq.date.dt.year.between(2010,2017)]),('2018_end',eq.loc[eq.date.dt.year.ge(2018)]),
            ('2018_2020',eq.loc[eq.date.dt.year.between(2018,2020)]),('2021_2022',eq.loc[eq.date.dt.year.between(2021,2022)]),
            ('2023_end',eq.loc[eq.date.dt.year.ge(2023)]),*[(str(y),f) for y,f in eq.groupby(eq.date.dt.year)]]
        for period,f in periods:
            start_index = f.index[0]
            initial = state.initial if start_index==0 else eq.nav.iloc[start_index-1]
            benchmark_initial = state.initial if start_index==0 else eq.spy_nav.iloc[start_index-1]
            reference = pd.DataFrame(dict(nav=f.spy_nav,daily_return=f.spy_return,exposure=1.,positions=1.))
            a,b = performance(f,initial),performance(reference,benchmark_initial)
            stats.append(dict(run=name,rule=state.rule,policy=state.policy,cost_bps=state.rate*10000,
                period=period,start=str(f.date.min().date()),end=str(f.date.max().date()),**a,
                spy_cagr=b['cagr'],spy_max_drawdown=b['max_drawdown'],cagr_gap=a['cagr']-b['cagr'],
                maximum_weight=holdings.loc[holdings.date.between(f.date.min(),f.date.max()),'weight'].max()))
        print('Saved',name,flush=True)
    summary = pd.DataFrame(stats)
    summary.to_csv(out/'summary.csv',index=False)
    (out/'baseline_replay.json').write_text(json.dumps(baseline_checks,indent=2))
    code = [Path(__file__),ROOT/'src/ath_breakout/research/initial_risk_trend.py',ROOT/'src/ath_breakout/research/sma50_portfolio.py',ROOT/'scripts/research/backtest_ath_sma50_portfolio.py']
    result = dict(study_id='ath_30_initial_risk_trend_v001',source=str(SOURCE.relative_to(ROOT)),inputs=inputs,
        protocol_sha256=sha256(ROOT/'research/ath/ATH_INITIAL_RISK_TREND_PLAN.md'),
        code={str(p.relative_to(ROOT)):sha256(p) for p in code},
        artifacts={str(p.relative_to(out)):sha256(p) for p in out.rglob('*') if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    print(summary.loc[summary.period.eq('all')].to_string(index=False),flush=True)
    print(out,flush=True)


if __name__=='__main__':
    main()
