"""Independent scalar raw signal windows and same-date momentum/MV ranks."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402


def main(run):
    run = Path(run)
    prep = json.loads((run / 'preparation.json').read_text())
    signals = pd.read_parquet(run / 'signals.parquet')
    ids = np.load(run / 'security_ids.npy').tolist()
    high_tail, raw_tail, checked, pools_checked = None, None, 0, 0
    for year in range(2005, 2027):
        path = ROOT / f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        assert sha256(path) == prep['inputs'][str(path.relative_to(ROOT))]
        d = pd.read_parquet(path, columns=['permno', 'date', 'high', 'close', 'volume',
            'price_adjustment_factor', 'share_adjustment_factor', 'total_return'], filters=[('permno', 'in', ids)])
        factor = d.price_adjustment_factor.where(d.price_adjustment_factor.gt(0))
        d['c'] = (d.close/factor).where(d.close.gt(0))
        d['h'] = (d.high/factor).where(d.high.gt(0) & (d.close.isna() | d.high.ge(d.close)))
        d['v'] = (d.volume*d.share_adjustment_factor).where(d.volume.ge(0) & d.share_adjustment_factor.gt(0))
        calendar = valid_nyse_sessions(f'{year}-01-01', min(pd.Timestamp(f'{year}-12-31'), pd.Timestamp('2026-06-30')))
        high = d.pivot(index='date', columns='permno', values='h').reindex(index=calendar, columns=ids)
        all_high = high if high_tail is None else pd.concat([high_tail, high])
        if year >= 2007:
            e = signals.loc[signals.date.dt.year.eq(year)]
            lb = d if raw_tail is None else pd.concat([raw_tail, d])
            cal = valid_nyse_sessions(f'{year-1}-01-01', min(pd.Timestamp(f'{year}-12-31'), pd.Timestamp('2026-06-30')))
            matrices = {key: lb.pivot(index='date', columns='permno', values=key).reindex(index=cal, columns=ids).to_numpy()
                        for key in ['c', 'v', 'total_return']}
            ix = {sid: j for j, sid in enumerate(ids)}
            hvalues = all_high.to_numpy()
            for row in e.itertuples():
                j, t = ix[row.permno], cal.get_loc(row.date)
                hpos = all_high.index.get_loc(row.date)
                assert np.isclose(row.adjusted_close, matrices['c'][t, j])
                if row.definition.startswith('high2y'):
                    window = 504
                    values = hvalues[hpos-window:hpos, j]
                    assert len(values) == window and np.isfinite(values).all()
                    assert np.isclose(values.max(), row.prior_high)
                assert row.adjusted_close > row.prior_high
                assert row.is_ath == bool(row.adjusted_close > row.prior_ath)
                returns = matrices['total_return'][t-125:t-20, j]
                assert len(returns) == 105 and np.isfinite(returns).all() and (returns >= -1).all()
                assert np.isclose(np.prod(1+returns)-1, row.momentum_6_1, rtol=1e-9, atol=1e-10)
                long_returns = matrices['total_return'][t-251:t-20,j]
                assert len(long_returns)==231 and np.isfinite(long_returns).all()
                assert np.isclose(np.prod(1+long_returns)-1,row.momentum_12_1,rtol=1e-9,atol=1e-10)
                volume = matrices['v'][t-63:t, j]
                assert len(volume) == 63 and np.isfinite(volume).all()
                assert np.isclose(matrices['v'][t, j]/volume.mean(), row.volume_ratio_63)
                first, second = matrices['c'][t-84:t-42, j], matrices['c'][t-42:t, j]
                ratio = (second.max()/second.min()-1)/(first.max()/first.min()-1)
                assert np.isclose(ratio, row.contraction_42)
                checked += 1
            pool = pd.read_parquet(run / f'pools/{year}.parquet')
            count = pool.groupby('date').momentum.transform('size')
            rank = (pool.groupby('date').momentum.rank(method='average')-.5)/count
            assert np.array_equal(count, pool.rank_population)
            assert np.array_equal(np.ceil(5*rank).clip(1, 5), pool.quintile)
            joined = e.merge(pool[['date', 'permno', 'momentum', 'quintile']].rename(columns={'quintile':'market_quintile'}), on=['date', 'permno'], validate='many_to_one')
            assert len(joined)==len(e) and joined.quintile.eq(joined.market_quintile).all()
            assert joined.loc[joined.definition.str.endswith('top20'),'quintile'].eq(5).all()
            assert np.allclose(joined.momentum_6_1, joined.momentum)
            for _, g in e.groupby(['definition', 'date']):
                n = len(g)
                m = (g.momentum_6_1.rank(method='average')-.5)/n
                v = (g.volume_ratio_63.clip(upper=2).rank(method='average')-.5)/n
                assert np.allclose(g.score_MV, (m+v)/2)
            pools_checked += len(pool)
            print(f'Raw/rank audit {year}: {len(e)} signal windows', flush=True)
        high_tail = all_high.tail(504)
        raw_tail = d if year >= 2006 else None
    result = dict(raw_signal_windows=checked, pool_rank_rows=pools_checked, passed=True)
    (run / 'independent_signal_verification.json').write_text(json.dumps(result, indent=2))
    print(result)


if __name__ == '__main__':
    main(sys.argv[1])
