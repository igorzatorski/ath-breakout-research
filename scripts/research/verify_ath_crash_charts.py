"""Independent reconciliation of every plotted point and crash metric."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


def main(run):
    run = Path(run)
    rows = pd.read_csv(run/'crash_charts/reviewed_chart_rows.csv',parse_dates=['date'])
    assert not rows.duplicated(['episode','policy','series','panel','date']).any()
    metrics = pd.read_csv(run/'crash_metrics.csv')
    checked = 0
    for (episode,policy,rule,panel),g in rows.groupby(['episode','policy','series','panel']):
        source = pd.read_csv(run/f'{rule if rule!="SPY" else "base"}__{policy}_10bps/equity.csv',parse_dates=['date'])
        f = source.set_index('date').loc[g.date]
        if panel==1:
            nav = f.spy_nav if rule=='SPY' else f.nav
            expected = nav/nav.iloc[0]*100
        elif panel==2:
            nav = source.set_index('date')['spy_nav' if rule=='SPY' else 'nav']
            peak = nav.cummax().clip(lower=100000.)
            expected = ((nav/peak-1)*100).loc[g.date]
        else:
            assert rule!='SPY'
            expected = 100*f.cash/f.nav
        assert np.allclose(expected,g.value,rtol=1e-11,atol=1e-9)
        checked += len(g)
    for row in metrics.itertuples():
        e = pd.read_csv(run/row.run/'equity.csv',parse_dates=['date'])
        g = e.loc[e.date.between(row.start,row.end)]
        j = g.index[0]
        initial = 100000. if j==0 else e.nav.iloc[j-1]
        curve = pd.Series([initial]+g.nav.tolist())
        assert np.isclose(row.window_return,curve.iloc[-1]/curve.iloc[0]-1)
        assert np.isclose(row.local_max_drawdown,(curve/curve.cummax()-1).min())
        cash = g.cash/g.nav
        assert np.isclose(row.average_cash,cash.mean())
        assert np.isclose(row.min_cash,cash.min()) and np.isclose(row.max_cash,cash.max())
        assert np.isclose(row.cash_at_spy_trough,cash.loc[g.date.eq(row.spy_trough_date)].iloc[0])
        spy_initial = 100000. if j==0 else e.spy_nav.iloc[j-1]
        spy = pd.Series([spy_initial]+g.spy_nav.tolist())
        dd = spy/spy.cummax()-1
        t = int(dd.idxmin())
        p = int(spy.iloc[:t+1].idxmax())
        assert row.spy_trough_date == str(g.date.iloc[t-1].date())
        assert np.isclose(row.spy_peak_to_trough,dd.iloc[t])
        assert np.isclose(row.strategy_matched_peak_to_trough,curve.iloc[t]/curve.iloc[p]-1)
    result = dict(chart_points=checked,crash_metric_rows=len(metrics),passed=True)
    (run/'independent_crash_verification.json').write_text(json.dumps(result,indent=2))
    print(result)


if __name__=='__main__':
    main(sys.argv[1])
