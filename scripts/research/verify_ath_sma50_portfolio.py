"""Independent transaction/share replay and raw-panel execution checks for ATH28."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


def main(path):
    path = Path(path)
    ids = np.load(path/'security_ids.npy')
    ix = {int(s): i for i, s in enumerate(ids)}
    signals = pd.read_parquet(path/'signals.parquet')
    source = {(pd.Timestamp(r.date), int(r.permno)) for r in signals.itertuples()}
    panels = {}
    for file in sorted((path/'panels').glob('*.npz')):
        with np.load(file) as z:
            arrays = {k: z[k] for k in z.files if k != 'dates'}
            for i, date in enumerate(z['dates']):
                panels[pd.Timestamp(date)] = {k: a[i] for k, a in arrays.items()}
    checks = {}
    for directory in sorted(path.glob('*bps')):
        tx = pd.read_parquet(directory/'transactions.parquet')
        tx.date = pd.to_datetime(tx.date)
        tx.decision_date = pd.to_datetime(tx.decision_date)
        eq = pd.read_csv(directory/'equity.csv', parse_dates=['date'])
        h = pd.read_parquet(directory/'holdings.parquet')
        h.date = pd.to_datetime(h.date)
        tgroup = {d: g for d, g in tx.groupby('date', sort=False)}
        hgroup = {d: g for d, g in h.groupby('date', sort=False)}
        cash, quantities, last = 100000., {}, {}
        count = 0
        rate = 0.001 if directory.name.endswith('_10bps') else 0.
        previous = None
        for row in eq.itertuples():
            panel = panels[row.date]
            day = tgroup.get(row.date, tx.iloc[:0])
            for t in day.itertuples():
                sid = int(t.permno)
                assert np.isclose(quantities.get(sid, 0.), t.quantity_before, atol=1e-7)
                if t.kind == 'DIVIDEND':
                    assert np.isclose(t.cash_delta, quantities[sid]*panel['dividend'][ix[sid]])
                else:
                    assert np.isclose(t.cash_delta, -t.quantity*t.price-t.fee, atol=1e-7)
                    assert np.isclose(t.fee, abs(t.quantity*t.price)*(0 if t.kind == 'CIZ_TERMINAL' else rate))
                    if t.kind != 'CIZ_TERMINAL':
                        assert np.isclose(t.price, panel['open'][ix[sid]])
                    if t.kind == 'ENTRY':
                        assert t.decision_date == previous
                        assert (t.decision_date, sid) in source
                    if t.kind == 'SMA50_EXIT':
                        decision = panels[t.decision_date]
                        assert decision['close'][ix[sid]] < decision['sma'][ix[sid]]
                        assert t.decision_date < row.date
                        intervening = [d for d in eq.date if t.decision_date < d < row.date]
                        assert all(not np.isfinite(panels[d]['open'][ix[sid]]) for d in intervening)
                    quantities[sid] = quantities.get(sid, 0.)+t.quantity
                    if t.kind in ['SMA50_EXIT', 'CIZ_TERMINAL']:
                        assert abs(quantities[sid]) < max(1e-7, abs(t.quantity_before)*1e-10)
                        del quantities[sid]
                        last.pop(sid, None)
                cash += t.cash_delta
                assert np.isclose(cash, t.cash_after, atol=max(1e-5, abs(cash)*1e-10))
                count += 1
            holdings = hgroup.get(row.date, h.iloc[:0])
            assert set(quantities) == set(holdings.permno)
            assert len(holdings) <= 20 and holdings.permco.is_unique
            for position in holdings.itertuples():
                sid = int(position.permno)
                c, o = panel['close'][ix[sid]], panel['open'][ix[sid]]
                expected = c if np.isfinite(c) and c > 0 else o if np.isfinite(o) and o > 0 else last[sid]
                assert np.isclose(expected, position.price)
                assert np.isclose(quantities[sid], position.quantity, atol=1e-7)
                assert np.isclose(position.value, position.price*position.quantity)
                last[sid] = position.price
            assert np.isclose(cash, row.cash, atol=max(1e-5, row.nav*1e-10))
            assert np.isclose(cash+holdings.value.sum(), row.nav, atol=max(1e-5, row.nav*1e-10))
            previous = row.date
        summary = pd.read_csv(path/'summary.csv')
        stats = summary.loc[summary.run.eq(directory.name) & summary.period.eq('all')].iloc[0]
        curve = np.r_[100000., eq.nav.to_numpy()]
        assert np.isclose(stats.cagr, (curve[-1]/curve[0])**(252/len(eq))-1)
        assert np.isclose(stats.max_drawdown, (curve/np.maximum.accumulate(curve)-1).min())
        checks[directory.name] = dict(transactions=count, sessions=len(eq), holding_rows=len(h),
            final_cash=float(cash), final_nav=float(eq.nav.iloc[-1]), passed=True)
        print(directory.name, checks[directory.name], flush=True)
    (path/'independent_verification.json').write_text(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
