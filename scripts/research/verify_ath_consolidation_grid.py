"""Independent saved-grid reconciliation and direct raw-window checks."""
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
    for c in ['stock_return', 'spy_return', 'excess_spy', 'nonoverlap', 'momentum_6_1']:
        assert np.allclose(z[c], original[c].reindex(z.event_id), equal_nan=True)
    lengths = [10, 21, 42, 63, 126]
    for a, b in zip(lengths[:-1], lengths[1:]):
        both = z[[f'width_{a}', f'width_{b}']].notna().all(axis=1)
        assert (z.loc[both, f'width_{b}'] >= z.loc[both, f'width_{a}']-1e-12).all()
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
            cal = valid_nyse_sessions(pd.Timestamp(row.date)-pd.Timedelta(days=260), row.date)
            prior = cal[cal < row.date]
            for n in lengths:
                window = raw.reindex(pd.MultiIndex.from_product([prior[-n:], [row.permno]]))
                prices = (window.close/window.price_adjustment_factor).to_numpy()
                valid = (len(prices) == n and np.isfinite(prices).all() and (prices > 0).all()
                         and window.price_adjustment_factor.gt(0).all())
                expected = prices.max()/prices.min()-1 if valid else np.nan
                assert np.isclose(getattr(row, f'width_{n}'), expected, equal_nan=True, atol=1e-12)
                raw_checks += 1
    base = z.loc[z.excess_spy.notna() & z.feature_complete]
    s = pd.read_csv(out/'summary.csv', dtype={'period': str})
    checks = 0
    for r in s.itertuples():
        f = base if r.weighting == 'all' else base.loc[base.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        bmean = f.excess_spy.mean()
        if r.length:
            f = f.loc[f[f'width_{r.length}'] <= r.width+1e-12]
        assert len(f) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), f[col].mean(), equal_nan=True, atol=1e-12)
            checks += 1
        assert np.isclose(r.improvement, f.excess_spy.mean()-bmean, equal_nan=True)
        assert np.isclose(r.stock-r.spy, r.excess, equal_nan=True)
    main = s.loc[s.weighting.eq('all') & s.period.eq('all') & s.length.gt(0)]
    assert len(main) == 25
    for length, f in main.groupby('length'):
        assert f.sort_values('width').events.diff().dropna().ge(0).all()
    result = dict(status='passed', summary_mean_checks=checks, raw_window_sample_checks=raw_checks,
                  frozen_events=len(z), common_annual_events=len(base),
                  manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
