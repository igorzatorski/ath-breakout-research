"""Independent direct scheduled-window SMA and outcome reconciliation."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
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
    tail = None
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        assert sha256(path) == manifest['inputs'][str(path.relative_to(ROOT))]
        raw = pd.read_parquet(path, columns=['permno', 'date', 'close', 'price_adjustment_factor'])
        factor = raw.price_adjustment_factor
        raw['p'] = (raw.close/factor).where(np.isfinite(factor) & factor.gt(0) & np.isfinite(raw.close) & raw.close.gt(0))
        current = raw[['permno', 'date', 'p']]
        e = z.loc[z.date.dt.year.eq(year)]
        if len(e):
            d = pd.concat([tail, current], ignore_index=True)
            cal = valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31')
            groups = {p: f.set_index('date').p.reindex(cal).to_numpy() for p, f in d.loc[d.permno.isin(e.permno)].groupby('permno')}
            for r in e.itertuples():
                values = groups[r.permno]
                end = cal.get_loc(r.date)+1
                assert np.isclose(values[end-1], r.signal_close, equal_nan=True)
                means = {}
                for n in [20, 50, 100, 200]:
                    window = values[end-n:end]
                    means[n] = sum(window)/n if len(window) == n and np.isfinite(window).all() else np.nan
                    assert np.isclose(means[n], getattr(r, f'sma_{n}'), equal_nan=True, rtol=1e-12)
                    raw_checks += 1
                def gt(a, b):
                    return bool(np.isfinite(a) and np.isfinite(b) and a-b > 1e-12*max(abs(a), abs(b)))
                expected = {f'price_gt{n}': gt(values[end-1], means[n]) for n in means}
                expected['sma100_gt200'] = gt(means[100], means[200])
                expected['sma50_gt100_gt200'] = gt(means[50], means[100]) and gt(means[100], means[200])
                for name, value in expected.items():
                    assert getattr(r, name) == value
                    raw_checks += 1
                assert r.feature_complete == all(np.isfinite(x) for x in [values[end-1], *means.values()])
        tail = current
    base = z.loc[z.excess_spy.notna() & z.feature_complete]
    assert len(z.loc[z.excess_spy.notna()]) == 23712
    assert (~base.sma50_gt100_gt200 | base.sma100_gt200).all()
    summary = pd.read_csv(out/'summary.csv', dtype={'period': str})
    checks = 0
    for r in summary.itertuples():
        f = base if r.weighting == 'all' else base.loc[base.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        reference = f
        if r.filter != 'reference':
            f = f.loc[f[r.filter]]
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
        removed = f.loc[~f[r.filter]]
        assert len(removed) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), removed[col].mean(), equal_nan=True)
            checks += 1
    audit = pd.read_csv(out/'feature_audit.csv')
    assert (audit.naturally_pass+audit.naturally_fail+audit.missing).eq(23712).all()
    assert (audit.common_pass+audit.common_fail).eq(len(base)).all()
    result = dict(status='passed', raw_sma_and_membership_checks=raw_checks, summary_checks=checks,
        frozen_events=len(z), annual_events=len(base), missing_annual_features=23712-len(base),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
