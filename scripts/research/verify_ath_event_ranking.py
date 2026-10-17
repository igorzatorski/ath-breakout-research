"""Direct count-based score audit, common-date means and draw reconciliation."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402


def close(a, b):
    assert np.allclose(a, b, equal_nan=True, atol=1e-11), (a, b)


def main():
    out = Path(sys.argv[1])
    manifest = json.loads((out/'manifest.json').read_text())
    for name, digest in manifest['inputs'].items():
        assert sha256(ROOT/name) == digest
    for name, digest in manifest['artifacts'].items():
        assert sha256(out/name) == digest
    source_path = next(ROOT/p for p in manifest['inputs'] if p.endswith('events.parquet'))
    raw, z = pd.read_parquet(source_path), pd.read_parquet(out/'events.parquet')
    for col in raw:
        pd.testing.assert_series_equal(raw[col], z[col])
    rank_checks = 0
    valid = np.isfinite(raw[['momentum_6_1', 'volume_ratio_63', 'contraction_42']]).all(axis=1)
    assert np.array_equal(valid, z.ranking_features)
    for _, f in z.loc[valid].groupby('date'):
        components = {}
        for name, values in [('M', f.momentum_6_1.to_numpy()), ('V', np.minimum(f.volume_ratio_63, 2)),
            ('C', -f.contraction_42.to_numpy())]:
            values = np.asarray(values)
            ordered = np.sort(values)
            lo = np.searchsorted(ordered, values, side='left')
            hi = np.searchsorted(ordered, values, side='right')
            components[name] = (lo+(hi-lo)/2)/len(f)
            close(components[name], f[f'component_{name}'])
            rank_checks += len(f)
        scores = {'M': components['M'], 'MV': (components['M']+components['V'])/2,
            'MVC': (components['M']+components['V']+components['C'])/3}
        for name, score in scores.items():
            close(score, f[f'score_{name}'])
            ordered = np.sort(score)
            lo = np.searchsorted(ordered, score, side='left')
            hi = np.searchsorted(ordered, score, side='right')
            rank = (lo+(hi-lo)/2)/len(f)
            close(rank, f[f'rank_{name}'])
            close(np.clip(np.ceil(rank*5), 1, 5), f[f'quintile_{name}'])
            rank_checks += 3*len(f)
        assert f.candidate_count.eq(len(f)).all()
    assert np.array_equal(z.candidate_date_supported, valid & z.candidate_count.ge(5))
    annual = z.loc[z.excess_spy.notna()]
    expected_flags = {}
    for evaluation, nonoverlap, top_only in [('primary', False, False), ('nonoverlap_top', True, True)]:
        f = annual.loc[annual.candidate_date_supported]
        if nonoverlap:
            f = f.loc[f.nonoverlap]
        dates = []
        for date, g in f.groupby('date'):
            required = {5.} if top_only else {1., 2., 3., 4., 5.}
            if all(required.issubset(set(g[f'quintile_{model}'])) for model in ['M', 'MV', 'MVC']):
                dates.append(date)
        mask = z.excess_spy.notna() & z.candidate_date_supported & z.date.isin(dates)
        if nonoverlap:
            mask &= z.nonoverlap
        expected_flags[evaluation] = mask
        field = 'primary_evaluation' if not nonoverlap else 'nonoverlap_top_evaluation'
        assert np.array_equal(mask, z[field])
    summary = pd.read_csv(out/'summary.csv', dtype={'period': str})
    summary_checks = 0
    for (evaluation, period), rows in summary.groupby(['evaluation', 'period']):
        f = z.loc[expected_flags[evaluation]]
        if period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(period)]
        elif period in ['2018_2020', '2021_2022', '2023_partial2025']:
            f = f.loc[f.episode.eq(period)]
        elif period != 'all':
            f = f.loc[f.date.dt.year.eq(int(period))]
        reference = f.groupby('date').excess_spy.mean()
        for r in rows.itertuples():
            g = f if r.group == 'reference' else f.loc[f[f'quintile_{r.group.split("_Q")[0]}'].eq(int(r.group[-1]))]
            dates = g.groupby('date')[['stock_return', 'spy_return', 'excess_spy']].mean()
            assert len(g) == r.events and g.date.nunique() == r.dates and g.permco.nunique() == r.companies
            for field, col in [('stock_equal_date', 'stock_return'), ('spy_equal_date', 'spy_return'), ('excess_equal_date', 'excess_spy')]:
                close(getattr(r, field), dates[col].mean())
                summary_checks += 1
            close(r.improvement_equal_date, (dates.excess_spy-reference).mean())
            for field, col in [('stock', 'stock_return'), ('spy', 'spy_return'), ('excess', 'excess_spy')]:
                close(getattr(r, field), g[col].mean())
                summary_checks += 1
            close(r.median_stock, g.stock_return.median())
            close(r.loss, g.stock_return.lt(0).mean())
            for level in [1, 2, 3]:
                count = g.stock_return.ge(level-1e-12).sum()
                denominator = f.stock_return.ge(level-1e-12).sum()
                assert count == getattr(r, f'winners_{level*100}')
                close(getattr(r, f'fraction_{level*100}'), count/len(g) if len(g) else np.nan)
                close(getattr(r, f'retention_{level*100}'), count/denominator if denominator else np.nan)
                summary_checks += 3
    interval_checks, direct_draw_checks = 0, 0
    all_rows = pd.read_csv(out/'uncertainty.csv')
    for (evaluation, block), rows in all_rows.groupby(['evaluation', 'block'], sort=False):
        f = z.loc[expected_flags[evaluation]]
        top_only = evaluation != 'primary'
        names = ['reference']+[f'{m}_Q{q}' for m in ['M', 'MV', 'MVC'] for q in ([5] if top_only else range(1, 6))]
        membership = [np.ones(len(f), bool)]+[f[f'quintile_{name.split("_Q")[0]}'].eq(int(name[-1])).to_numpy() for name in names[1:]]
        draws = np.load(out/f'draws_{evaluation}_{block}.npz')
        points, samples = draws['points'], draws['samples']
        assert list(draws['groups']) == names
        for i, keep in enumerate(membership):
            close(points[i], f.loc[keep].groupby('date').excess_spy.mean().mean())
        coefficients = np.load(out/f'coefficients_{evaluation}.npy')
        definitions = pd.read_csv(out/f'contrasts_{evaluation}.csv')
        independent = np.zeros_like(coefficients)
        for i, r in enumerate(definitions.itertuples()):
            parts = r.label.split('_')
            terms = []
            if r.kind == 'top_vs_reference':
                terms = [(f'{parts[0]}_Q5', 1), ('reference', -1)]
            elif r.kind == 'spread':
                terms = [(f'{parts[0]}_Q5', 1), (f'{parts[0]}_Q1', -1)]
            elif r.kind == 'incremental_top':
                terms = [(f'{parts[0]}_Q5', 1), (f'{parts[3]}_Q5', -1)]
            elif r.kind == 'incremental_spread':
                terms = [(f'{parts[0]}_Q5', 1), (f'{parts[0]}_Q1', -1), (f'{parts[3]}_Q5', -1), (f'{parts[3]}_Q1', 1)]
            elif r.kind == 'adjacent':
                terms = [(f'{parts[0]}_{parts[1]}', 1), (f'{parts[0]}_{parts[3]}', -1)]
            for name, weight in terms:
                independent[i, names.index(name)] += weight
        close(independent, coefficients)
        values, estimates = samples@independent.T, independent@points
        for i, r in enumerate(rows.itertuples()):
            assert r.label == definitions.label.iloc[i]
            finite = values[:, i][np.isfinite(values[:, i])]
            bounds = np.percentile(finite, [2.5, 97.5]) if len(finite) >= .95*len(samples) else [np.nan]*2
            close(r.estimate, estimates[i])
            close(r.lower95, bounds[0])
            close(r.upper95, bounds[1])
            interval_checks += 3
        for family, keep in [('incremental3', definitions.kind.eq('incremental_top').to_numpy()), ('all', np.ones(len(definitions), bool))]:
            complete = np.isfinite(values[:, keep]).all(axis=1)
            radius = np.percentile(np.abs(values[complete][:, keep]-estimates[keep]).max(axis=1), 95) if complete.mean() >= .95 else np.nan
            for i, r in enumerate(rows.itertuples()):
                close(getattr(r, f'{family}_lower'), estimates[i]-radius if keep[i] else np.nan)
                close(getattr(r, f'{family}_upper'), estimates[i]+radius if keep[i] else np.nan)
                assert getattr(r, f'{family}_complete_draws') == complete.sum()
                interval_checks += 3
        calendar = valid_nyse_sessions(f.date.min(), f.date.max())
        dates = pd.DatetimeIndex(sorted(f.date.unique()))
        company, labels = pd.factorize(f.permco, sort=True)
        rng = np.random.default_rng(20261017)
        lengths = np.minimum(block, len(calendar)-np.arange(0, len(calendar), block))
        for draw_index in range(3):
            starts = rng.integers(0, len(calendar), len(lengths))
            selected = np.concatenate([(start+np.arange(length)) % len(calendar) for start, length in zip(starts, lengths)])
            time_weights = np.bincount(selected, minlength=len(calendar))[calendar.get_indexer(dates)]
            company_weights = rng.exponential(size=len(labels))
            for i, keep in enumerate(membership):
                g = f.loc[keep, ['date', 'excess_spy']].copy()
                g['w'] = company_weights[company[keep]]
                g['wx'] = g.w*g.excess_spy
                sums = g.groupby('date')[['w', 'wx']].sum().reindex(dates)
                means = sums.wx/sums.w
                close(samples[draw_index, i], (means.to_numpy()@time_weights)/time_weights.sum() if time_weights.sum() else np.nan)
                direct_draw_checks += 1
    result = dict(status='passed', source_events=len(z), rank_score_checks=rank_checks, summary_tail_checks=summary_checks,
        interval_checks=interval_checks, direct_company_date_draw_checks=direct_draw_checks,
        common_primary_events=int(z.primary_evaluation.sum()), common_primary_dates=z.loc[z.primary_evaluation, 'date'].nunique(),
        manifest_sha256=sha256(out/'manifest.json'), verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
