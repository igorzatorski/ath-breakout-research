"""Exactly 25 past-close consolidation filters on frozen annual ATH outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.consolidation_grid import LENGTHS, CELLS, past_width, grid_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_15_consolidation_grid_v001'


def describe(f):
    return dict(events=len(f), companies=f.permco.nunique(), stock=f.stock_return.mean(), spy=f.spy_return.mean(),
        excess=f.excess_spy.mean(), median=f.excess_spy.median(), loss=f.stock_return.lt(0).mean(),
        underperform=f.excess_spy.lt(0).mean(), equal_company=f.groupby('permco').excess_spy.mean().mean(),
        equal_date=f.groupby('date').excess_spy.mean().mean(), sparse=len(f) < 100)


def main():
    out = ROOT/f'outputs/research/ath/{STUDY}/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    print(out, flush=True)
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    inputs = {}

    def checked(path, expected, columns=None):
        assert sha256(path) == expected, path
        inputs[str(path.relative_to(ROOT))] = expected
        return pd.read_parquet(path, columns=columns)

    original = checked(SOURCE/'events.parquet', manifest['artifacts']['events.parquet'])
    events = original.loc[original.common_momentum & original.quintile_6_1.eq(5)].copy()
    tail, features, scalar = None, [], 0
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        d = checked(path, manifest['inputs'][str(path.relative_to(ROOT))],
                    ['permno', 'date', 'close', 'price_adjustment_factor'])
        factor = d.price_adjustment_factor
        d['adjusted_close'] = (d.close/factor).where(np.isfinite(factor) & factor.gt(0) & np.isfinite(d.close) & d.close.gt(0))
        current = d[['permno', 'date', 'adjusted_close']]
        if year >= 1994:
            e = events.loc[events.date.dt.year.eq(year), ['event_id', 'permno', 'date']].copy()
            lb = pd.concat([tail, current], ignore_index=True)
            prices = lb.pivot(index='date', columns='permno', values='adjusted_close').reindex(
                valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31'))
            ix = pd.MultiIndex.from_frame(e[['date', 'permno']])
            for length in LENGTHS:
                result = past_width(prices, length)
                e[f'width_{length}'] = result.stack().reindex(ix).to_numpy()
                # Direct array slice independent of the rolling feature implementation.
                for row in e.iloc[np.linspace(0, max(0, len(e)-1), min(5, len(e)), dtype=int)].itertuples():
                    pos = prices.index.get_loc(row.date)
                    window = prices[row.permno].iloc[pos-length:pos].to_numpy()
                    expected = window.max()/window.min()-1 if len(window) == length and np.isfinite(window).all() and (window > 0).all() else np.nan
                    actual = e.loc[e.event_id.eq(row.event_id), f'width_{length}'].iloc[0]
                    assert np.isclose(expected, actual, equal_nan=True, atol=1e-12)
                    scalar += 1
            features.append(e.drop(columns=['date', 'permno']))
            print(f'Features {year}: {len(e)} signals', flush=True)
        tail = current
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    z['period'] = period_labels(z.date)
    z['feature_complete'] = z[[f'width_{n}' for n in LENGTHS]].notna().all(axis=1)
    z.to_parquet(out/'events.parquet', index=False)
    original_base = z.loc[z.excess_spy.notna()]
    assert len(original_base) == 23712
    base = original_base.loc[original_base.feature_complete]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in [('original', original_base), ('common_features', base),
        ('missing_features', original_base.loc[~original_base.feature_complete])]]).to_csv(out/'coverage.csv', index=False)
    summary, uncertainty = [], []
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                          *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            for length, width in [(0, 0.)]+CELLS:
                selected = g if length == 0 else g.loc[g[f'width_{length}'].le(width+1e-12)]
                summary.append(dict(weighting=weighting, period=period, length=length, width=width,
                    baseline_excess=g.excess_spy.mean(), improvement=selected.excess_spy.mean()-g.excess_spy.mean(), **describe(selected)))
        cal = valid_nyse_sessions(f.date.min(), f.date.max())
        for block in [252, 504]:
            print(f'Joint bootstrap {weighting} block={block}', flush=True)
            uncertainty.extend(dict(weighting=weighting, **r) for r in grid_intervals(f, cal, block=block))
    s = pd.DataFrame(summary)
    s.to_csv(out/'summary.csv', index=False)
    pd.DataFrame(uncertainty).to_csv(out/'uncertainty.csv', index=False)
    gradients = []
    for (weighting, period), f in s.loc[s.length.gt(0)].groupby(['weighting', 'period']):
        for axis, fixed, varied in [('width', 'length', 'width'), ('length', 'width', 'length')]:
            for value, group in f.groupby(fixed):
                group = group.sort_values(varied)
                for a, b in zip(group.iloc[:-1].itertuples(), group.iloc[1:].itertuples()):
                    gradients.append(dict(weighting=weighting, period=period, axis=axis, fixed=value,
                        start=getattr(a, varied), end=getattr(b, varied), delta_excess=b.excess-a.excess,
                        events_start=a.events, events_end=b.events))
    pd.DataFrame(gradients).to_csv(out/'adjacent_contrasts.csv', index=False)
    config = dict(study_id=STUDY, cells=CELLS, scalar_feature_checks=scalar, draws=2000, seed=20261016,
                  baseline_events=len(base), original_annual_events=len(original_base), horizon=252,
                  split_adjusted_closing_ranges=True, excludes_signal_day=True, exploratory=True)
    result = dict(config=config, inputs=inputs, source_manifest_sha256=sha256(SOURCE/'manifest.json'),
        protocol_sha256=sha256(ROOT/'research/ath/ATH_CONSOLIDATION_GRID_PLAN.md'),
        code={str(p.relative_to(ROOT)): sha256(p) for p in [Path(__file__), ROOT/'src/ath_breakout/research/consolidation_grid.py']})
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
