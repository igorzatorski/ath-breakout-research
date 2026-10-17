"""Five prior-ATH record ages with explicit pre-1993 unknown-date handling."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.record_age import MINIMUM_AGES, previous_record_positions, classified, mask, band_codes  # noqa: E402
from ath_breakout.research.filter_grid import joint_grid_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from study_ath_signal import bounds  # noqa: E402
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_22_record_age_v001'


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
    seeded = set(prior)
    cal = valid_nyse_sessions('1992-12-31', '2026-12-31')
    seed_end = cal.get_loc(pd.Timestamp('1992-12-31'))
    carried, features = {}, []
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        d = checked(path, manifest['inputs'][str(path.relative_to(ROOT))],
            ['permno', 'date', 'high', 'close', 'price_adjustment_factor', 'delisting_flag']).sort_values(['permno', 'date']).reset_index(drop=True)
        _, _, observed, _ = bounds(d)
        d['observed_bound'] = observed
        cumulative = d.groupby('permno').observed_bound.cummax().groupby(d.permno).ffill()
        d['prior_ath'] = np.fmax(cumulative.groupby(d.permno).shift(), d.permno.map(prior))
        positions = cal.get_indexer(d.date)
        assert (positions >= 0).all()
        before, carried = previous_record_positions(d, positions, carried)
        d['age_exact'] = positions-before
        unknown_seed = before.isna() & d.permno.isin(seeded) & d.prior_ath.notna()
        d['age_lower_bound'] = d.age_exact.where(~unknown_seed, positions-seed_end)
        d['age_censored'] = unknown_seed
        d['previous_record_date'] = pd.NaT
        known = before.notna()
        d.loc[known, 'previous_record_date'] = cal[before.loc[known].astype(int)].to_numpy()
        e = events.loc[events.date.dt.year.eq(year)]
        if len(e):
            q = e[['event_id', 'permno', 'date', 'prior_ath']].merge(d[['permno', 'date', 'prior_ath', 'age_exact',
                'age_lower_bound', 'age_censored', 'previous_record_date']], on=['permno', 'date'],
                how='left', validate='one_to_one', suffixes=('_source', ''))
            assert np.allclose(q.prior_ath, q.prior_ath_source, equal_nan=True)
            assert q.age_exact.dropna().ge(1).all()
            features.append(q[['event_id', 'age_exact', 'age_lower_bound', 'age_censored', 'previous_record_date']])
            print(f'Record age {year}: {len(e)} signals', flush=True)
        for p, h in d.groupby('permno').observed_bound.max().dropna().items():
            prior[p] = max(prior.get(p, h), h)
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    z['period'] = period_labels(z.date)
    z['age_classified'] = classified(z)
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.age_classified]
    availability = [('original', annual), ('classified', base), ('exact_date', annual.loc[annual.age_exact.notna()]),
        ('seed_date_unknown_classified', annual.loc[annual.age_censored & annual.age_classified]),
        ('unclassified', annual.loc[~annual.age_classified])]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in availability]).to_csv(out/'coverage.csv', index=False)
    z.assign(annual_available=z.excess_spy.notna()).groupby(['age_censored', 'age_classified', 'annual_available']).size().rename('events').to_csv(out/'age_audit.csv')
    summaries, intervals = [], []
    labels = [-1]+MINIMUM_AGES
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                          *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            for minimum in labels:
                keep = g.loc[mask(g, minimum)]
                row = dict(weighting=weighting, period=period, minimum=minimum, improvement=keep.excess_spy.mean()-g.excess_spy.mean(),
                    median_stock=keep.stock_return.median(), sample_skew=keep.stock_return.skew(), **describe(keep))
                for level in [1, 2, 3]:
                    count = keep.stock_return.ge(level-1e-12).sum()
                    available = g.stock_return.ge(level-1e-12).sum()
                    row[f'winners_{level*100}'] = int(count)
                    row[f'fraction_{level*100}'] = count/len(keep) if len(keep) else np.nan
                    row[f'retention_{level*100}'] = count/available if available else np.nan
                summaries.append(row)
        groups = np.column_stack([mask(f, n) for n in labels])
        for block in [252, 504]:
            print(f'Bootstrap {weighting} block={block}', flush=True)
            intervals.extend(dict(weighting=weighting, **r) for r in joint_grid_intervals(f, groups,
                [dict(minimum=n) for n in labels], valid_nyse_sessions(f.date.min(), f.date.max()), block=block))
    s = pd.DataFrame(summaries)
    s.to_csv(out/'summary.csv', index=False)
    pd.DataFrame(intervals).to_csv(out/'uncertainty.csv', index=False)
    codes = band_codes(base)
    bands = ['1_to4', '5_to20', '21_to62', '63_to125', '126_to251', 'ge252']
    pd.DataFrame([dict(band=label, censored_events=int(base.loc[codes == i, 'age_censored'].sum()),
        **describe(base.loc[codes == i])) for i, label in enumerate(bands)]).to_csv(out/'age_bands.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/record_age.py', ROOT/'src/ath_breakout/research/filter_grid.py',
            ROOT/'scripts/research/study_ath_signal.py', ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id=STUDY, minimum_ages=MINIMUM_AGES, baseline_events=len(base), inputs=inputs, seed=20261016,
        draws=2000, blocks=[252, 504], code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        protocol_sha256=sha256(ROOT/'research/ath/ATH_RECORD_AGE_PLAN.md'), source_manifest_sha256=sha256(SOURCE/'manifest.json'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
