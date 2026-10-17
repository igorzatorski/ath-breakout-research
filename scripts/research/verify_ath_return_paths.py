"""Independent matrix statistics and sampled raw scalar wealth reconstructions."""
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
        assert sha256(out/name) == digest, name
    z = pd.read_parquet(out/'events.parquet').set_index('event_id')
    source = pd.read_parquet(ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z/events.parquet')
    expected = source.loc[source.excess_spy.notna()].set_index('event_id')
    assert set(z.index) == set(expected.index) and z.index.is_unique
    for c in ['stock_return', 'spy_return', 'nonoverlap', 'momentum_6_1']:
        assert np.allclose(z[c], expected[c].reindex(z.index), equal_nan=True)
    cache = {}

    def raw(year):
        if year not in cache:
            path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
            assert sha256(path) == manifest['inputs'][str(path.relative_to(ROOT))]
            cache[year] = pd.read_parquet(path, columns=['permno', 'date', 'open', 'close', 'total_return', 'delisting_flag'])
        return cache[year]

    checks, raw_paths, path_ids = 0, 0, []
    for path in sorted((out/'by_year').glob('paths_*.npz')):
        year = int(path.stem.split('_')[-1])
        data = np.load(path)
        ids, w = data['event_id'], data['wealth']
        path_ids.extend(ids.tolist())
        f = z.reindex(ids)
        assert w.shape == (len(ids), 252) and np.isfinite(w).all() and (w >= 0).all()
        assert np.allclose(w[:, -1]-1, f.stock_return, atol=1e-10)
        full = np.column_stack([np.ones(len(w)), w])
        peaks = np.maximum.accumulate(full, axis=1)
        metrics = dict(mae=full.min(axis=1)-1, mfe=full.max(axis=1)-1,
                       max_drawdown=(full/peaks-1).min(axis=1))
        for col, values in metrics.items():
            assert np.allclose(f[col], values, atol=1e-12)
            checks += len(w)
        chosen = list(np.linspace(0, len(w)-1, min(8, len(w)), dtype=int))
        terminal = np.flatnonzero(f.terminal_cash)
        if len(terminal):
            chosen.extend(terminal[:2].tolist())
        history = pd.concat([raw(y) for y in range(year, min(year+2, 2026)+1)], ignore_index=True).set_index(['date', 'permno'])
        for i in sorted(set(chosen)):
            e = f.iloc[i]
            calendar = valid_nyse_sessions(e.entry_date, e.exit_date)
            h = history.reindex(pd.MultiIndex.from_product([calendar, [e.permno]]))
            assert len(h) == 252
            wealth, dead, values = 1., False, []
            for j, r in enumerate(h.itertuples()):
                if j == 0:
                    wealth = r.close/r.open
                elif not dead:
                    wealth *= 1+r.total_return
                if r.delisting_flag == 'Y':
                    dead = True
                values.append(wealth)
            assert np.allclose(w[i], values, atol=1e-10, rtol=1e-10)
            raw_paths += 1
        for level in [.5, 1., 2., 3.]:
            key = str(int(level*100))
            ever = (w >= 1+level-1e-12).any(axis=1)
            assert np.array_equal(f[f'ever_{key}'], ever)
            for i in sorted(set(chosen)):
                hit = np.flatnonzero(w[i] >= 1+level-1e-12)
                first = hit[0]+1 if len(hit) else np.nan
                low = min(1., w[i, :hit[0]].min())-1 if len(hit) and hit[0] else (0. if len(hit) else np.nan)
                assert np.isclose(f.iloc[i][f'first_{key}'], first, equal_nan=True)
                assert np.isclose(f.iloc[i][f'mae_before_{key}'], low, equal_nan=True)
                checks += 2
            checks += len(w)
        cache = {k: v for k, v in cache.items() if k >= year+1}
    assert len(path_ids) == len(set(path_ids)) == len(z) and set(path_ids) == set(z.index)
    distributions = pd.read_csv(out/'distribution.csv')
    for _, d in distributions.groupby(['sample', 'weighting', 'period', 'metric']):
        first = d.iloc[0]
        f = z if first['sample'] == 'all_ath' else z.loc[z.common_momentum & z.quintile_6_1.eq(5)]
        if first.weighting == 'nonoverlap':
            f = f.loc[f.nonoverlap]
        if first.period != 'all':
            f = f.loc[f.period.eq(first.period)]
        assert d.events.sum() == len(f)
        assert np.isclose(d.fraction.sum(), 1.)
        assert np.isclose(d.contribution.sum(), f[first.metric].mean())
        checks += 3
    tails = pd.read_csv(out/'tails.csv')
    losses = pd.read_csv(out/'winner_prior_losses.csv')
    for r in tails.itertuples():
        f = z if r.sample == 'all_ath' else z.loc[z.common_momentum & z.quintile_6_1.eq(5)]
        if r.weighting == 'nonoverlap':
            f = f.loc[f.nonoverlap]
        if r.period != 'all':
            f = f.loc[f.period.eq(r.period)]
        winners = f.loc[f.stock_return.ge(r.level-1e-12)]
        assert len(winners) == r.final_events
        assert np.isclose(winners.stock_return.sum()/len(f), r.contribution)
        assert r.final_events <= r.ever_events
        if r.level >= 1:
            subset = losses.loc[losses['sample'].eq(r.sample) & losses.weighting.eq(r.weighting)
                & losses.period.eq(r.period) & losses.level.eq(r.level)]
            for t in subset.itertuples():
                assert t.winners == len(winners)
                count = winners[f'mae_before_{int(r.level*100)}'].le(-t.loss+1e-12).sum()
                assert count == t.crossed_events
                checks += 1
        checks += 3
    result = dict(status='passed', numerical_checks=checks, raw_complete_path_samples=raw_paths,
        all_endpoints_reconciled=len(z), manifest_sha256=sha256(out/'manifest.json'),
        verifier_sha256=sha256(Path(__file__)))
    (out/'independent_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
