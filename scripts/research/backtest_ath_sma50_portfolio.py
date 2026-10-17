"""Recorded first portfolio backtest; fresh signals, SMA50 and two weight policies."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.sma50_portfolio import Portfolio, performance  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_27_event_ranking_v001/20261017T140021546620Z'
HASH_SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
START, END = pd.Timestamp('1994-01-03'), pd.Timestamp('2026-06-30')


def benchmark(path, sessions, cost_bps):
    spy = pd.read_parquet(path).set_index('date').reindex(sessions)
    if not np.isfinite(spy[['open', 'close', 'adj_close']]).all().all() or (spy[['open', 'close', 'adj_close']] <= 0).any().any():
        raise ValueError('Incomplete benchmark calendar')
    curve = 100000/(1+cost_bps/10000)*spy.close.iloc[0]/spy.open.iloc[0]*spy.adj_close/spy.adj_close.iloc[0]
    returns = curve.pct_change()
    returns.iloc[0] = curve.iloc[0]/100000-1
    return curve, returns


def main():
    out = ROOT/f'outputs/backtests/ath_28_sma50_portfolio_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    (out/'panels').mkdir(parents=True)
    print(out, flush=True)
    inputs = {}
    source_manifest = json.loads((SOURCE/'manifest.json').read_text())
    assert sha256(SOURCE/'events.parquet') == source_manifest['artifacts']['events.parquet']
    for p in [SOURCE/'events.parquet', SOURCE/'manifest.json', HASH_SOURCE/'manifest.json']:
        inputs[str(p.relative_to(ROOT))] = sha256(p)
    signals = pd.read_parquet(SOURCE/'events.parquet')
    assert len(signals) == 25250 and signals.event_id.is_unique
    assert np.isfinite(signals.score_MV).all()
    signals = signals.sort_values(['date', 'score_MV', 'momentum_6_1', 'permno'], ascending=[True, False, False, True])
    signals.to_parquet(out/'signals.parquet', index=False)
    by_date = {date: f.to_dict('records') for date, f in signals.groupby('date', sort=False)}
    ids = np.array(sorted(signals.permno.astype(int).unique()))
    np.save(out/'security_ids.npy', ids)
    index = {int(sid): i for i, sid in enumerate(ids)}
    hashes = json.loads((HASH_SOURCE/'manifest.json').read_text())['inputs']
    spy_path = ROOT/'data/raw/yfinance/SPY.parquet'
    inputs[str(spy_path.relative_to(ROOT))] = sha256(spy_path)
    sessions = valid_nyse_sessions(START, END)
    states = {f'{policy}_{cost}bps': Portfolio(policy, cost) for policy in ['drift', 'monthly_equal'] for cost in [0, 10]}
    tail = None
    previous_date = None
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        digest = sha256(path)
        assert digest == hashes[str(path.relative_to(ROOT))]
        inputs[str(path.relative_to(ROOT))] = digest
        columns = ['permno', 'permco', 'date', 'open', 'close', 'price_adjustment_factor',
            'ordinary_dividend', 'nonordinary_dividend', 'total_return', 'delisting_flag', 'period_price_factor']
        d = pd.read_parquet(path, columns=columns, filters=[('permno', 'in', ids.tolist())])
        factor = d.price_adjustment_factor.where(np.isfinite(d.price_adjustment_factor) & d.price_adjustment_factor.gt(0))
        d['c'] = (d.close/factor).where(np.isfinite(d.close) & d.close.gt(0))
        d['o'] = (d.open/factor).where(np.isfinite(d.open) & d.open.gt(0))
        # CIZ cash amounts are per pre-event share. On simultaneous split and
        # distribution dates use the pre-event cumulative price-factor basis.
        distribution_factor = factor*d.period_price_factor
        d['div'] = (d.ordinary_dividend+d.nonordinary_dividend)/distribution_factor
        # A terminal nonordinary cash payout is already in CIZ's Y return.
        # It settles at close; do not also credit it as an opening dividend.
        terminal = d.delisting_flag.eq('Y')
        ordinary = (d.ordinary_dividend/distribution_factor).where(d.ordinary_dividend.ne(0), 0.)
        d.loc[terminal, 'div'] = ordinary.loc[terminal]
        calendar = valid_nyse_sessions(f'{year}-01-01', min(pd.Timestamp(f'{year}-12-31'), END))

        def pivot(col):
            return d.pivot(index='date', columns='permno', values=col).reindex(index=calendar, columns=ids)
        close = pivot('c')
        if tail is None:
            tail = close.tail(49)
            continue
        complete_close = pd.concat([tail, close])
        sma = complete_close.rolling(50, min_periods=50).mean().reindex(calendar)
        previous = complete_close.shift(1).reindex(calendar)
        d['terminal'] = d.delisting_flag.eq('Y')
        d['observed'] = True
        panel = {'open': pivot('o').to_numpy(), 'close': close.to_numpy(), 'dividend': pivot('div').to_numpy(),
            'return': pivot('total_return').to_numpy(), 'company': pivot('permco').to_numpy(),
            'terminal': pivot('terminal').eq(True).to_numpy(), 'observed': pivot('observed').eq(True).to_numpy(),
            'sma': sma.to_numpy(), 'previous_close': previous.to_numpy()}
        np.savez_compressed(out/f'panels/{year}.npz', dates=calendar.to_numpy(), **panel)
        for i, date in enumerate(calendar):
            candidates = by_date.get(previous_date, []) if previous_date is not None else []
            rows = {field: values[i] for field, values in panel.items()}
            for state in states.values():
                state.session(date, previous_date, rows, index, candidates)
            previous_date = date
        tail = close.tail(49)
        print(f'Portfolio year {year}: '+', '.join(f'{name} NAV={state.nav():.2f}, positions={len(state.positions)}' for name, state in states.items()), flush=True)
    stats = []
    for name, state in states.items():
        directory = out/name
        directory.mkdir()
        eq = pd.DataFrame(state.equity)
        spy_curve, spy_returns = benchmark(spy_path, sessions, state.rate*10000)
        eq['spy_nav'] = spy_curve.to_numpy()
        eq['spy_return'] = spy_returns.to_numpy()
        eq['drawdown'] = eq.nav/np.maximum.accumulate(np.r_[state.initial, eq.nav])[1:]-1
        eq.to_csv(directory/'equity.csv', index=False)
        pd.DataFrame(state.transactions).to_parquet(directory/'transactions.parquet', index=False)
        pd.DataFrame(state.closed).to_csv(directory/'closed_positions.csv', index=False)
        state.ending_positions().to_csv(directory/'open_positions.csv', index=False)
        pd.DataFrame(state.holdings).to_parquet(directory/'holdings.parquet', index=False)
        pd.DataFrame(state.skips).to_csv(directory/'skips.csv', index=False)
        pnl = sum(p['pnl'] for p in state.closed)+state.ending_positions().unrealized_total_pnl.sum()
        assert np.isclose(pnl, state.nav()-state.initial, atol=max(1e-4, state.nav()*1e-10))
        audit = dict(policy=state.policy, cost_bps=state.rate*10000, source_candidates=len(signals),
            stale_position_marks=state.stale_marks, deferred_exit_days=state.deferred_exits,
            held_return_checks=state.return_checks, max_return_reconciliation_error=state.max_return_error,
            weight_resets=state.rebalance_count, fees=state.fees, closed_positions=len(state.closed),
            ending_positions=len(state.positions), cashflow_pnl=pnl, final_nav=state.nav())
        (directory/'accounting_audit.json').write_text(json.dumps(audit, indent=2))
        periods = [('all', eq), ('1994_2009', eq.loc[eq.date.dt.year.le(2009)]),
            ('2010_2017', eq.loc[eq.date.dt.year.between(2010, 2017)]), ('2018_end', eq.loc[eq.date.dt.year.ge(2018)]),
            ('2018_2020', eq.loc[eq.date.dt.year.between(2018, 2020)]), ('2021_2022', eq.loc[eq.date.dt.year.between(2021, 2022)]),
            ('2023_end', eq.loc[eq.date.dt.year.ge(2023)]), *[(str(y), f) for y, f in eq.groupby(eq.date.dt.year)]]
        for period, f in periods:
            if f.empty:
                continue
            initial = state.initial if f.index[0] == 0 else eq.nav.iloc[f.index[0]-1]
            benchmark_frame = pd.DataFrame(dict(nav=f.spy_nav, daily_return=f.spy_return, exposure=1., positions=1.))
            benchmark_initial = state.initial if f.index[0] == 0 else eq.spy_nav.iloc[f.index[0]-1]
            a, b = performance(f, initial), performance(benchmark_frame, benchmark_initial)
            stats.append(dict(run=name, period=period, start=str(f.date.min().date()), end=str(f.date.max().date()),
                **a, spy_cagr=b['cagr'], spy_volatility=b['volatility'], spy_max_drawdown=b['max_drawdown'],
                cagr_gap=a['cagr']-b['cagr'], maximum_weight=pd.DataFrame(state.holdings).loc[
                    lambda h: h.date.between(f.date.min(), f.date.max()), 'weight'].max()))
    summary = pd.DataFrame(stats)
    summary.to_csv(out/'summary.csv', index=False)
    print(summary.loc[summary.period.eq('all')].to_string(index=False), flush=True)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/sma50_portfolio.py']
    result = dict(study_id='ath_28_sma50_portfolio_v001', inputs=inputs, start=str(START.date()), end=str(END.date()),
        policies=['drift', 'monthly_equal'], cost_bps=[0, 10], maximum_companies=20, target_weight=.05,
        code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        protocol_sha256=sha256(ROOT/'research/ath/ATH_SMA50_PORTFOLIO_PLAN.md'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.rglob('*') if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(out, flush=True)


if __name__ == '__main__':
    main()
