"""Independent ATH33 cold-start decision and cash/share replay."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z'


def main(path,rule_filter=None):
    path = Path(path)
    ids = np.load(path/'security_ids.npy')
    ix = {int(s):i for i,s in enumerate(ids)}
    signals = pd.read_parquet(path/'signals.parquet')
    source = {(pd.Timestamp(r.date),int(r.permno)) for r in signals.itertuples()}
    summary = pd.read_csv(path/'summary.csv')
    results = {}
    for directory in sorted(path.glob('*bps')):
        if rule_filter and not directory.name.startswith(rule_filter+'__'):
            continue
        rule,config = directory.name.split('__')
        floor_active = rule.startswith('floor5')
        thresholds = {'sma150':None,'step25_50':(.25,.5),'step50_100':(.5,1.),'step100_200':(1.,2.)}[rule]
        stages = {}
        reconstructed_transitions = []
        rate = .001 if config.endswith('_10bps') else 0.
        tx = pd.read_parquet(directory/'transactions.parquet')
        equity = pd.read_csv(directory/'equity.csv',parse_dates=['date'])
        holdings = pd.read_parquet(directory/'holdings.parquet')
        decisions = pd.read_parquet(directory/'exit_decisions.parquet')
        groups = {d:g for d,g in tx.groupby('date',sort=False)}
        hgroups = {d:g for d,g in holdings.groupby('date',sort=False)}
        expected_decisions = {(r.date,int(r.permno)):r for r in decisions.itertuples()}
        qty,anchors,marks,pending = {},{},{},{}
        assert equity.date.iloc[0]==pd.Timestamp('2008-01-02')
        assert tx.date.ge('2008-01-02').all()
        assert tx.loc[tx.kind.eq('ENTRY'),'decision_date'].ge('2007-12-31').all()
        cash,previous,decision_count,terminal_count = 100000.,pd.Timestamp('2007-12-31'),0,0
        for year,year_eq in equity.groupby(equity.date.dt.year,sort=False):
            with np.load(SOURCE/f'panels/{year}.npz') as z:
                panel = {k:z[k] for k in z.files if k!='dates'}
            with np.load(path/f'features/{year}.npz') as z:
                panel.update({k:z[k] for k in z.files if k!='dates'})
            for i,row in enumerate(year_eq.itertuples()):
                daily = groups.get(row.date,tx.iloc[:0])
                overnight_qty,overnight_marks = dict(qty),dict(marks)
                required_exits = {sid for sid in pending if np.isfinite(panel['open'][i,ix[sid]]) and panel['open'][i,ix[sid]]>0}
                actual_exits = set(daily.loc[daily.kind.str.endswith('_EXIT'),'permno'].astype(int))
                assert actual_exits==required_exits
                expected_dividends = sum(q*panel['dividend'][i,ix[sid]] for sid,q in overnight_qty.items() if panel['observed'][i,ix[sid]])
                assert np.isclose(daily.loc[daily.kind.eq('DIVIDEND'),'cash_delta'].sum(),expected_dividends,atol=max(1e-5,row.nav*1e-10))
                for t in daily.itertuples():
                    sid,j = int(t.permno),ix[int(t.permno)]
                    assert np.isclose(qty.get(sid,0.),t.quantity_before,atol=1e-7)
                    if t.kind=='DIVIDEND':
                        assert np.isclose(t.cash_delta,overnight_qty[sid]*panel['dividend'][i,j])
                    else:
                        assert np.isclose(t.cash_delta,-t.quantity*t.price-t.fee,atol=1e-6)
                        assert np.isclose(t.fee,abs(t.quantity*t.price)*(0 if t.kind=='CIZ_TERMINAL' else rate))
                        if t.kind=='CIZ_TERMINAL':
                            assert panel['terminal'][i,j]
                            prior = overnight_marks.get(sid,panel['previous_close'][i,j])
                            payoff = prior*(1+panel['return'][i,j])-panel['dividend'][i,j]
                            assert np.isclose(t.price,max(0.,payoff))
                            terminal_count += 1
                        else:
                            assert np.isclose(t.price,panel['open'][i,j])
                        if t.kind=='ENTRY':
                            assert t.decision_date==previous and (t.decision_date,sid) in source
                            assert sid not in anchors
                            anchors[sid] = t.price
                            stages[sid] = 0
                        if t.kind.endswith('_EXIT'):
                            assert (t.decision_date,t.kind)==pending[sid]
                        qty[sid] = qty.get(sid,0.)+t.quantity
                        if t.kind.endswith('_EXIT') or t.kind=='CIZ_TERMINAL':
                            assert abs(qty[sid]) < max(1e-7,abs(t.quantity_before)*1e-10)
                            del qty[sid]
                            anchors.pop(sid)
                            stages.pop(sid)
                            marks.pop(sid,None)
                            pending.pop(sid,None)
                    cash += t.cash_delta
                    assert np.isclose(cash,t.cash_after,atol=max(1e-5,row.nav*1e-10))
                h = hgroups.get(row.date,holdings.iloc[:0])
                assert set(qty)==set(h.permno) and h.permco.is_unique and len(h)<=20
                if daily.kind.str.startswith('REBAL_').any():
                    last = daily.loc[~daily.kind.isin(['DIVIDEND','CIZ_TERMINAL'])].iloc[-1]
                    assert np.allclose(h.quantity.to_numpy()*panel['open'][i,[ix[int(s)] for s in h.permno]]/last.nav_after,.05,atol=1e-9)
                for position in h.itertuples():
                    sid,j = int(position.permno),ix[int(position.permno)]
                    close,opening = panel['close'][i,j],panel['open'][i,j]
                    expected_mark = close if np.isfinite(close) and close>0 else opening if np.isfinite(opening) and opening>0 else marks[sid]
                    assert np.isclose(expected_mark,position.price)
                    assert np.isclose(qty[sid],position.quantity,atol=1e-7)
                    marks[sid] = position.price
                    old_stage = stages[sid]
                    if sid not in pending and thresholds is not None and np.isfinite(close) and close>0:
                        reached = 2 if close >= anchors[sid]*(1+thresholds[1]) else 1 if close >= anchors[sid]*(1+thresholds[0]) else 0
                        stages[sid] = max(stages[sid],reached)
                    window = (150,100,50)[stages[sid]]
                    trend = panel[f'sma{window}'][i,j]
                    if stages[sid] != old_stage:
                        old_sma = panel[f'sma{(150,100,50)[old_stage]}'][i,j]
                        reconstructed_transitions.append(dict(date=row.date,permno=sid,entry_price=anchors[sid],close=close,
                            prior_stage=old_stage,stage=stages[sid],previous_sma=old_sma,selected_sma=trend,
                            numerically_lower=bool(np.isfinite(trend) and np.isfinite(old_sma) and trend<old_sma)))
                    floor = .95*anchors[sid] if floor_active else np.nan
                    floor_hit = floor_active and np.isfinite(close) and close<floor
                    trend_hit = np.isfinite(close) and np.isfinite(trend) and close<trend
                    if sid not in pending and (floor_hit or trend_hit):
                        reason = 'BOTH_EXIT' if floor_hit and trend_hit else 'INITIAL_5_EXIT' if floor_hit else f'SMA{window}_EXIT'
                        pending[sid] = (row.date,reason)
                        d = expected_decisions[(row.date,sid)]
                        assert d.window==window and d.stage==stages[sid]
                        assert d.reason==reason and np.isclose(d.entry_price,anchors[sid])
                        assert np.isclose(d.floor,floor,equal_nan=True) and np.isclose(d.sma,trend,equal_nan=True)
                        decision_count += 1
                    assert bool(position.pending_exit)==(sid in pending), (directory.name,row.date,sid,close,trend,floor,position.pending_exit,pending.get(sid))
                assert np.isclose(cash,row.cash,atol=max(1e-5,row.nav*1e-10))
                assert np.isclose(cash+sum(qty[sid]*marks[sid] for sid in qty),row.nav,atol=max(1e-5,row.nav*1e-10))
                previous = row.date
        assert decision_count==len(decisions)
        observed_transitions = pd.read_parquet(directory/'transitions.parquet')
        expected_transitions = pd.DataFrame(reconstructed_transitions,columns=observed_transitions.columns)
        assert len(expected_transitions)==len(observed_transitions)
        if len(expected_transitions):
            pd.testing.assert_frame_equal(expected_transitions.sort_values(['date','permno']).reset_index(drop=True),
                observed_transitions.sort_values(['date','permno']).reset_index(drop=True),check_dtype=False)

        stats = summary.loc[summary.run.eq(directory.name)&summary.period.eq('all')].iloc[0]
        curve = np.r_[100000.,equity.nav.to_numpy()]
        assert np.isclose(stats.cagr,(curve[-1]/curve[0])**(252/len(equity))-1)
        assert np.isclose(stats.max_drawdown,(curve/np.maximum.accumulate(curve)-1).min())
        results[directory.name] = dict(sessions=len(equity),transactions=len(tx),holdings=len(holdings),
            independently_reconstructed_decisions=decision_count,stage_transitions=len(reconstructed_transitions),terminal_settlements=terminal_count,passed=True)
        print(directory.name,results[directory.name],flush=True)
        (path/f'independent_verification_{rule_filter or "all"}.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__':
    main(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
