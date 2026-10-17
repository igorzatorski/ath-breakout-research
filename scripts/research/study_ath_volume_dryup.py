"""Fifteen pre-breakout volume filters on frozen ATH momentum annual events."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.volume_dryup import HALVES, CELLS, volume_features, comparable_volume, mask  # noqa: E402
from ath_breakout.research.filter_grid import joint_grid_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_19_volume_dryup_v001'


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
    tail, features, scalar = None, [], 0
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        d = checked(path, manifest['inputs'][str(path.relative_to(ROOT))],
                    ['permno', 'date', 'volume', 'share_adjustment_factor'])
        d['p'] = comparable_volume(d.volume, d.share_adjustment_factor)
        current = d[['permno', 'date', 'p']]
        if year >= 1994:
            e = events.loc[events.date.dt.year.eq(year), ['event_id', 'permno', 'date']].copy()
            ids = e.permno.unique()
            lb = pd.concat([tail.loc[tail.permno.isin(ids)], current.loc[current.permno.isin(ids)]], ignore_index=True)
            volumes = lb.pivot(index='date', columns='permno', values='p').reindex(
                valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31'))
            ix = pd.MultiIndex.from_frame(e[['date', 'permno']])
            for half in HALVES:
                early, recent, ratio = volume_features(volumes, half)
                for name, arr in [('early', early), ('recent', recent), ('ratio', ratio)]:
                    e[f'{name}_{half}'] = arr.stack().reindex(ix).to_numpy()
                for row in e.iloc[np.linspace(0, max(0, len(e)-1), min(5, len(e)), dtype=int)].itertuples():
                    pos = volumes.index.get_loc(row.date)
                    a = volumes[row.permno].iloc[pos-2*half:pos-half].to_numpy()
                    b = volumes[row.permno].iloc[pos-half:pos].to_numpy()
                    aw = a.mean() if len(a) == half and np.isfinite(a).all() else np.nan
                    bw = b.mean() if len(b) == half and np.isfinite(b).all() else np.nan
                    expected = bw/aw if np.isfinite(aw) and aw > 0 and np.isfinite(bw) else np.nan
                    assert np.isclose(expected, getattr(row, f'ratio_{half}'), equal_nan=True)
                    scalar += 1
            features.append(e.drop(columns=['date', 'permno']))
            print(f'Volume dry-up {year}: {len(e)} signals', flush=True)
        tail = current
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    z['period'] = period_labels(z.date)
    z['feature_complete'] = z[[f'ratio_{n}' for n in HALVES]].notna().all(axis=1)
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.feature_complete]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in [('original', annual), ('common_features', base),
        ('missing_features', annual.loc[~annual.feature_complete])]]).to_csv(out/'coverage.csv', index=False)
    audit = []
    for n in HALVES:
        missing_volume = annual[[f'early_{n}', f'recent_{n}']].isna().any(axis=1)
        zero = ~missing_volume & annual[f'early_{n}'].le(0)
        audit.append(dict(half=n, total_sessions=2*n, annual_events=len(annual), missing_volume=int(missing_volume.sum()),
            zero_early_mean=int(zero.sum()), observed_ratio=int(annual[f'ratio_{n}'].notna().sum())))
    pd.DataFrame(audit).to_csv(out/'feature_audit.csv', index=False)
    summary, uncertainty = [], []
    labels = [(0, 0.)]+CELLS
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                          *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            for half, ratio in labels:
                keep = g.loc[mask(g, half, ratio)]
                row = dict(weighting=weighting, period=period, half=half, total_sessions=2*half, ratio=ratio,
                    improvement=keep.excess_spy.mean()-g.excess_spy.mean(), sample_skew=keep.stock_return.skew(),
                    median_stock=keep.stock_return.median(), **describe(keep))
                for level in [1, 2, 3]:
                    winners = keep.stock_return.ge(level-1e-12)
                    available = g.stock_return.ge(level-1e-12).sum()
                    row[f'winners_{level*100}'] = int(winners.sum())
                    row[f'fraction_{level*100}'] = winners.mean()
                    row[f'retention_{level*100}'] = winners.sum()/available if available else np.nan
                summary.append(row)
        cal = valid_nyse_sessions(f.date.min(), f.date.max())
        groups = np.column_stack([mask(f, n, r) for n, r in labels])
        for block in [252, 504]:
            print(f'Joint bootstrap {weighting} block={block}', flush=True)
            uncertainty.extend(dict(weighting=weighting, **r) for r in joint_grid_intervals(f, groups,
                [dict(half=n, total_sessions=2*n, ratio=r) for n, r in labels], cal, block=block))
    s = pd.DataFrame(summary)
    s.to_csv(out/'summary.csv', index=False)
    pd.DataFrame(uncertainty).to_csv(out/'uncertainty.csv', index=False)
    gradients = []
    for (weighting, period), f in s.loc[s.half.gt(0)].groupby(['weighting', 'period']):
        for axis, fixed in [('ratio', 'half'), ('half', 'ratio')]:
            for value, group in f.groupby(fixed):
                group = group.sort_values(axis)
                for a, b in zip(group.iloc[:-1].itertuples(), group.iloc[1:].itertuples()):
                    gradients.append(dict(weighting=weighting, period=period, axis=axis, fixed=value,
                        start=getattr(a, axis), end=getattr(b, axis), delta_excess=b.excess-a.excess,
                        events_start=a.events, events_end=b.events))
    pd.DataFrame(gradients).to_csv(out/'adjacent_contrasts.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/volume_dryup.py', ROOT/'src/ath_breakout/research/filter_grid.py',
            ROOT/'src/ath_breakout/research/consolidation_grid.py', ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id=STUDY, cells=CELLS, scalar_feature_checks=scalar, baseline_events=len(base),
        original_annual_events=len(annual), inputs=inputs, seed=20261016, draws=2000, blocks=[252, 504],
        code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        protocol_sha256=sha256(ROOT/'research/ath/ATH_VOLUME_DRYUP_PLAN.md'),
        source_manifest_sha256=sha256(SOURCE/'manifest.json'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
