"""Independent prefix-maximum record dates and frozen-outcome reconciliation."""
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
    seed = pd.read_parquet(ROOT/'outputs/research/ath/shared_inputs/high_seed_before_1993.parquet')
    values = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    levels = dict(zip(seed.loc[np.isfinite(values), 'permno'], values[np.isfinite(values)]))
    dates = {}
    cal = valid_nyse_sessions('1992-12-31', '2026-12-31')
    raw_checks = 0
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        assert sha256(path) == manifest['inputs'][str(path.relative_to(ROOT))]
        raw = pd.read_parquet(path, columns=['permno', 'date', 'high', 'close', 'price_adjustment_factor'])
        factor = raw.price_adjustment_factor.where(np.isfinite(raw.price_adjustment_factor) & raw.price_adjustment_factor.gt(0))
        close = raw.close.where(np.isfinite(raw.close) & raw.close.gt(0))/factor
        high = raw.high.where(np.isfinite(raw.high) & raw.high.gt(0) & (raw.close.isna() | raw.high.ge(raw.close)))/factor
        raw['bound'] = np.fmax(close, high)
        events = z.loc[z.date.dt.year.eq(year)]
        selected = pd.concat([events.head(4), events.tail(4), events.loc[events.age_censored].head(4)]).drop_duplicates('event_id')
        for r in selected.itertuples():
            prefix = raw.loc[raw.permno.eq(r.permno) & raw.date.lt(r.date)]
            maximum = prefix.bound.max()
            previous = levels.get(r.permno, np.nan)
            date = dates.get(r.permno, pd.NaT)
            if np.isfinite(maximum) and (not np.isfinite(previous) or maximum > previous):
                previous = maximum
                date = prefix.loc[prefix.bound.eq(maximum), 'date'].min()
            assert np.isclose(previous, r.prior_ath)
            age = np.nan if pd.isna(date) else cal.get_loc(r.date)-cal.get_loc(date)
            lower = cal.get_loc(r.date) if pd.isna(date) else age
            assert np.isclose(age, r.age_exact, equal_nan=True)
            assert np.isclose(lower, r.age_lower_bound, equal_nan=True)
            assert bool(pd.isna(date)) == r.age_censored
            assert (pd.isna(date) and pd.isna(r.previous_record_date)) or date == r.previous_record_date
            raw_checks += 5
        maxima = raw.groupby('permno').bound.max().dropna()
        winners = raw.loc[raw.bound.eq(raw.permno.map(maxima))].groupby('permno').date.min()
        for p, value in maxima.items():
            if p not in levels or value > levels[p]:
                levels[p] = value
                dates[p] = winners[p]
    base = z.loc[z.excess_spy.notna() & z.age_classified]
    assert len(base) == 23712
    assert base.loc[base.age_censored, 'age_exact'].isna().all()
    assert base.loc[base.age_censored, 'age_lower_bound'].ge(252).all()
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
            f = f.loc[f.age_exact.ge(r.minimum) | (f.age_exact.isna() & f.age_lower_bound.ge(r.minimum))]
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
    bands = pd.read_csv(out/'age_bands.csv')
    assert bands.events.sum() == len(base)
    assert np.isclose((bands.events*bands.excess).sum()/len(base), base.excess_spy.mean())
    main = summary.loc[summary.weighting.eq('all') & summary.period.eq('all') & summary.minimum.ge(0)].sort_values('minimum')
    assert main.events.diff().dropna().le(0).all()
    for i, r in enumerate(main.itertuples()):
        assert bands.iloc[i+1:].events.sum() == r.events
    result = dict(status='passed', raw_prefix_checks=raw_checks, summary_checks=checks,
        frozen_events=len(z), annual_events=len(base), unknown_seed_dates=int(base.age_censored.sum()),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
