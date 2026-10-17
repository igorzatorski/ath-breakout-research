"""Reconstruct ATH28 held prices and moving averages independently from raw CRSP."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main(path):
    path = Path(path)
    ids = np.load(path/'security_ids.npy')
    ix = {int(s): i for i, s in enumerate(ids)}
    held = pd.concat([pd.read_parquet(d/'holdings.parquet')[['date', 'permno']] for d in path.glob('*bps')]).drop_duplicates()
    missing_sma = 0
    checked = 0
    tail = None
    for year in range(1993, 2027):
        d = pd.read_parquet(ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet',
            columns=['date', 'permno', 'close', 'price_adjustment_factor'], filters=[('permno', 'in', ids.tolist())])
        d['adjusted'] = d.close/d.price_adjustment_factor
        d.loc[~np.isfinite(d.adjusted) | d.adjusted.le(0), 'adjusted'] = np.nan
        if year == 1993:
            # Actual exchange calendar; avoid counting non-trading dates.
            sys.path.insert(0, str(ROOT/'src'))
            from ath_breakout.data.market_calendar import valid_nyse_sessions
            calendar = valid_nyse_sessions('1993-01-01', '1993-12-31')
        else:
            with np.load(path/f'panels/{year}.npz') as z:
                calendar = pd.DatetimeIndex(z['dates'])
                saved_close, saved_sma = z['close'], z['sma']
        raw = d.pivot(index='date', columns='permno', values='adjusted').reindex(index=calendar, columns=ids)
        combined = pd.concat([tail, raw]) if tail is not None else raw
        if year > 1993:
            rolling = combined.rolling(window=50, min_periods=50).mean().reindex(calendar)
            assert np.allclose(raw.to_numpy(), saved_close, equal_nan=True)
            assert np.allclose(rolling.to_numpy(), saved_sma, equal_nan=True)
            dates = {date: i for i, date in enumerate(calendar)}
            selected = held.loc[held.date.dt.year.eq(year)]
            for r in selected.itertuples():
                missing_sma += not np.isfinite(saved_sma[dates[r.date], ix[int(r.permno)]])
            checked += saved_close.size
        tail = raw.tail(49)
    result = dict(raw_close_and_sma_cells=checked, unique_held_missing_sma_days=int(missing_sma), passed=True)
    (path/'raw_panel_verification.json').write_text(json.dumps(result, indent=2))
    print(result)


if __name__ == '__main__':
    main(sys.argv[1])
