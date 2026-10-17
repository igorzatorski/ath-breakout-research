"""Independent raw fixed-anchor samples, population and summary reconciliations."""
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
    carry = dict(zip(seed.loc[np.isfinite(values), 'permno'], values[np.isfinite(values)]))
    previous, previous_start = None, None
    raw_checks = 0
    for year in range(1993, 2027):
        start = carry.copy()
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        assert sha256(path) == manifest['inputs'][str(path.relative_to(ROOT))]
        d = pd.read_parquet(path, columns=['permno', 'date', 'close', 'high', 'price_adjustment_factor'])
        valid_factor = np.isfinite(d.price_adjustment_factor) & d.price_adjustment_factor.gt(0)
        close_ok = valid_factor & np.isfinite(d.close) & d.close.gt(0)
        high_ok = valid_factor & np.isfinite(d.high) & d.high.gt(0) & (d.close.isna() | d.high.ge(d.close))
        d['p'] = (d.close/d.price_adjustment_factor).where(close_ok)
        d['h'] = np.fmax(d.p, (d.high/d.price_adjustment_factor).where(high_ok))
        group = z.loc[z.date.dt.year.eq(year)]
        if len(group):
            sample = group.iloc[np.linspace(0, len(group)-1, min(8, len(group)), dtype=int)]
            lb = pd.concat([previous, d], ignore_index=True).set_index(['date', 'permno'])
            for row in sample.itertuples():
                cal = valid_nyse_sessions(pd.Timestamp(row.date)-pd.Timedelta(days=160), row.date)
                prior_dates = cal[cal < row.date]
                for n in [10, 21, 42, 63]:
                    dates = prior_dates[-n:]
                    first = dates[0]
                    history = d if first.year == year else previous
                    initial = start if first.year == year else previous_start
                    observed = history.loc[history.permno.eq(row.permno) & history.date.lt(first), 'h'].max()
                    anchor = np.fmax(initial.get(row.permno, np.nan), observed)
                    prices = lb.p.reindex(pd.MultiIndex.from_product([dates, [row.permno]])).to_numpy()
                    okay = len(prices) == n and np.isfinite(prices).all() and (prices > 0).all()
                    low, high = (prices.min(), prices.max()) if okay else (np.nan, np.nan)
                    depth = 1-low/anchor if np.isfinite(anchor) and anchor > 0 else np.nan
                    for name, value in [('anchor', anchor), ('low', low), ('high', high), ('depth', depth)]:
                        assert np.isclose(getattr(row, f'{name}_{n}'), value, equal_nan=True, atol=1e-12)
                        raw_checks += 1
                    assert getattr(row, f'upper_{n}') == (okay and np.isfinite(anchor) and anchor > 0 and high <= anchor*(1+1e-12))
                    raw_checks += 1
        for p, h in d.groupby('permno').h.max().dropna().items():
            carry[p] = max(carry.get(p, h), h)
        previous, previous_start = d, start
    annual = z.loc[z.excess_spy.notna()]
    base = annual.loc[annual.feature_complete]
    summaries = pd.read_csv(out/'summary.csv', dtype={'period': str})
    checks = 0
    for r in summaries.itertuples():
        f = base if r.weighting == 'all' else base.loc[base.nonoverlap]
        if r.period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(r.period)]
        elif r.period != 'all':
            f = f.loc[f.date.dt.year.eq(int(r.period))]
        baseline = f.excess_spy.mean()
        anchor = f if r.length == 0 else f.loc[f[f'upper_{r.length}']]
        keep = anchor if r.depth <= 0 else anchor.loc[anchor[f'depth_{r.length}'] <= r.depth+1e-12]
        assert len(keep) == r.events
        for label, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
            assert np.isclose(getattr(r, label), keep[col].mean(), equal_nan=True, atol=1e-12)
            checks += 1
        assert np.isclose(r.improvement, keep.excess_spy.mean()-baseline, equal_nan=True)
        assert np.isclose(r.minus_anchor_only, keep.excess_spy.mean()-anchor.excess_spy.mean(), equal_nan=True)
    audit = pd.read_csv(out/'exclusion_audit.csv')
    assert (audit.missing+audit.prior_closing_breakout+audit.too_deep+audit.passing == audit.annual).all()
    main = summaries.loc[summaries.weighting.eq('all') & summaries.period.eq('all') & summaries.depth.gt(0)]
    assert len(main) == 16
    for _, f in main.groupby('length'):
        assert f.sort_values('depth').events.diff().dropna().ge(0).all()
    result = dict(status='passed', summary_mean_checks=checks, raw_feature_sample_checks=raw_checks,
        frozen_source_events=len(z), common_annual_events=len(base),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
