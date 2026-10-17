"""Independent raw two-half ranges, common-support and summary reconciliation."""
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
    for year, group in z.groupby(z.date.dt.year):
        sample = group.iloc[np.linspace(0, len(group)-1, min(9, len(group)), dtype=int)]
        ids = sample.permno.unique()
        frames = []
        for y in [year-1, year]:
            path = ROOT/f'data/raw/crsp/daily_by_year/daily_{y}.parquet'
            assert sha256(path) == manifest['inputs'][str(path.relative_to(ROOT))]
            raw = pd.read_parquet(path, columns=['permno', 'date', 'close', 'price_adjustment_factor'])
            frames.append(raw.loc[raw.permno.isin(ids)])
        raw = pd.concat(frames).set_index(['date', 'permno'])
        for row in sample.itertuples():
            cal = valid_nyse_sessions(pd.Timestamp(row.date)-pd.Timedelta(days=270), row.date)
            prior = cal[cal < row.date]
            for half in [5, 10, 21, 42, 63]:
                dates = prior[-2*half:]
                window = raw.reindex(pd.MultiIndex.from_product([dates, [row.permno]]))
                p = (window.close/window.price_adjustment_factor).where(
                    np.isfinite(window.close) & window.close.gt(0) & np.isfinite(window.price_adjustment_factor)
                    & window.price_adjustment_factor.gt(0)).to_numpy()
                a, b = p[:half], p[half:]
                aw = a.max()/a.min()-1 if len(a) == half and np.isfinite(a).all() else np.nan
                bw = b.max()/b.min()-1 if len(b) == half and np.isfinite(b).all() else np.nan
                ratio = bw/aw if np.isfinite(aw) and aw > 1e-12 and np.isfinite(bw) else np.nan
                for name, value in [('early', aw), ('recent', bw), ('ratio', ratio)]:
                    assert np.isclose(getattr(row, f'{name}_{half}'), value, equal_nan=True, atol=1e-12)
                    raw_checks += 1
    halves = [5, 10, 21, 42, 63]
    complete = z[[f'ratio_{n}' for n in halves]].notna().all(axis=1)
    assert complete.equals(z.feature_complete)
    base = z.loc[z.excess_spy.notna() & complete]
    s = pd.read_csv(out/'summary.csv', dtype={'period': str})
    checks = 0
    for r in s.itertuples():
        f = base if r.weighting == 'all' else base.loc[base.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        reference = f
        if r.half:
            f = f.loc[f[f'ratio_{r.half}'] <= r.ratio+1e-12]
        assert len(f) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), f[col].mean(), equal_nan=True, atol=1e-12)
            checks += 1
        assert np.isclose(r.improvement, f.excess_spy.mean()-reference.excess_spy.mean(), equal_nan=True)
        for level in [1, 2, 3]:
            count = f.stock_return.ge(level-1e-12).sum()
            assert count == getattr(r, f'winners_{level*100}')
            denom = reference.stock_return.ge(level-1e-12).sum()
            expected = count/denom if denom else np.nan
            assert np.isclose(expected, getattr(r, f'retention_{level*100}'), equal_nan=True)
            checks += 2
    audit = pd.read_csv(out/'feature_audit.csv')
    assert (audit.missing_prices+audit.zero_early_width+audit.observed_ratio == audit.annual_events).all()
    main = s.loc[s.weighting.eq('all') & s.period.eq('all') & s.half.gt(0)]
    assert len(main) == 15
    for _, f in main.groupby('half'):
        assert f.sort_values('ratio').events.diff().dropna().ge(0).all()
    result = dict(status='passed', summary_checks=checks, raw_feature_sample_checks=raw_checks,
        frozen_source_events=len(z), common_annual_events=len(base),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
