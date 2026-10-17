"""Independent raw CRSP path sample and full loss-decomposition checks for ATH29."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main(path):
    path = Path(path)
    events = pd.read_parquet(path/'exit_events.parquet')
    assert np.allclose(events.pre_execution_pnl+events.execution_movement_pnl-events.exit_fee,events.actual_pnl,atol=1e-6)
    complete = events.loc[events.paired_status.eq('complete')]
    sample = complete.sample(60,random_state=2901)
    terminal = complete.loc[complete.terminal_before_endpoint.eq(True)].head(20)
    sample = pd.concat([sample,terminal]).drop_duplicates(['policy','permno','entry_date'])
    ids = sample.permno.unique().tolist()
    columns = ['date','permno','open','close','price_adjustment_factor','period_price_factor',
        'ordinary_dividend','nonordinary_dividend','delisting_flag','total_return']
    frames = []
    for year in range(sample.entry_date.dt.year.min(),sample.endpoint_date.dt.year.max()+1):
        frames.append(pd.read_parquet(ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet',columns=columns,
            filters=[('permno','in',ids)]))
    raw = pd.concat(frames).set_index(['permno','date'])
    source = ROOT/'outputs/backtests/ath_28_sma50_portfolio_v001/20261017T145348713599Z'
    calendar = pd.to_datetime(pd.read_csv(source/'drift_10bps/equity.csv').date)
    errors = []
    for episode in sample.itertuples():
        dates = calendar.loc[calendar.between(episode.entry_date,episode.endpoint_date)]
        assert len(dates)==252
        d = raw.loc[episode.permno].reindex(dates)
        cash, alive = 0., True
        sale = np.nan
        previous = np.nan
        final = np.nan
        for date,r in d.iterrows():
            if not alive:
                continue
            div = 0. if date == episode.entry_date else (r.ordinary_dividend+r.nonordinary_dividend)/(r.price_adjustment_factor*r.period_price_factor)
            if r.delisting_flag == 'Y':
                div = 0. if r.ordinary_dividend == 0 else r.ordinary_dividend/(r.price_adjustment_factor*r.period_price_factor)
            cash += div
            if date == episode.exit_date:
                sale = (r.open/r.price_adjustment_factor*.999+cash)/(episode.entry_price*1.001)-1
            if r.delisting_flag == 'Y':
                cash += previous*(1+r.total_return)-div
                final, alive = cash, False
            else:
                previous = r.close/r.price_adjustment_factor
                final = previous*.999+cash
        hold = final/(episode.entry_price*1.001)-1
        errors += [abs(hold-episode.hold_return),abs(sale-episode.sale_return)]
        assert errors[-1] < 1e-9 and errors[-2] < 1e-9
    summary = pd.read_csv(path/'paired_summary.csv')
    for r in summary.itertuples():
        q = complete.loc[complete.policy.eq(r.policy)]
        if r.period=='1994_2009': q=q.loc[q.entry_date.dt.year.le(2009)]
        elif r.period=='2010_2017': q=q.loc[q.entry_date.dt.year.between(2010,2017)]
        elif r.period=='2018_end': q=q.loc[q.entry_date.dt.year.ge(2018)]
        elif r.period=='2023_end': q=q.loc[q.entry_date.dt.year.ge(2023)]
        assert len(q)==r.complete_pairs
        assert np.isclose((q.hold_return-q.sale_return).mean(),r.mean_hold_minus_sale)
        assert np.isclose((q.hold_return>q.sale_return).mean(),r.hold_ahead_frequency)
    result = dict(raw_path_sample=len(sample),raw_path_max_return_error=max(errors),
        full_dollar_decompositions=len(events),summary_rows=len(summary),passed=True)
    (path/'independent_verification.json').write_text(json.dumps(result,indent=2))
    print(result)


if __name__ == '__main__':
    main(sys.argv[1])
