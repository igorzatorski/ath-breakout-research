"""Independent signal-day volume and prior-mean checks on saved ATH outcomes."""
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
            raw = pd.read_parquet(path, columns=['permno', 'date', 'volume', 'share_adjustment_factor'])
            frames.append(raw.loc[raw.permno.isin(ids)])
        raw = pd.concat(frames).set_index(['date', 'permno'])
        for row in sample.itertuples():
            cal = valid_nyse_sessions(pd.Timestamp(row.date)-pd.Timedelta(days=270), row.date)
            prior = cal[cal < row.date]
            for lookback in [5, 10, 21, 42, 63]:
                dates = prior[-lookback:]
                window = raw.reindex(pd.MultiIndex.from_product([dates, [row.permno]]))
                p = (window.volume*window.share_adjustment_factor).where(
                    np.isfinite(window.volume) & window.volume.ge(0) & np.isfinite(window.share_adjustment_factor)
                    & window.share_adjustment_factor.gt(0)).to_numpy()
                aw = p.mean() if len(p) == lookback and np.isfinite(p).all() else np.nan
                signal = raw.loc[(row.date, row.permno)]
                bw = signal.volume*signal.share_adjustment_factor if np.isfinite(signal.volume) and signal.volume >= 0 and np.isfinite(signal.share_adjustment_factor) and signal.share_adjustment_factor > 0 else np.nan
                ratio = bw/aw if np.isfinite(aw) and aw > 0 and np.isfinite(bw) else np.nan
                for name, value in [('prior_mean', aw), ('signal_volume', bw), ('ratio', ratio)]:
                    assert np.isclose(getattr(row, f'{name}_{lookback}'), value, equal_nan=True, atol=1e-12)
                    raw_checks += 1
    lookbacks = [5, 10, 21, 42, 63]
    complete = z[[f'ratio_{n}' for n in lookbacks]].notna().all(axis=1)
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
        if r.lookback:
            f = f.loc[f[f'ratio_{r.lookback}'] >= r.ratio-1e-12]
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
    assert (audit.missing_volume+audit.zero_prior_mean+audit.observed_ratio == audit.annual_events).all()
    for lookback in [10, 21, 42, 63]:
        assert np.allclose(z.signal_volume_5, z[f'signal_volume_{lookback}'], equal_nan=True)
    bands = pd.read_csv(out/'relative_volume_bands.csv')
    for lookback, group in bands.groupby('lookback'):
        observed = pd.cut(base[f'ratio_{lookback}'], [-np.inf, 1., 1.5, 2., 3., np.inf],
            labels=['lt1', '1_to1.5', '1.5_to2', '2_to3', 'ge3'], right=False)
        assert group.events.sum() == len(base)
        assert np.isclose((group.events*group.excess).sum()/len(base), base.excess_spy.mean())
        for row in group.itertuples():
            selected = base.loc[observed.eq(row.band)]
            assert len(selected) == row.events
            assert np.isclose(selected.excess_spy.mean(), row.excess, equal_nan=True)
            checks += 2
    main = s.loc[s.weighting.eq('all') & s.period.eq('all') & s.lookback.gt(0)]
    assert len(main) == 20
    for _, f in main.groupby('lookback'):
        assert f.sort_values('ratio').events.diff().dropna().le(0).all()
    result = dict(status='passed', summary_checks=checks, raw_feature_sample_checks=raw_checks,
        zero_signal_volume_annual=int(z.loc[z.excess_spy.notna(), 'signal_volume_5'].eq(0).sum()),
        frozen_source_events=len(z), common_annual_events=len(base),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
