"""Sixteen fixed-anchor ATH proximity variants on frozen annual event outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.proximity_grid import LENGTHS, CELLS, proximity_features, selected, joint_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from study_ath_signal import bounds  # noqa: E402
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_16_proximity_grid_v001'


def main():
    out = ROOT/f'outputs/research/ath/{STUDY}/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    print(out, flush=True)
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    inputs = {}

    def checked(path, digest, columns=None):
        assert sha256(path) == digest, path
        inputs[str(path.relative_to(ROOT))] = digest
        return pd.read_parquet(path, columns=columns)

    original = checked(SOURCE/'events.parquet', manifest['artifacts']['events.parquet'])
    events = original.loc[original.common_momentum & original.quintile_6_1.eq(5)].copy()
    seed_path = ROOT/'outputs/research/ath/shared_inputs/high_seed_before_1993.parquet'
    seed = checked(seed_path, manifest['inputs'][str(seed_path.relative_to(ROOT))])
    seed_bound = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    prior = dict(zip(seed.loc[np.isfinite(seed_bound), 'permno'], seed_bound[np.isfinite(seed_bound)]))
    tail, features, scalar = None, [], 0
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        d = checked(path, manifest['inputs'][str(path.relative_to(ROOT))],
            ['permno', 'date', 'close', 'high', 'price_adjustment_factor', 'delisting_flag']).sort_values(['permno', 'date']).reset_index(drop=True)
        close, _, observed, _ = bounds(d)
        d['adjusted_close'], d['observed_bound'] = close, observed
        cumulative = d.groupby('permno').observed_bound.cummax().groupby(d.permno).ffill()
        d['prior_ath'] = np.fmax(cumulative.groupby(d.permno).shift(), d.permno.map(prior))
        current = d[['permno', 'date', 'adjusted_close', 'prior_ath']]
        if year >= 1994:
            e = events.loc[events.date.dt.year.eq(year), ['event_id', 'permno', 'date', 'prior_ath']].copy()
            ids = e.permno.unique()
            lb = pd.concat([tail.loc[tail.permno.isin(ids)], current.loc[current.permno.isin(ids)]], ignore_index=True)
            cal = valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31')
            prices = lb.pivot(index='date', columns='permno', values='adjusted_close').reindex(cal)
            aths = lb.pivot(index='date', columns='permno', values='prior_ath').reindex(cal)
            ix = pd.MultiIndex.from_frame(e[['date', 'permno']])
            assert np.allclose(e.prior_ath, aths.stack().reindex(ix), equal_nan=True)
            for length in LENGTHS:
                anchor, low, high, depth = proximity_features(prices, aths, length)
                for name, arr in [('anchor', anchor), ('low', low), ('high', high), ('depth', depth)]:
                    e[f'{name}_{length}'] = arr.stack().reindex(ix).to_numpy()
                e[f'observed_{length}'] = e[[f'anchor_{length}', f'low_{length}', f'high_{length}']].notna().all(axis=1)
                e[f'upper_{length}'] = e[f'observed_{length}'] & e[f'high_{length}'].le(e[f'anchor_{length}']*(1+1e-12))
                for row in e.iloc[np.linspace(0, max(0, len(e)-1), min(5, len(e)), dtype=int)].itertuples():
                    pos = prices.index.get_loc(row.date)
                    a = aths[row.permno].iloc[pos-length]
                    window = prices[row.permno].iloc[pos-length:pos].to_numpy()
                    expected = 1-window.min()/a if len(window) == length and np.isfinite(window).all() and np.isfinite(a) and a > 0 else np.nan
                    assert np.isclose(expected, getattr(row, f'depth_{length}'), equal_nan=True)
                    scalar += 1
            features.append(e.drop(columns=['date', 'permno', 'prior_ath']))
            print(f'Anchors {year}: {len(e)} signals', flush=True)
        for p, h in d.groupby('permno').observed_bound.max().dropna().items():
            prior[p] = max(prior.get(p, h), h)
        tail = current
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    z['period'] = period_labels(z.date)
    z['feature_complete'] = z[[f'observed_{n}' for n in LENGTHS]].all(axis=1)
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.feature_complete]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in [('original', annual), ('common_features', base),
        ('missing_features', annual.loc[~annual.feature_complete])]]).to_csv(out/'coverage.csv', index=False)
    audit = []
    for length, depth in CELLS:
        observed = annual[f'observed_{length}']
        upper = annual[f'upper_{length}']
        passing = selected(annual, length, depth)
        audit.append(dict(length=length, depth=depth, annual=len(annual), missing=int((~observed).sum()),
            prior_closing_breakout=int((observed & ~upper).sum()), too_deep=int((upper & ~passing).sum()), passing=int(passing.sum())))
    pd.DataFrame(audit).to_csv(out/'exclusion_audit.csv', index=False)
    summary, uncertainty = [], []
    labels = [(0, 0.)]+CELLS+[(n, -1.) for n in LENGTHS]
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                          *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            for length, depth in labels:
                keep = g.loc[selected(g, length, depth)]
                anchor_only = g if length == 0 else g.loc[selected(g, length, -1)]
                summary.append(dict(weighting=weighting, period=period, length=length, depth=depth,
                    improvement=keep.excess_spy.mean()-g.excess_spy.mean(),
                    minus_anchor_only=keep.excess_spy.mean()-anchor_only.excess_spy.mean(), **describe(keep)))
        cal = valid_nyse_sessions(f.date.min(), f.date.max())
        for block in [252, 504]:
            print(f'Bootstrap {weighting} block={block}', flush=True)
            uncertainty.extend(dict(weighting=weighting, **r) for r in joint_intervals(f, cal, block=block))
    pd.DataFrame(summary).to_csv(out/'summary.csv', index=False)
    pd.DataFrame(uncertainty).to_csv(out/'uncertainty.csv', index=False)
    gradients = []
    s = pd.DataFrame(summary)
    for (weighting, period), f in s.loc[s.length.gt(0) & s.depth.gt(0)].groupby(['weighting', 'period']):
        for axis, fixed in [('depth', 'length'), ('length', 'depth')]:
            for value, group in f.groupby(fixed):
                group = group.sort_values(axis)
                for a, b in zip(group.iloc[:-1].itertuples(), group.iloc[1:].itertuples()):
                    gradients.append(dict(weighting=weighting, period=period, axis=axis, fixed=value,
                        start=getattr(a, axis), end=getattr(b, axis), delta_excess=b.excess-a.excess,
                        events_start=a.events, events_end=b.events))
    pd.DataFrame(gradients).to_csv(out/'adjacent_contrasts.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/proximity_grid.py', ROOT/'scripts/research/study_ath_signal.py',
            ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id=STUDY, cells=CELLS, scalar_feature_checks=scalar, baseline_events=len(base),
        original_annual_events=len(annual), inputs=inputs, seed=20261016, draws=2000, blocks=[252, 504],
        code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        protocol_sha256=sha256(ROOT/'research/ath/ATH_PROXIMITY_GRID_PLAN.md'),
        source_manifest_sha256=sha256(SOURCE/'manifest.json'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
