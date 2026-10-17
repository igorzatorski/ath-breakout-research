"""Independent interval lookup, peer-count ranks and outcome reconciliation."""
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
    for col in ['stock_return', 'spy_return', 'excess_spy', 'momentum_6_1', 'quintile_6_1', 'common_momentum', 'permno', 'permco', 'nonoverlap']:
        assert np.allclose(z[col], original[col].reindex(z.event_id), equal_nan=True)
    raw_checks, peer_checks = 0, 0
    h = pd.read_parquet(ROOT/'outputs/research/ath/shared_inputs/industry_history_v001/sic_history.parquet')
    h['start'] = pd.to_datetime(h.effective_from)
    h['end'] = pd.to_datetime(h.effective_to)
    histories = {int(p): f.reset_index(drop=True) for p, f in h.groupby('permno')}
    mapping = {}
    group = None
    text = (ROOT/'outputs/research/ath/shared_inputs/industry_history_v001/Siccodes12.txt').read_text()
    for line in text.splitlines():
        pieces = line.split()
        if not pieces:
            continue
        if '-' in pieces[0] and len(pieces[0]) == 9:
            lo, hi = map(int, pieces[0].split('-'))
            mapping.update({code: group for code in range(lo, hi+1)})
        elif pieces[0].isdigit():
            group = int(pieces[0])
    for year, e in z.groupby(z.date.dt.year):
        pool = pd.read_parquet(out/f'by_year/ranking_{year}.parquet')
        frozen_path = ROOT/f'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z/by_year/ranking_pool_6_1_{year}.parquet'
        assert sha256(frozen_path) == manifest['inputs'][str(frozen_path.relative_to(ROOT))]
        frozen = pd.read_parquet(frozen_path)
        for col in frozen.columns:
            pd.testing.assert_series_equal(pool[col].reset_index(drop=True), frozen[col].reset_index(drop=True))
        for permno, f in pool.groupby('permno'):
            history = histories.get(int(permno))
            expected_industry = np.zeros(len(f), int)
            expected_status = np.full(len(f), 'no_interval', dtype=object)
            if history is not None:
                intervals = pd.IntervalIndex.from_arrays(history.start, history.end, closed='both')
                loc = intervals.get_indexer(f.date)
                for i, position in enumerate(loc):
                    if position >= 0:
                        code = history.siccd.iloc[position]
                        valid = pd.notna(code) and 100 <= code <= 9998 and int(code) == code
                        expected_industry[i] = mapping.get(int(code), 12) if valid else 0
                        expected_status[i] = 'classified' if valid else 'invalid_sic'
            assert np.array_equal(expected_industry, f.industry)
            assert np.array_equal(expected_status, f.classification_status)
            raw_checks += 2*len(f)
        for _, f in pool.loc[pool.industry.gt(0)].groupby(['date', 'industry']):
            values = np.sort(f.momentum.to_numpy())
            less = np.searchsorted(values, f.momentum, side='left')
            equal = np.searchsorted(values, f.momentum, side='right')-less
            expected = (less+equal/2)/len(f)
            assert np.allclose(expected, f.industry_percentile, atol=1e-12)
            assert f.industry_peers.eq(len(f)).all()
            assert f.industry_supported.eq(len(f) >= 20).all()
            peer_checks += 3*len(f)
        missing = pool.industry.eq(0)
        assert pool.loc[missing, 'industry_percentile'].isna().all()
        ep = e[['date', 'permno']].merge(pool, on=['date', 'permno'], how='left', validate='one_to_one')
        for col in ['industry', 'industry_peers', 'industry_percentile', 'industry_supported', 'siccd']:
            assert np.allclose(e[col], ep[col], equal_nan=True)
        print(f'Independent industry checks {year}', flush=True)
    base = z.loc[z.excess_spy.notna() & z.feature_complete]
    assert len(z.loc[z.excess_spy.notna()]) == 23712
    summary = pd.read_csv(out/'summary.csv', dtype={'period': str})
    checks = 0
    for r in summary.itertuples():
        f = base if r.weighting == 'all' else base.loc[base.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        reference = f
        if r.minimum >= 0:
            f = f.loc[f.industry_percentile.gt(r.minimum)]
        assert len(f) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), f[col].mean(), equal_nan=True)
            checks += 1
        assert np.isclose(r.improvement, f.excess_spy.mean()-reference.excess_spy.mean(), equal_nan=True)
        for level in [1, 2, 3]:
            count = f.stock_return.ge(level-1e-12).sum()
            denom = reference.stock_return.ge(level-1e-12).sum()
            assert count == getattr(r, f'winners_{level*100}')
            assert np.isclose(count/denom if denom else np.nan, getattr(r, f'retention_{level*100}'), equal_nan=True)
            checks += 2
    complements = pd.read_csv(out/'complement_summary.csv', dtype={'period': str})
    for r in complements.itertuples():
        f = base if r.weighting == 'all' else base.loc[base.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        removed = f.loc[~f.industry_percentile.gt(r.minimum)]
        assert len(removed) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), removed[col].mean(), equal_nan=True)
            checks += 1
    main = summary.loc[summary.weighting.eq('all') & summary.period.eq('all') & summary.minimum.ge(0)].sort_values('minimum')
    assert main.events.diff().dropna().le(0).all()
    industries = pd.read_csv(out/'by_industry.csv')
    for minimum, rows in industries.groupby('minimum'):
        f = base if minimum < 0 else base.loc[base.industry_percentile.gt(minimum)]
        assert rows.events.sum() == len(f)
        assert np.isclose((rows.events*rows.excess).sum()/len(f), f.excess_spy.mean())
    coverage = pd.read_csv(out/'coverage.csv').set_index('sample')
    assert coverage.loc['common_features', 'events'] == len(base)
    assert coverage.loc['original', 'events'] == coverage.loc[['common_features', 'missing_features'], 'events'].sum()
    result = dict(status='passed', raw_classification_checks=raw_checks, peer_rank_checks=peer_checks, summary_checks=checks,
        frozen_events=len(z), annual_events=len(base), missing_annual_features=23712-len(base),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
