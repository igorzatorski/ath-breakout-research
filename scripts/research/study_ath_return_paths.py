"""Annual distributions, right-tail influence and closing-wealth paths."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.long_paths import closing_wealth_paths  # noqa: E402
from ath_breakout.research.return_paths import path_metrics, distribution, PROFIT_LEVELS, LOSS_LEVELS  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_17_return_paths_v001'


def main():
    out = ROOT/f'outputs/research/ath/{STUDY}/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    (out/'by_year').mkdir(parents=True)
    print(out, flush=True)
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    inputs, cache = {}, {}

    def checked(path, digest, columns=None):
        assert sha256(path) == digest, path
        inputs[str(path.relative_to(ROOT))] = digest
        return pd.read_parquet(path, columns=columns)

    original = checked(SOURCE/'events.parquet', manifest['artifacts']['events.parquet'])
    source_coverage = pd.DataFrame([dict(sample='all_ath', signals=len(original), annual_pairs=int(original.excess_spy.notna().sum())),
        dict(sample='momentum_top20', signals=int((original.common_momentum & original.quintile_6_1.eq(5)).sum()),
             annual_pairs=int((original.common_momentum & original.quintile_6_1.eq(5) & original.excess_spy.notna()).sum()))])
    source_coverage.to_csv(out/'source_coverage.csv', index=False)
    events = original.loc[original.excess_spy.notna()].copy()
    assert len(events) == 71961 and events.event_id.is_unique

    def raw(year):
        if year not in cache:
            path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
            cache[year] = checked(path, manifest['inputs'][str(path.relative_to(ROOT))],
                ['permno', 'date', 'open', 'close', 'total_return', 'delisting_flag'])
        return cache[year]

    results, path_rows = [], []
    for year, e in events.groupby(events.date.dt.year):
        ids = pd.Index(sorted(e.permno.unique()))
        cal = valid_nyse_sessions(f'{year}-01-01', f'{year+2}-01-31')
        d = pd.concat([raw(y) for y in range(year, min(year+2, 2026)+1)], ignore_index=True)
        d = d.loc[d.permno.isin(ids) & d.date.le(cal[-1])]
        arrays = {c: d.pivot(index='date', columns='permno', values=c).reindex(index=cal, columns=ids).to_numpy(float)
                  for c in ['open', 'close', 'total_return']}
        terminal = d.assign(t=d.delisting_flag.eq('Y')).pivot(index='date', columns='permno', values='t').reindex(index=cal, columns=ids).eq(True).to_numpy(bool)
        entry = cal.get_indexer(e.date)+1
        cols = ids.get_indexer(e.permno)
        w = closing_wealth_paths(arrays['open'], arrays['close'], arrays['total_return'], terminal, entry, cols, 252)
        assert np.isfinite(w).all() and np.allclose(w[:, -1]-1, e.stock_return, atol=1e-10, rtol=1e-10)
        metrics = path_metrics(w)
        metrics.insert(0, 'event_id', e.event_id.to_numpy())
        results.append(metrics)
        # Save exact complete paths so all aggregate charts and path diagnostics can be rerun.
        np.savez_compressed(out/f'by_year/paths_{year}.npz', event_id=e.event_id.to_numpy(), wealth=w)
        print(f'Paths {year}: {len(e)} reconciled endpoints', flush=True)
        cache = {k: v for k, v in cache.items() if k >= year+1}
    z = events.merge(pd.concat(results, ignore_index=True), on='event_id', validate='one_to_one')
    z['period'] = period_labels(z.date)
    z.to_parquet(out/'events.parquet', index=False)
    summaries, bins, quantiles, tails, pre_losses, influence = [], [], [], [], [], []
    for sample, f0 in [('all_ath', z), ('momentum_top20', z.loc[z.common_momentum & z.quintile_6_1.eq(5)])]:
        for weighting, f1 in [('all', f0), ('nonoverlap', f0.loc[f0.nonoverlap])]:
            for period, f in [('all', f1), *[(p, f1.loc[f1.period.eq(p)]) for p in ['early', 'middle', 'recent']]]:
                meta = dict(sample=sample, weighting=weighting, period=period)
                x = f.stock_return
                summaries.append(dict(**meta, events=len(f), companies=f.permco.nunique(), stock=x.mean(), spy=f.spy_return.mean(),
                    excess=f.excess_spy.mean(), median=x.median(), loss=x.lt(0).mean(), mean_loss=x.loc[x.lt(0)].mean(),
                    mean_gain=x.loc[x.ge(0)].mean(), median_mae=f.mae.median(), median_mfe=f.mfe.median(),
                    median_drawdown=f.max_drawdown.median(), equal_company=f.groupby('permco').stock_return.mean().mean()))
                for col in ['stock_return', 'spy_return', 'mae', 'mfe', 'max_drawdown']:
                    for q in [.01, .05, .10, .25, .50, .75, .90, .95, .99]:
                        quantiles.append(dict(**meta, metric=col, quantile=q, value=f[col].quantile(q)))
                for col in ['stock_return', 'spy_return']:
                    bins.extend(dict(**meta, metric=col, **r) for r in distribution(f, col))
                for level in PROFIT_LEVELS:
                    key = str(int(level*100))
                    finished = x.ge(level-1e-12)
                    reached = f[f'ever_{key}']
                    contribution = x.loc[finished].sum()/len(f)
                    tails.append(dict(**meta, level=level, final_events=int(finished.sum()), final_fraction=finished.mean(),
                        ever_events=int(reached.sum()), ever_fraction=reached.mean(), contribution=contribution,
                        remaining_mean=x.loc[~finished].mean(), mean_final_winners=x.loc[finished].mean(),
                        median_first_session=f.loc[reached, f'first_{key}'].median()))
                    if level >= 1:
                        winners = f.loc[finished]
                        for loss in LOSS_LEVELS:
                            hit = winners[f'mae_before_{key}'].le(-loss+1e-12)
                            pre_losses.append(dict(**meta, level=level, loss=loss, winners=len(winners),
                                crossed_events=int(hit.sum()), crossed_fraction=hit.mean()))
                ordered = f.sort_values(['stock_return', 'event_id'], ascending=[False, True])
                for top in [.01, .05]:
                    n = int(np.ceil(top*len(f)))
                    best = ordered.iloc[:n]
                    influence.append(dict(**meta, top_fraction=top, removed_events=n,
                        contribution=best.stock_return.sum()/len(f), remaining_mean=ordered.iloc[n:].stock_return.mean()))
        # Full-population cross-sectional path summaries, not conditional winner trajectories.
        rows = []
        for path in sorted((out/'by_year').glob('paths_*.npz')):
            data = np.load(path)
            keep = np.isin(data['event_id'], f0.event_id)
            rows.append(data['wealth'][keep])
        wealth = np.concatenate(rows)
        for session in range(252):
            values = wealth[:, session]-1
            path_rows.append(dict(sample=sample, session=session+1, events=len(values), mean=values.mean(),
                q10=np.quantile(values, .1), q25=np.quantile(values, .25), median=np.quantile(values, .5),
                q75=np.quantile(values, .75), q90=np.quantile(values, .9)))
    for name, rows in [('summary', summaries), ('distribution', bins), ('quantiles', quantiles), ('tails', tails),
                       ('winner_prior_losses', pre_losses), ('top_tail_influence', influence), ('path_quantiles', path_rows)]:
        pd.DataFrame(rows).to_csv(out/f'{name}.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/return_paths.py', ROOT/'src/ath_breakout/research/long_paths.py']
    result = dict(study_id=STUDY, annual_events=len(z), endpoints_reconciled=len(z), inputs=inputs,
        source_manifest_sha256=sha256(SOURCE/'manifest.json'),
        protocol_sha256=sha256(ROOT/'research/ath/ATH_RETURN_PATHS_PLAN.md'),
        code={str(p.relative_to(ROOT)): sha256(p) for p in code})
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.rglob('*') if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(pd.DataFrame(summaries).query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
