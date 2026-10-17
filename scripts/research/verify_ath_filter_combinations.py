"""Separate intersections, source reconciliation and stored-draw interval audit."""
from itertools import product
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
    assert np.isclose(a, b, equal_nan=True, atol=1e-11), (a, b)


def main():
    out = Path(sys.argv[1])
    manifest = json.loads((out/'manifest.json').read_text())
    for name, digest in manifest['artifacts'].items():
        assert sha256(out/name) == digest
    for name, digest in manifest['inputs'].items():
        assert sha256(ROOT/name) == digest
    z = pd.read_parquet(out/'events.parquet')
    inputs = [ROOT/p for p in manifest['inputs'] if p.endswith('events.parquet')]
    for path in inputs:
        f = pd.read_parquet(path).set_index('event_id').reindex(z.event_id)
        assert f.index.is_unique and len(f) == len(z)
        for col in ['stock_return', 'spy_return', 'excess_spy', 'permno', 'permco', 'nonoverlap', 'quintile_6_1']:
            assert np.allclose(z[col], f[col], equal_nan=True)
        if 'contraction' in str(path):
            assert np.allclose(z.contraction_42, f.ratio_42, equal_nan=True)
            assert np.allclose(z.contraction_63, f.ratio_63, equal_nan=True)
        elif 'breakout_volume' in str(path):
            assert np.allclose(z.volume_ratio_63, f.ratio_63, equal_nan=True)
        elif 'record_age' in str(path):
            for col in ['age_exact', 'age_lower_bound', 'age_censored', 'age_classified']:
                assert np.allclose(z[col], f[col], equal_nan=True)
        elif 'breakout_strength' in str(path):
            assert np.allclose(z.breakout_strength, f.breakout_strength, equal_nan=True)
    base = z.loc[z.excess_spy.notna() & z.combination_support]
    assert len(base) == 23712
    states = list(product(range(3), repeat=4))
    names = [''.join(f'{letter}{value}' for letter, value in zip('CVAB', state)) for state in states]

    def flags(f):
        age = np.where(f.age_exact.notna(), f.age_exact, f.age_lower_bound)
        return {'C1': f.contraction_42.to_numpy() <= .75+1e-12, 'C2': f.contraction_63.to_numpy() <= .75+1e-12,
            'V1': f.volume_ratio_63.to_numpy() >= 1.5-1e-12, 'V2': f.volume_ratio_63.to_numpy() >= 2.-1e-12,
            'A1': age >= 126, 'A2': age >= 252, 'B1': f.breakout_strength.to_numpy() >= .5-1e-12,
            'B2': f.breakout_strength.to_numpy() >= 1.-1e-12}

    def masks(f):
        options = flags(f)
        result = {}
        for name, state in zip(names, states):
            selected = [options[f'{letter}{level}'] for letter, level in zip('CVAB', state) if level]
            result[name] = np.logical_and.reduce(selected) if selected else np.ones(len(f), bool)
        return result

    checks = 0
    summary = pd.read_csv(out/'summary.csv', dtype={'period': str})
    for (weighting, period), rows in summary.groupby(['weighting', 'period']):
        f = base if weighting == 'all' else base.loc[base.nonoverlap]
        if period in ['early', 'middle', 'recent']:
            f = f.loc[f.period.eq(period)]
        elif period != 'all':
            f = f.loc[f.date.dt.year.eq(int(period))]
        group = masks(f)
        assert set(rows.config) == set(names)
        for r in rows.itertuples():
            selected = f.loc[group[r.config]]
            assert len(selected) == r.events and selected.permco.nunique() == r.companies
            assert r.limited_support == (len(selected) < 200 or selected.permco.nunique() < 50)
            expected = {'stock': selected.stock_return.mean(), 'spy': selected.spy_return.mean(),
                'excess': selected.excess_spy.mean(), 'improvement': selected.excess_spy.mean()-f.excess_spy.mean(),
                'median_stock': selected.stock_return.median(), 'median': selected.excess_spy.median(),
                'loss': selected.stock_return.lt(0).mean(), 'sample_skew': selected.stock_return.skew(),
                'equal_company': selected.groupby('permco').excess_spy.mean().mean(),
                'equal_date': selected.groupby('date').excess_spy.mean().mean()}
            for field, value in expected.items():
                close(getattr(r, field), value)
                checks += 1
            for level in [1, 2, 3]:
                win = selected.stock_return.ge(level-1e-12)
                count = win.sum()
                total = f.stock_return.ge(level-1e-12).sum()
                assert count == getattr(r, f'winners_{level*100}')
                close(getattr(r, f'fraction_{level*100}'), win.mean())
                close(getattr(r, f'retention_{level*100}'), count/total if total else np.nan)
                close(getattr(r, f'tail_contribution_{level*100}'), selected.loc[win, 'stock_return'].sum()/len(selected) if len(selected) else np.nan)
                checks += 4
    options = flags(base)
    for r in pd.read_csv(out/'overlap.csv').itertuples():
        a, b = options[r.first], options[r.second]
        assert int((a & b).sum()) == r.intersection and int((a | b).sum()) == r.union
        close(r.jaccard, (a & b).sum()/(a | b).sum())
        close(r.second_given_first, (a & b).sum()/a.sum())
        close(r.phi, np.corrcoef(a, b)[0, 1])
    bits = np.column_stack([options[f'{c}2'] for c in 'CVAB'])
    signatures = sum(bits[:, j].astype(int)*(2**j) for j in range(4))
    for r in pd.read_csv(out/'exclusive_signatures.csv').itertuples():
        f = base.loc[signatures == r.signature]
        assert len(f) == r.events
        close(f.excess_spy.mean(), r.excess)
    assert pd.read_csv(out/'exclusive_signatures.csv').events.sum() == len(base)
    for r in pd.read_csv(out/'pass_counts.csv').itertuples():
        f = base.loc[bits.sum(axis=1) == r.main_passes]
        assert len(f) == r.events
        close(f.excess_spy.mean(), r.excess)
    concentration_checks = 0
    for weighting, rows in pd.read_csv(out/'concentration.csv').groupby('weighting'):
        f = base if weighting == 'all' else base.loc[base.nonoverlap]
        group = masks(f)
        for r in rows.itertuples():
            selected = f.loc[group[r.config]]
            n, total = len(selected), selected.excess_spy.sum()
            companies = selected.groupby('permco').excess_spy.agg(['sum', 'size'])
            years = selected.groupby(selected.date.dt.year).excess_spy.agg(['sum', 'size'])
            pos = companies.loc[companies['sum'].gt(0)].sort_values('sum', ascending=False)
            for count, field in [(1, 'top1_excess_share'), (5, 'top5_excess_share')]:
                close(getattr(r, field), pos['sum'].head(count).sum()/total if total > 0 else np.nan)
            close(r.effective_companies, n*n/(companies['size']**2).sum() if n else np.nan)
            for groups, prefix in [(companies, 'company'), (years, 'year')]:
                leave = [(total-a.sum)/(n-a.size) for a in groups.itertuples() if n > a.size]
                close(getattr(r, f'leave_{prefix}_min'), min(leave) if leave else np.nan)
                close(getattr(r, f'leave_{prefix}_max'), max(leave) if leave else np.nan)
            removed = pos.head(5)
            close(r.remove_top5_excess, (total-removed['sum'].sum())/(n-removed['size'].sum()) if n > removed['size'].sum() else np.nan)
            concentration_checks += 8
    edges = pd.read_csv(out/'contrast_definitions.csv')
    assert edges.kind.value_counts().to_dict() == {'addition': 216, 'neighbor': 108, 'baseline': 80}
    for r in edges.itertuples():
        parent, child = states[r.parent], states[r.child]
        changed = [j for j in range(4) if parent[j] != child[j]]
        if r.kind == 'baseline':
            assert r.parent == 0 and r.child > 0
        else:
            assert len(changed) == 1
            j = changed[0]
            assert r.feature == 'CVAB'[j]
            assert (parent[j] == 0 and child[j] in [1, 2]) if r.kind == 'addition' else (parent[j] == 1 and child[j] == 2)
    interval_checks, bootstrap_checks = 0, 0
    intervals = pd.read_csv(out/'uncertainty.csv')
    for (weighting, block), rows in intervals.groupby(['weighting', 'block'], sort=False):
        f = base if weighting == 'all' else base.loc[base.nonoverlap]
        group = masks(f)
        draw = np.load(out/f'draws_{weighting}_{block}.npz')
        points, samples = draw['points'], draw['samples']
        for i, name in enumerate(names):
            close(points[i], f.loc[group[name], 'excess_spy'].mean())
        # Independently generate direct event weights for the first three draws.
        cal = valid_nyse_sessions(f.date.min(), f.date.max())
        rng = np.random.default_rng(20261017)
        lengths = np.minimum(block, len(cal)-np.arange(0, len(cal), block))
        codes, companies = pd.factorize(f.permco, sort=True)
        dates = cal.get_indexer(f.date)
        for draw_index in range(3):
            starts = rng.integers(0, len(cal), len(lengths))
            selected_dates = np.concatenate([(start+np.arange(length)) % len(cal) for start, length in zip(starts, lengths)])
            time_weights = np.bincount(selected_dates, minlength=len(cal))
            company_weights = rng.multinomial(len(companies), np.full(len(companies), 1/len(companies)))
            weights = time_weights[dates]*company_weights[codes]
            for i, name in enumerate(names):
                w = weights[group[name]]
                x = f.loc[group[name], 'excess_spy'].to_numpy()
                close(samples[draw_index, i], (w@x)/w.sum() if w.sum() else np.nan)
                bootstrap_checks += 1
        differences = samples[:, edges.child]-samples[:, edges.parent]
        estimates = points[edges.child]-points[edges.parent]
        families = {'main15': edges.kind.eq('baseline') & edges.main, 'grid80': edges.kind.eq('baseline'),
            'main_add32': edges.kind.eq('addition') & edges.main, 'all404': np.ones(len(edges), bool)}
        for i, r in enumerate(rows.itertuples()):
            assert r.child == edges.child.iloc[i] and r.parent == edges.parent.iloc[i]
            finite = differences[:, i][np.isfinite(differences[:, i])]
            bounds = np.percentile(finite, [2.5, 97.5]) if len(finite) >= .95*len(samples) else [np.nan]*2
            close(r.estimate, estimates[i])
            close(r.lower95, bounds[0])
            close(r.upper95, bounds[1])
            assert len(finite) == r.valid_draws
            interval_checks += 4
        for name, keep in families.items():
            good = np.isfinite(differences[:, keep]).all(axis=1)
            radius = np.percentile(np.max(np.abs(differences[good][:, keep]-estimates[keep]), axis=1), 95) if good.mean() >= .95 else np.nan
            for i, r in enumerate(rows.itertuples()):
                close(getattr(r, f'{name}_lower'), estimates[i]-radius if keep[i] else np.nan)
                close(getattr(r, f'{name}_upper'), estimates[i]+radius if keep[i] else np.nan)
                assert getattr(r, f'{name}_complete_draws') == good.sum()
                interval_checks += 3
    result = dict(status='passed', configurations=81, source_events=len(z), common_annual_events=len(base),
        summary_tail_checks=checks, concentration_checks=concentration_checks, interval_checks=interval_checks,
        direct_bootstrap_checks=bootstrap_checks, manifest_sha256=sha256(out/'manifest.json'),
        verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
