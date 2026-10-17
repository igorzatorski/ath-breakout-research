"""Independent saved-output reconciliation and raw-feature sample checks."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402


def main():
    out = Path(sys.argv[1])
    manifest = json.loads((out/'manifest.json').read_text())
    checks = 0
    for name, digest in manifest['artifacts'].items():
        assert sha256(out/name) == digest, name
        checks += 1
    z = pd.read_parquet(out/'events.parquet')
    q = pd.read_parquet(out/'controls.parquet')
    source_dir = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
    original = pd.read_parquet(source_dir/'events.parquet').set_index('event_id')
    assert z.event_id.is_unique
    expected = original.loc[original.common_momentum]
    assert set(z.event_id) == set(expected.index)
    for col in ['stock_return', 'spy_return', 'excess_spy', 'momentum_6_1', 'quintile_6_1', 'nonoverlap']:
        assert np.allclose(z[col], original[col].reindex(z.event_id), equal_nan=True)
        checks += len(z)
    assert not q.duplicated(['event_id', 'rank']).any()
    assert q.groupby('event_id').size().eq(5).all()
    assert q.groupby('event_id').control_permco.nunique().eq(5).all()
    assert q.control_permco.ne(q.event_permco).all()
    assert q.momentum_gap.abs().le(.1+1e-12).all()
    assert q.size_ratio.between(.5-1e-12, 2+1e-12).all()
    assert q.vol_ratio.between(1/1.5-1e-12, 1.5+1e-12).all()
    assert np.allclose(q.event_momentum, original.momentum_6_1.reindex(q.event_id))
    assert np.allclose(q.control_momentum-q.event_momentum, q.momentum_gap)
    assert np.array_equal(q.event_permco, original.permco.reindex(q.event_id))
    ath_keys = pd.MultiIndex.from_frame(original.reset_index()[['date', 'permno']])
    assert not pd.MultiIndex.from_frame(q[['date', 'permno']]).isin(ath_keys).any()
    means = q.groupby('event_id').value.agg(['count', 'mean'])
    controls = z.event_id.map(means['mean']).where(z.event_id.map(means['count']).eq(5))
    assert np.array_equal(z.matched_at_signal, z.event_id.isin(q.event_id))
    assert np.array_equal(z.valid_controls_6_1, z.event_id.map(means['count']).fillna(0))
    assert np.allclose(z.control_return_6_1, controls, equal_nan=True)
    assert np.allclose(z.incremental_ath, z.stock_return-controls, equal_nan=True)
    raw_feature_checks = 0
    for year, group in q.groupby(q.date.dt.year):
        pool = pd.read_parquet(source_dir/f'by_year/ranking_pool_6_1_{year}.parquet').set_index(['date', 'permno'])
        ix = pd.MultiIndex.from_frame(group[['date', 'permno']])
        assert ix.isin(pool.index).all()
        assert np.allclose(group.control_momentum, pool.momentum.reindex(ix))
        assert np.array_equal(group.control_permco, pool.permco.reindex(ix))
        # Independent scalar 63-observation sample, including year-boundary windows.
        selected = group.iloc[np.linspace(0, len(group)-1, min(6, len(group)), dtype=int)]
        ids = selected.permno.unique()
        raw = pd.concat([pd.read_parquet(ROOT/f'data/raw/crsp/daily_by_year/daily_{y}.parquet',
            columns=['permno', 'date', 'market_cap', 'total_return']) for y in [year-1, year]], ignore_index=True)
        raw = raw.loc[raw.permno.isin(ids)].set_index(['date', 'permno'])
        for row in selected.itertuples():
            calendar = valid_nyse_sessions(pd.Timestamp(row.date)-pd.Timedelta(days=150), row.date)[-63:]
            returns = raw.total_return.reindex(pd.MultiIndex.from_product([calendar, [row.permno]]))
            assert len(returns) == 63 and returns.notna().all()
            vol = returns.std(ddof=1)*np.sqrt(252)
            ev = original.loc[row.event_id]
            assert np.isclose(vol/ev.vol63, row.vol_ratio, atol=1e-9)
            assert np.isclose(raw.loc[(row.date, row.permno), 'market_cap']/ev.market_cap, row.size_ratio)
            raw_feature_checks += 2
        checks += len(group)*3
    summary = pd.read_csv(out/'summary.csv', dtype={'period': str})
    for r in summary.itertuples():
        f = z.loc[z.incremental_ath.notna() & z.excess_spy.notna()]
        if r.sample == 'top20':
            f = f.loc[f.quintile_6_1.eq(5)]
        if r.weighting == 'nonoverlap':
            f = f.loc[f.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        assert len(f) == r.events
        for col, metric in [('stock', 'stock_return'), ('controls', 'control_return_6_1'),
                            ('spy', 'spy_return'), ('incremental', 'incremental_ath')]:
            assert np.isclose(getattr(r, col), f[metric].sum()/len(f))
            checks += 1
        assert np.isclose(r.stock-r.controls, r.incremental)
    result = dict(status='passed', numerical_checks=checks, raw_feature_sample_checks=raw_feature_checks,
                  controls_rows=len(q), frozen_event_rows=len(z),
                  manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
