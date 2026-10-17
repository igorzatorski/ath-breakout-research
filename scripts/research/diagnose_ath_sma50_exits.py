"""ATH29: frozen portfolio loss decomposition and fixed252-session exit paths."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.research.exit_diagnostic import price_components, unit_path  # noqa: E402

SOURCE = ROOT/'outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def main():
    out = ROOT/f'outputs/research/ath/ath_29_sma50_exit_diagnostic_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    print(out, flush=True)
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    hashes = {k.replace('\\','/'):v for k,v in manifest['artifacts'].items()}
    required = ['security_ids.npy']+[str(p.relative_to(SOURCE)) for p in (SOURCE/'panels').glob('*.npz')]
    required += [f'{name}/{file}' for name in ['drift_10bps','monthly_equal_10bps'] for file in ['closed_positions.csv','transactions.parquet']]
    for name in required:
        assert sha(SOURCE/name) == hashes[name.replace('\\','/')]
    ids = np.load(SOURCE/'security_ids.npy')
    ix = {int(sid): i for i,sid in enumerate(ids)}
    fields = ['open','close','dividend','terminal','return','previous_close']
    parts = {k: [] for k in fields}
    dates = []
    for file in sorted((SOURCE/'panels').glob('*.npz')):
        with np.load(file) as z:
            dates.extend(z['dates'])
            for k in fields:
                parts[k].append(z[k])
    arrays = {k: np.concatenate(parts.pop(k)) for k in fields}
    dates = pd.DatetimeIndex(dates)
    di = {d:i for i,d in enumerate(dates)}
    records = []
    max_pnl_error, max_drift_return_error = 0., 0.
    for policy in ['drift_10bps','monthly_equal_10bps']:
        c = pd.read_csv(SOURCE/policy/'closed_positions.csv', parse_dates=['entry_date','exit_date'])
        tx = pd.read_parquet(SOURCE/policy/'transactions.parquet')
        entries = {(r.date,int(r.permno)):r for r in tx.loc[tx.kind.eq('ENTRY')].itertuples()}
        exits = {(r.date,int(r.permno)):r for r in tx.loc[tx.kind.eq('SMA50_EXIT')].itertuples()}
        for r in c.loc[c.reason.eq('SMA50_EXIT')].itertuples():
            entry, sale = entries[(r.entry_date,int(r.permno))], exits[(r.exit_date,int(r.permno))]
            j, a, b = ix[int(r.permno)], di[r.entry_date], di[r.exit_date]
            decision = di[sale.decision_date]
            decision_price = arrays['close'][decision,j]
            quantity = -sale.quantity
            episode = tx.loc[(tx.index >= entry.Index)&(tx.index < sale.Index)&tx.permno.eq(r.permno)]
            pre = quantity*decision_price+episode.cash_delta.sum()
            movement = quantity*(sale.price-decision_price)
            error = abs(pre+movement-sale.fee-r.pnl)
            max_pnl_error = max(max_pnl_error,error)
            assert error < max(1e-5,abs(r.bought)*1e-9)
            record = dict(policy=policy,permno=int(r.permno),ticker=r.ticker,entry_date=r.entry_date,
                decision_date=sale.decision_date,exit_date=r.exit_date,holding_sessions=b-a+1,
                entry_price=entry.price,decision_close=decision_price,exit_price=sale.price,
                execution_window_return=sale.price/decision_price-1,price_return_at_decision=decision_price/entry.price-1,
                actual_pnl=r.pnl,actual_profit_ratio=r.cashflow_profit_ratio,pre_execution_pnl=pre,
                execution_movement_pnl=movement,exit_fee=sale.fee,paired_status='exit_at_or_after252')
            components = price_components(arrays['open'][a:b+1,j],arrays['close'][a:b+1,j],entry.price,sale.price)
            if components:
                record.update(components)
            end = a+251
            if b < end:
                if end >= len(dates):
                    record['paired_status'] = 'immature252'
                else:
                    sl = slice(a,end+1)
                    pair = unit_path(arrays['open'][sl,j],arrays['close'][sl,j],arrays['dividend'][sl,j],
                        arrays['terminal'][sl,j],arrays['return'][sl,j],arrays['previous_close'][sl,j],entry.price,b-a)
                    record['paired_status'] = 'complete' if pair else 'missing_path'
                    if pair:
                        record.update(pair)
                        record['endpoint_date'] = dates[end]
                        if policy == 'drift_10bps':
                            err = abs(pair['sale_return']-r.cashflow_profit_ratio)
                            max_drift_return_error = max(max_drift_return_error,err)
                            assert err < 1e-8
            records.append(record)
        print(policy,'SMA exits processed',sum(r['policy']==policy for r in records),flush=True)
    events = pd.DataFrame(records)
    events.to_parquet(out/'exit_events.parquet',index=False)
    summaries, losses = [], []
    for policy, g in events.groupby('policy'):
        for period, f in [('all',g),('1994_2009',g.loc[g.entry_date.dt.year.le(2009)]),
            ('2010_2017',g.loc[g.entry_date.dt.year.between(2010,2017)]),('2018_end',g.loc[g.entry_date.dt.year.ge(2018)]),
            ('2023_end',g.loc[g.entry_date.dt.year.ge(2023)])]:
            q = f.loc[f.paired_status.eq('complete')]
            lost = q.sale_return.lt(0)
            summaries.append(dict(policy=policy,period=period,sma_exits=len(f),complete_pairs=len(q),
                mean_sale_return=q.sale_return.mean(),mean_hold_return=q.hold_return.mean(),
                mean_hold_minus_sale=q.hold_minus_sale.mean(),median_hold_minus_sale=q.hold_minus_sale.median(),
                hold_ahead_frequency=q.hold_minus_sale.gt(0).mean(),subsequent_10pct_price_rebound=q.max_post_exit_price_return.ge(.1).mean(),
                losing_sales=int(lost.sum()),losing_sale_then_positive_endpoint=int((lost&q.hold_return.gt(0)).sum()),
                losing_sale_recovery_frequency=q.loc[lost,'hold_return'].gt(0).mean(),
                final_doublers=int(q.hold_return.ge(1).sum()),final_doubler_sale_return_mean=q.loc[q.hold_return.ge(1),'sale_return'].mean(),
                hold_advantage_without_doublers=q.loc[q.hold_return.lt(1),'hold_minus_sale'].mean()))
        for label, f in [('all_losses',g.loc[g.actual_pnl.lt(0)]),('large_losses_le_minus20pct',g.loc[g.actual_profit_ratio.le(-.2)])]:
            total = -f.actual_pnl.sum()
            losses.append(dict(policy=policy,group=label,count=len(f),total_loss_usd=total,
                pre_execution_loss_usd=-f.pre_execution_pnl.sum(),execution_movement_loss_usd=-f.execution_movement_pnl.sum(),
                exit_fees_usd=f.exit_fee.sum(),execution_movement_share=-f.execution_movement_pnl.sum()/total,
                mean_profit_ratio=f.actual_profit_ratio.mean(),mean_price_return_at_decision=f.price_return_at_decision.mean(),
                mean_execution_window_return=f.execution_window_return.mean(),median_execution_window_return=f.execution_window_return.median(),
                adverse_execution_ge5pct=f.execution_window_return.le(-.05).mean()))
        g.nsmallest(20,'actual_pnl').to_csv(out/f'{policy}_largest_losses.csv',index=False)
    summary = pd.DataFrame(summaries)
    summary.to_csv(out/'paired_summary.csv',index=False)
    pd.DataFrame(losses).to_csv(out/'loss_decomposition.csv',index=False)
    counts = events.groupby(['policy','paired_status']).size().unstack(fill_value=0)
    counts.to_csv(out/'coverage.csv')
    audit = dict(max_actual_pnl_reconciliation_error=max_pnl_error,max_drift_sale_return_error=max_drift_return_error,
        source_sha256=sha(SOURCE/'manifest.json'),source_artifacts_verified=len(required),source_run=str(SOURCE.relative_to(ROOT)))
    (out/'audit.json').write_text(json.dumps(audit,indent=2))
    metadata = dict(study_id='ath_29_sma50_exit_diagnostic_v001',source=str(SOURCE.relative_to(ROOT)),
        protocol_sha256=sha(ROOT/'research/ath/ATH_SMA50_EXIT_DIAGNOSTIC_PLAN.md'),
        code={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/ath_breakout/research/exit_diagnostic.py']},
        artifacts={str(p.relative_to(out)):sha(p) for p in out.iterdir() if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(metadata,indent=2))
    print(summary.to_string(index=False),flush=True)
    print(pd.DataFrame(losses).to_string(index=False),flush=True)
    print(counts.to_string(),flush=True)


if __name__ == '__main__':
    main()
