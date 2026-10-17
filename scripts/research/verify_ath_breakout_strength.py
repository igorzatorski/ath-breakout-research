"""Independent scalar true ranges, ATR and frozen outcome reconciliation."""
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
    for col in ['stock_return', 'spy_return', 'excess_spy', 'momentum_6_1', 'quintile_6_1', 'common_momentum', 'permno', 'permco', 'nonoverlap']:
        assert np.allclose(z[col], original[col].reindex(z.event_id), equal_nan=True)
    raw_checks = 0
    tail = None
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        assert sha256(path) == manifest['inputs'][str(path.relative_to(ROOT))]
        raw = pd.read_parquet(path, columns=['permno', 'date', 'high', 'low', 'close', 'price_adjustment_factor'])
        factor = raw.price_adjustment_factor
        factor = factor.where(np.isfinite(factor) & factor.gt(0))
        for c in ['high', 'low', 'close']:
            raw[c] = (raw[c]/factor).where(np.isfinite(raw[c]) & raw[c].gt(0))
        current = raw[['permno', 'date', 'high', 'low', 'close']]
        e = z.loc[z.date.dt.year.eq(year)]
        if len(e):
            d = pd.concat([tail, current], ignore_index=True)
            cal = valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31')
            groups = {p: f.set_index('date')[['high', 'low', 'close']].reindex(cal).to_numpy()
                for p, f in d.loc[d.permno.isin(e.permno)].groupby('permno')}
            for r in e.itertuples():
                values = groups[r.permno]
                end = cal.get_loc(r.date)
                trs = []
                for i in range(end-20, end):
                    h, l, c = values[i]
                    previous = values[i-1, 2]
                    valid = all(np.isfinite([h, l, c, previous])) and min(h, l, c, previous) > 0 and l <= c <= h
                    trs.append(max(h-l, abs(h-previous), abs(l-previous)) if valid else np.nan)
                atr = sum(trs)/20 if np.isfinite(trs).all() else np.nan
                close = values[end, 2]
                overshoot = close-r.prior_ath
                strength = overshoot/atr if np.isfinite(atr) and atr > 0 and overshoot > 0 else np.nan
                for expected, saved in [(close, r.signal_close), (atr, r.atr20_prior),
                    (overshoot, r.overshoot), (strength, r.breakout_strength)]:
                    assert np.isclose(expected, saved, equal_nan=True, rtol=1e-11)
                    raw_checks += 1
                assert r.feature_complete == bool(np.isfinite(strength))
        tail = current
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
            f = f.loc[f.breakout_strength.ge(r.minimum-1e-12)]
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
        removed = f.loc[~f.breakout_strength.ge(r.minimum-1e-12)]
        assert len(removed) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), removed[col].mean(), equal_nan=True)
            checks += 1
    codes = sum(base.breakout_strength.ge(t-1e-12).astype(int) for t in [.1, .25, .5, 1., 2.])
    bands = pd.read_csv(out/'strength_bands.csv')
    assert bands.events.sum() == len(base)
    assert np.isclose((bands.events*bands.excess).sum()/len(base), base.excess_spy.mean())
    for i, r in enumerate(bands.itertuples()):
        selected = base.loc[codes.eq(i)]
        assert len(selected) == r.events
        assert np.isclose(selected.excess_spy.mean(), r.excess, equal_nan=True)
    main = summary.loc[summary.weighting.eq('all') & summary.period.eq('all') & summary.minimum.ge(0)].sort_values('minimum')
    assert main.events.diff().dropna().le(0).all()
    for i, r in enumerate(main.itertuples()):
        assert bands.iloc[i+1:].events.sum() == r.events
    result = dict(status='passed', raw_close_atr_overshoot_strength_checks=raw_checks, summary_checks=checks,
        frozen_events=len(z), annual_events=len(base), missing_annual_features=23712-len(base),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
