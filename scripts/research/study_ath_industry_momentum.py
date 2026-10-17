"""Three frozen within-FF12 momentum filters on annual ATH outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.industry_momentum import THRESHOLDS, MIN_PEERS, sic_mapping, prepare_history, attach_industry, industry_ranks, mask  # noqa: E402
from ath_breakout.research.filter_grid import joint_grid_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_25_industry_momentum_v001'


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
    classification = ROOT/'outputs/research/ath/shared_inputs/industry_history_v001'
    history_path, mapping_path = classification/'sic_history.parquet', classification/'Siccodes12.txt'
    inputs[str(history_path.relative_to(ROOT))] = sha256(history_path)
    inputs[str(mapping_path.relative_to(ROOT))] = sha256(mapping_path)
    history = prepare_history(pd.read_parquet(history_path))
    mapping, names = sic_mapping(mapping_path.read_text())
    features, pool_audit = [], []
    (out/'by_year').mkdir()
    for year, e in events.groupby(events.date.dt.year):
        path = SOURCE/f'by_year/ranking_pool_6_1_{year}.parquet'
        key = str(path.relative_to(SOURCE))
        pool = checked(path, manifest['artifacts'][key])
        assert not pool.duplicated(['date', 'permno']).any()
        zpool = industry_ranks(attach_industry(pool, history, mapping))
        zpool.to_parquet(out/f'by_year/ranking_{year}.parquet', index=False)
        pool_audit.append(dict(year=year, securities_dates=len(pool), classified=int(zpool.industry.gt(0).sum()),
            supported=int(zpool.industry_supported.sum()), no_interval=int(zpool.classification_status.eq('no_interval').sum()),
            invalid_sic=int(zpool.classification_status.eq('invalid_sic').sum())))
        columns = ['date', 'permno', 'siccd', 'effective_from', 'effective_to', 'industry',
            'classification_status', 'industry_peers', 'industry_percentile', 'industry_supported', 'feature_status']
        feature = e[['event_id', 'date', 'permno']].merge(zpool[columns], on=['date', 'permno'], how='left', validate='one_to_one')
        assert feature.industry.notna().all()
        features.append(feature.drop(columns=['date', 'permno']))
        print(f'Within-industry ranking {year}: {len(e)} signals', flush=True)
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    z['feature_complete'] = z.industry_supported
    pd.DataFrame(pool_audit).to_csv(out/'pool_coverage.csv', index=False)
    z['period'] = period_labels(z.date)
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.feature_complete]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in [('original', annual),
        ('common_features', base), ('missing_features', annual.loc[~annual.feature_complete])]]).to_csv(out/'coverage.csv', index=False)
    annual.groupby([annual.date.dt.year.rename('year'), 'feature_status']).size().rename('events').to_csv(out/'feature_audit.csv')
    summaries, intervals, complements = [], [], []
    labels = [-1.]+THRESHOLDS
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                          *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            for name in labels:
                membership = mask(g, name)
                keep = g.loc[membership]
                row = dict(weighting=weighting, period=period, minimum=name,
                    improvement=keep.excess_spy.mean()-g.excess_spy.mean(), median_stock=keep.stock_return.median(),
                    sample_skew=keep.stock_return.skew(), **describe(keep))
                for level in [1, 2, 3]:
                    count = keep.stock_return.ge(level-1e-12).sum()
                    available = g.stock_return.ge(level-1e-12).sum()
                    row[f'winners_{level*100}'] = int(count)
                    row[f'fraction_{level*100}'] = count/len(keep) if len(keep) else np.nan
                    row[f'retention_{level*100}'] = count/available if available else np.nan
                summaries.append(row)
                if name >= 0:
                    complements.append(dict(weighting=weighting, period=period, minimum=name, **describe(g.loc[~membership])))
        groups = np.column_stack([mask(f, name) for name in labels])
        for block in [252, 504]:
            print(f'Joint bootstrap {weighting} block={block}', flush=True)
            intervals.extend(dict(weighting=weighting, **r) for r in joint_grid_intervals(f, groups,
                [dict(minimum=name) for name in labels], valid_nyse_sessions(f.date.min(), f.date.max()), block=block))
    s = pd.DataFrame(summaries)
    s.to_csv(out/'summary.csv', index=False)
    pd.DataFrame(intervals).to_csv(out/'uncertainty.csv', index=False)
    pd.DataFrame(complements).to_csv(out/'complement_summary.csv', index=False)
    industry_rows = []
    for minimum in labels:
        for code_number, f in base.loc[mask(base, minimum)].groupby('industry'):
            industry_rows.append(dict(minimum=minimum, industry=code_number, name=names[code_number], **describe(f)))
    pd.DataFrame(industry_rows).to_csv(out/'by_industry.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/industry_momentum.py', ROOT/'src/ath_breakout/research/filter_grid.py',
            ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id=STUDY, thresholds=THRESHOLDS, min_peers=MIN_PEERS, industries=names, baseline_events=len(base), original_annual_events=len(annual),
        inputs=inputs, seed=20261016, draws=2000, blocks=[252, 504],
        code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        source_manifest_sha256=sha256(SOURCE/'manifest.json'),
        protocol_sha256=sha256(ROOT/'research/ath/ATH_INDUSTRY_MOMENTUM_PLAN.md'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.rglob('*') if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
