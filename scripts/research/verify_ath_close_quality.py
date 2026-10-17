"""Independent raw OHLC closing-location checks and summary reconciliation."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from audit_ath_baseline import sha256  # noqa: E402


def main():
    out = Path(sys.argv[1])
    manifest = json.loads((out/'manifest.json').read_text())
    for name, digest in manifest['artifacts'].items():
        assert sha256(out/name) == digest
    z = pd.read_parquet(out/'events.parquet')
    source = pd.read_parquet(ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z/events.parquet')
    original = source.loc[source.common_momentum & source.quintile_6_1.eq(5)].set_index('event_id')
    assert z.event_id.is_unique and set(z.event_id) == set(original.index)
    for col in ['stock_return', 'spy_return', 'excess_spy', 'momentum_6_1', 'nonoverlap']:
        assert np.allclose(z[col], original[col].reindex(z.event_id), equal_nan=True)
    raw_checks = 0
    for year, e in z.groupby(z.date.dt.year):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        assert sha256(path) == manifest['inputs'][str(path.relative_to(ROOT))]
        raw = pd.read_parquet(path, columns=['permno', 'date', 'high', 'low', 'close']).set_index(['date', 'permno'])
        selected = raw.reindex(pd.MultiIndex.from_frame(e[['date', 'permno']]))
        for col in ['high', 'low', 'close']:
            assert np.allclose(e[f'signal_{col}'], selected[col], equal_nan=True)
        for row, r in zip(e.itertuples(), selected.itertuples()):
            h, l, c = r.high, r.low, r.close
            value = np.nan
            if not all(np.isfinite([h, l, c])) or min(h, l, c) <= 0:
                status = 'missing_or_nonpositive'
            elif h < l or c < l or c > h:
                status = 'inconsistent_ohlc'
            elif h == l:
                status = 'zero_range'
            else:
                status = 'ok'
                value = (c-l)/(h-l)
            assert status == row.quality_status
            assert np.isclose(value, row.close_quality, equal_nan=True, atol=1e-12)
            raw_checks += 2
    annual = z.loc[z.excess_spy.notna()]
    base = annual.loc[annual.close_quality.notna()]
    s = pd.read_csv(out/'summary.csv', dtype={'period': str})
    checks = 0
    for r in s.itertuples():
        f = base if r.weighting == 'all' else base.loc[base.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        reference = f
        if r.minimum >= 0:
            f = f.loc[f.close_quality >= r.minimum-1e-12]
        assert len(f) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), f[col].mean(), equal_nan=True, atol=1e-12)
            checks += 1
        assert np.isclose(r.improvement, f.excess_spy.mean()-reference.excess_spy.mean(), equal_nan=True)
        for level in [1, 2, 3]:
            count = f.stock_return.ge(level-1e-12).sum()
            denom = reference.stock_return.ge(level-1e-12).sum()
            assert count == getattr(r, f'winners_{level*100}')
            assert np.isclose(count/denom if denom else np.nan, getattr(r, f'retention_{level*100}'), equal_nan=True)
            checks += 2
    main = s.loc[s.weighting.eq('all') & s.period.eq('all') & s.minimum.ge(0)].sort_values('minimum')
    assert len(main) == 4 and main.events.diff().dropna().le(0).all()
    bands = pd.read_csv(out/'quality_bands.csv')
    assert bands.events.sum() == len(base)
    assert np.isclose((bands.events*bands.excess).sum()/len(base), base.excess_spy.mean())
    codes = sum(base.close_quality.ge(t-1e-12).astype(int) for t in [.5, .7, .85, .95])
    for i, row in enumerate(bands.itertuples()):
        selected = base.loc[codes.eq(i)]
        assert len(selected) == row.events
        assert np.isclose(selected.excess_spy.mean(), row.excess, equal_nan=True)
    for i, threshold in enumerate([.5, .7, .85, .95]):
        expected = s.loc[s.weighting.eq('all') & s.period.eq('all') & s.minimum.eq(threshold), 'events'].iloc[0]
        assert bands.iloc[i+1:].events.sum() == expected
    coverage = pd.read_csv(out/'coverage.csv').set_index('sample')
    assert coverage.loc['feature_observed', 'events'] == len(base)
    assert coverage.loc[['feature_observed', 'zero_range', 'missing_or_nonpositive', 'inconsistent_ohlc'], 'events'].sum() == len(annual)
    result = dict(status='passed', summary_checks=checks, all_raw_feature_checks=raw_checks,
        frozen_source_events=len(z), common_annual_events=len(base),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
