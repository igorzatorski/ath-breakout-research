"""Four closing-location filters on frozen ATH momentum annual outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.close_quality import THRESHOLDS, closing_location, mask, band_codes  # noqa: E402
from ath_breakout.research.filter_grid import joint_grid_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_21_close_quality_v001'


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
    features = []
    for year, e in events.groupby(events.date.dt.year):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        raw = checked(path, manifest['inputs'][str(path.relative_to(ROOT))], ['permno', 'date', 'high', 'low', 'close'])
        p = e[['event_id', 'permno', 'date']].merge(raw, on=['permno', 'date'], how='left', validate='one_to_one')
        f = closing_location(p)
        f.insert(0, 'event_id', p.event_id)
        for col in ['high', 'low', 'close']:
            f[f'signal_{col}'] = p[col]
        features.append(f)
        print(f'Closing location {year}: {len(f)} signals', flush=True)
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    z['period'] = period_labels(z.date)
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.close_quality.notna()]
    availability = [dict(sample='original', **describe(annual)), dict(sample='feature_observed', **describe(base))]
    for status in ['zero_range', 'missing_or_nonpositive', 'inconsistent_ohlc']:
        availability.append(dict(sample=status, **describe(annual.loc[annual.quality_status.eq(status)])))
    pd.DataFrame(availability).to_csv(out/'coverage.csv', index=False)
    z.assign(outcome_available=z.excess_spy.notna()).groupby(['quality_status', 'outcome_available']).size().rename('events').to_csv(out/'quality_audit.csv')
    summaries, intervals, gradients = [], [], []
    labels = [-1.]+THRESHOLDS
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                          *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            for threshold in labels:
                keep = g.loc[mask(g, threshold)]
                row = dict(weighting=weighting, period=period, minimum=threshold,
                    improvement=keep.excess_spy.mean()-g.excess_spy.mean(), median_stock=keep.stock_return.median(),
                    sample_skew=keep.stock_return.skew(), **describe(keep))
                for level in [1, 2, 3]:
                    count = keep.stock_return.ge(level-1e-12).sum()
                    available = g.stock_return.ge(level-1e-12).sum()
                    row[f'winners_{level*100}'] = int(count)
                    row[f'fraction_{level*100}'] = count/len(keep) if len(keep) else np.nan
                    row[f'retention_{level*100}'] = count/available if available else np.nan
                summaries.append(row)
        cal = valid_nyse_sessions(f.date.min(), f.date.max())
        groups = np.column_stack([mask(f, t) for t in labels])
        for block in [252, 504]:
            print(f'Joint bootstrap {weighting} block={block}', flush=True)
            intervals.extend(dict(weighting=weighting, **r) for r in joint_grid_intervals(f, groups,
                [dict(minimum=t) for t in labels], cal, block=block))
    s = pd.DataFrame(summaries)
    s.to_csv(out/'summary.csv', index=False)
    pd.DataFrame(intervals).to_csv(out/'uncertainty.csv', index=False)
    for (weighting, period), f in s.loc[s.minimum.ge(0)].groupby(['weighting', 'period']):
        ordered = f.sort_values('minimum')
        for a, b in zip(ordered.iloc[:-1].itertuples(), ordered.iloc[1:].itertuples()):
            gradients.append(dict(weighting=weighting, period=period, start=a.minimum, end=b.minimum,
                delta_excess=b.excess-a.excess, events_start=a.events, events_end=b.events))
    pd.DataFrame(gradients).to_csv(out/'adjacent_contrasts.csv', index=False)
    codes = band_codes(base)
    bands = ['lt50', '50_to70', '70_to85', '85_to95', 'ge95']
    pd.DataFrame([dict(band=label, **describe(base.loc[codes == i]))
        for i, label in enumerate(bands)]).to_csv(out/'quality_bands.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/close_quality.py', ROOT/'src/ath_breakout/research/filter_grid.py',
            ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id=STUDY, thresholds=THRESHOLDS, baseline_events=len(base), original_annual_events=len(annual),
        inputs=inputs, seed=20261016, draws=2000, blocks=[252, 504],
        code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        source_manifest_sha256=sha256(SOURCE/'manifest.json'),
        protocol_sha256=sha256(ROOT/'research/ath/ATH_CLOSE_QUALITY_PLAN.md'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
