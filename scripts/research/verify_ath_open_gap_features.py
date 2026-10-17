"""Scalar raw ATR and signal-close audit for all modern entry candidates."""
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
    e = pd.read_parquet(run / 'signals.parquet')
    e = e.loc[e.date.ge('2007-12-31')]
    ids = np.load(run / 'security_ids.npy').tolist()
    original = ROOT / 'outputs/research/ath/ath_24_breakout_strength_v001/20261016T225642807548Z'
    source = json.loads((original / 'manifest.json').read_text())
    inputs, tail, checked = {}, None, 0
    for year in range(2007, 2027):
        path = ROOT / f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        digest = sha256(path)
        assert digest == source['inputs'][str(path.relative_to(ROOT))]
        inputs[str(path.relative_to(ROOT))] = digest
        raw = pd.read_parquet(path, columns=['date', 'permno', 'high', 'low', 'close', 'price_adjustment_factor'],
            filters=[('permno', 'in', ids)])
        factor = raw.price_adjustment_factor.where(raw.price_adjustment_factor.gt(0))
        for key in ['high', 'low', 'close']:
            raw[key] = (raw[key] / factor).where(raw[key].gt(0))
        g = e.loc[e.date.dt.year.eq(year)]
        joined = raw if tail is None else pd.concat([tail, raw])
        cal = valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31')
        groups = {sid: f.set_index('date')[['high', 'low', 'close']].reindex(cal).to_numpy()
                  for sid, f in joined.loc[joined.permno.isin(g.permno)].groupby('permno')}
        for row in g.itertuples():
            values = groups[row.permno]
            end = cal.get_loc(row.date)
            ranges = []
            for j in range(end - 20, end):
                high, low, close = values[j]
                previous = values[j-1, 2]
                valid = np.isfinite([high, low, close, previous]).all() and min(high, low, close, previous) > 0 and low <= close <= high
                ranges.append(max(high-low, abs(high-previous), abs(low-previous)) if valid else np.nan)
            atr = sum(ranges) / 20
            assert np.isclose(atr, row.atr20_prior, rtol=1e-11)
            assert np.isclose(values[end, 2], row.signal_close, rtol=1e-11)
            checked += 1
        tail = raw
    result = dict(candidate_raw_windows=checked, inputs=inputs, passed=True)
    (run / 'raw_entry_feature_verification.json').write_text(json.dumps(result, indent=2))
    print(dict(candidate_raw_windows=checked, passed=True))


if __name__ == '__main__':
    main(sys.argv[1])
