"""Full fixed81 neighborhood of four previously inspected entry candidates."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.filter_combinations import (  # noqa: E402
    STATES, config_name, memberships, indicators, contrasts, bootstrap_means, contrast_intervals,
)
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCES = {
    'C': 'ath_18_range_contraction_v001/20261016T220702501000Z',
    'V': 'ath_20_breakout_volume_v001/20261016T221719577843Z',
    'A': 'ath_22_record_age_v001/20261016T223810045721Z',
    'B': 'ath_24_breakout_strength_v001/20261016T225642807548Z',
}


def concentration(f):
    n, net = len(f), f.excess_spy.sum()
    company = f.groupby('permco').excess_spy.agg(['sum', 'size'])
    year = f.groupby(f.date.dt.year).excess_spy.agg(['sum', 'size'])
    pos = company.loc[company['sum'].gt(0)].sort_values('sum', ascending=False)
    leave_company = (net-company['sum'])/(n-company['size']).replace(0, np.nan)
    leave_year = (net-year['sum'])/(n-year['size']).replace(0, np.nan)
    remove = pos.head(5)
    return dict(top1_excess_share=pos['sum'].head(1).sum()/net if net > 0 else np.nan,
        top5_excess_share=remove['sum'].sum()/net if net > 0 else np.nan,
        effective_companies=n*n/(company['size']**2).sum() if n else np.nan,
        leave_company_min=leave_company.min(), leave_company_max=leave_company.max(),
        leave_year_min=leave_year.min(), leave_year_max=leave_year.max(),
        remove_top5_excess=(net-remove['sum'].sum())/(n-remove['size'].sum()) if n > remove['size'].sum() else np.nan)


def main():
    out = ROOT/f'outputs/research/ath/ath_26_filter_combinations_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    print(out, flush=True)
    inputs = {}
    z = None
    for key, directory in SOURCES.items():
        folder = ROOT/'outputs/research/ath'/directory
        manifest = json.loads((folder/'manifest.json').read_text())
        path = folder/'events.parquet'
        assert sha256(path) == manifest['artifacts']['events.parquet']
        inputs[str(path.relative_to(ROOT))] = sha256(path)
        inputs[str((folder/'manifest.json').relative_to(ROOT))] = sha256(folder/'manifest.json')
        f = pd.read_parquet(path)
        if z is None:
            z = f.drop(columns=[c for c in f if c.startswith(('ratio_', 'early_', 'recent_'))]).copy()
            z = z.merge(f[['event_id', 'ratio_42', 'ratio_63']].rename(columns={
                'ratio_42': 'contraction_42', 'ratio_63': 'contraction_63'}), on='event_id', validate='one_to_one')
        else:
            source = f.set_index('event_id').reindex(z.event_id)
            assert set(f.event_id) == set(z.event_id)
            for col in ['stock_return', 'spy_return', 'excess_spy', 'nonoverlap', 'permno', 'permco', 'quintile_6_1']:
                assert np.allclose(z[col], source[col], equal_nan=True)
            columns = {'V': ['ratio_63'], 'A': ['age_exact', 'age_lower_bound', 'age_censored', 'age_classified'],
                'B': ['breakout_strength']}[key]
            extra = f[['event_id']+columns].rename(columns={'ratio_63': 'volume_ratio_63'})
            z = z.merge(extra, on='event_id', validate='one_to_one')
    complete = z[['contraction_42', 'contraction_63', 'volume_ratio_63', 'breakout_strength']].notna().all(axis=1)
    z['combination_support'] = complete & z.age_classified
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.combination_support]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in [('original', annual), ('common', base),
        ('unsupported', annual.loc[~annual.combination_support])]]).to_csv(out/'coverage.csv', index=False)
    options = indicators(base)
    overlap = []
    for a, x in options.items():
        for b, y in options.items():
            both, union = int((x & y).sum()), int((x | y).sum())
            overlap.append(dict(first=a, second=b, first_count=int(x.sum()), second_count=int(y.sum()), intersection=both,
                union=union, jaccard=both/union if union else np.nan, second_given_first=both/x.sum() if x.sum() else np.nan,
                phi=np.corrcoef(x, y)[0, 1] if x.std() > 0 and y.std() > 0 else np.nan))
    pd.DataFrame(overlap).to_csv(out/'overlap.csv', index=False)
    main_flags = np.column_stack([options[f'{name}2'] for name in 'CVAB'])
    signature = main_flags@(2**np.arange(4))
    pd.DataFrame([dict(signature=i, main_passes=int(i).bit_count(), **describe(base.loc[signature == i]))
        for i in range(16)]).to_csv(out/'exclusive_signatures.csv', index=False)
    pd.DataFrame([dict(main_passes=i, **describe(base.loc[main_flags.sum(axis=1) == i]))
        for i in range(5)]).to_csv(out/'pass_counts.csv', index=False)
    edges = contrasts()
    edges.to_csv(out/'contrast_definitions.csv', index=False)
    summaries, diagnostics, uncertainty = [], [], []
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        g = memberships(f)
        for period, sample in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
            *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            group = memberships(sample)
            ref = sample.excess_spy.mean()
            for i, state in enumerate(STATES):
                keep = sample.loc[group[:, i]]
                row = dict(weighting=weighting, period=period, config=config_name(state), main=all(x in [0, 2] for x in state),
                    filters=sum(x > 0 for x in state), improvement=keep.excess_spy.mean()-ref,
                    median_stock=keep.stock_return.median(), sample_skew=keep.stock_return.skew(), **describe(keep))
                row['limited_support'] = row['events'] < 200 or row['companies'] < 50
                for level in [1, 2, 3]:
                    win = keep.stock_return.ge(level-1e-12)
                    available = sample.stock_return.ge(level-1e-12).sum()
                    row[f'winners_{level*100}'] = int(win.sum())
                    row[f'fraction_{level*100}'] = win.mean()
                    row[f'retention_{level*100}'] = win.sum()/available if available else np.nan
                    row[f'tail_contribution_{level*100}'] = keep.loc[win, 'stock_return'].sum()/len(keep) if len(keep) else np.nan
                summaries.append(row)
                if period == 'all':
                    diagnostics.append(dict(weighting=weighting, config=config_name(state), **concentration(keep)))
        counts = g.sum(axis=0)
        points = np.divide(g.T@f.excess_spy.to_numpy(), counts, out=np.full(len(STATES), np.nan), where=counts > 0)
        for block in [252, 504]:
            print(f'Joint81 bootstrap {weighting} block{block}', flush=True)
            samples = bootstrap_means(f, g, valid_nyse_sessions(f.date.min(), f.date.max()), block=block)
            np.savez_compressed(out/f'draws_{weighting}_{block}.npz', points=points, samples=samples)
            rows = contrast_intervals(points, samples, edges)
            rows.insert(0, 'weighting', weighting)
            rows.insert(1, 'block', block)
            uncertainty.append(rows)
    summary = pd.DataFrame(summaries)
    summary.to_csv(out/'summary.csv', index=False)
    pd.DataFrame(diagnostics).to_csv(out/'concentration.csv', index=False)
    pd.concat(uncertainty, ignore_index=True).to_csv(out/'uncertainty.csv', index=False)
    print(summary.loc[summary.weighting.eq('all') & summary.period.eq('all') & summary.main,
        ['config', 'events', 'stock', 'spy', 'excess', 'improvement', 'limited_support']].to_string(index=False), flush=True)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/filter_combinations.py',
        ROOT/'scripts/research/study_ath_consolidation_grid.py']
    manifest = dict(study_id='ath_26_filter_combinations_v001', inputs=inputs, draws=2000, seed=20261017, blocks=[252, 504],
        configurations=81, main_configurations=16, contrasts=len(edges),
        code={str(p.relative_to(ROOT)): sha256(p) for p in code}, protocol_sha256=sha256(ROOT/'research/ath/ATH_FILTER_COMBINATIONS_PLAN.md'))
    manifest['artifacts'] = {p.name: sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(out, flush=True)


if __name__ == '__main__':
    main()
