"""Same-date non-ATH controls matched on frozen 6-1 momentum, size and volatility."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.momentum_controls import match_momentum_controls  # noqa: E402
from ath_breakout.research.signal_study import forward_arrays  # noqa: E402
from ath_breakout.research.high_breakout import holding_return  # noqa: E402
from ath_breakout.research.baseline_robustness import crossed_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT / 'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_14_incremental_6_1_v001'


def main():
    out = ROOT / f'outputs/research/ath/{STUDY}/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    (out / 'by_year').mkdir(parents=True)
    print(out, flush=True)
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    inputs = {}

    def read(path, digest, columns=None):
        assert sha256(path) == digest, path
        inputs[str(path.relative_to(ROOT))] = digest
        return pd.read_parquet(path, columns=columns)

    events = read(SOURCE / 'events.parquet', manifest['artifacts']['events.parquet'])
    assert len(events) == 75884 and events.event_id.is_unique
    raw_cache = {}

    def raw(year):
        if year not in raw_cache:
            path = ROOT / f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
            raw_cache[year] = read(path, manifest['inputs'][str(path.relative_to(ROOT))],
                ['permno', 'date', 'market_cap', 'total_return', 'open', 'close', 'delisting_flag'])
        return raw_cache[year]

    all_events, coverage, balance, scalar_checks = [], [], [], 0
    for year in range(1994, 2027):
        ep = events.loc[events.date.dt.year.eq(year) & events.common_momentum].copy()
        pool_path = SOURCE / f'by_year/ranking_pool_6_1_{year}.parquet'
        pool = read(pool_path, manifest['artifacts'][str(pool_path.relative_to(SOURCE))])
        hist = pd.concat([raw(year-1), raw(year)], ignore_index=True)
        cal = valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31')
        rr = hist.total_return.where(np.isfinite(hist.total_return) & hist.total_return.ge(-1))
        vol = hist.assign(rr=rr).pivot(index='date', columns='permno', values='rr').reindex(cal).rolling(63, min_periods=63).std()*np.sqrt(252)
        ix = pd.MultiIndex.from_frame(pool[['date', 'permno']])
        pool['vol63'] = vol.stack().reindex(ix).to_numpy()
        pool = pool.merge(raw(year)[['date', 'permno', 'market_cap']], on=['date', 'permno'], validate='one_to_one')
        sig = events.loc[events.date.dt.year.eq(year), ['date', 'permno']]
        pool = pool.merge(sig.assign(is_ath=True), on=['date', 'permno'], how='left', validate='one_to_one')
        # Signal classification uses every certified ATH, including those outside common momentum.
        pool = pool.loc[~pool.is_ath.eq(True) & np.isfinite(pool.market_cap) & pool.market_cap.gt(0)
                        & np.isfinite(pool.vol63) & pool.vol63.gt(0)].copy()
        controls_by_date = dict(tuple(pool.groupby('date')))
        rows = []
        for date, group in ep.groupby('date'):
            group = group.loc[np.isfinite(group.market_cap) & group.market_cap.gt(0)
                              & np.isfinite(group.vol63) & group.vol63.gt(0)].copy()
            group['momentum'] = group.momentum_6_1
            candidates = controls_by_date.get(date, pool.iloc[:0])
            selected = match_momentum_controls(group, candidates)
            lookup = candidates.set_index('permno')
            for e in group.itertuples():
                for rank, p in enumerate(selected.get(e.permno, []), 1):
                    c = lookup.loc[p]
                    rows.append(dict(event_id=e.event_id, date=date, permno=p, rank=rank,
                        event_permco=e.permco, control_permco=c.permco,
                        event_momentum=e.momentum, control_momentum=c.momentum,
                        momentum_gap=c.momentum-e.momentum, size_ratio=c.market_cap/e.market_cap,
                        vol_ratio=c.vol63/e.vol63, control_percentile=c.momentum_percentile))
        cols = ['event_id', 'date', 'permno', 'rank', 'event_permco', 'control_permco',
                'event_momentum', 'control_momentum', 'momentum_gap', 'size_ratio', 'vol_ratio', 'control_percentile']
        q = pd.DataFrame(rows, columns=cols)
        ep['matched_at_signal'] = ep.event_id.isin(q.event_id)
        ep['valid_controls_6_1'] = 0
        ep['control_return_6_1'] = np.nan
        if len(q):
            selected = pd.Index(sorted(q.permno.unique()))
            calendar = valid_nyse_sessions(f'{year}-01-01', f'{year+2}-01-31')
            history = pd.concat([raw(y) for y in range(year, min(year+2, 2026)+1)], ignore_index=True)
            history = history.loc[history.permno.isin(selected) & history.date.le(calendar[-1])]
            arrays = {c: history.pivot(index='date', columns='permno', values=c).reindex(index=calendar, columns=selected).to_numpy(float)
                      for c in ['open', 'close', 'total_return']}
            terminal = history.assign(t=history.delisting_flag.eq('Y')).pivot(index='date', columns='permno', values='t').reindex(index=calendar, columns=selected).eq(True).to_numpy(bool)
            entries = calendar.get_indexer(q.date)+1
            indices = selected.get_indexer(q.permno)
            values, status, cash = forward_arrays(arrays['open'], arrays['close'], arrays['total_return'], terminal,
                entries, indices, 252, calendar.searchsorted(pd.Timestamp('2026-06-30'), side='right')-1)
            q = q.assign(value=values, status=status, terminal_cash=cash)
            means = q.groupby('event_id').value.agg(['count', 'mean'])
            ep['valid_controls_6_1'] = ep.event_id.map(means['count']).fillna(0).astype(int)
            ep['control_return_6_1'] = ep.event_id.map(means['mean']).where(ep.valid_controls_6_1.eq(5))
            for i in np.linspace(0, len(q)-1, min(10, len(q)), dtype=int):
                h = pd.DataFrame({c: a[:, indices[i]] for c, a in arrays.items()})
                h['delisting_flag'] = np.where(terminal[:, indices[i]], 'Y', 'N')
                v, state, _ = holding_return(h, entries[i], 252)
                assert np.isclose(v, values[i], equal_nan=True, atol=1e-10), state
                scalar_checks += 1
        ep['incremental_ath'] = ep.stock_return-ep.control_return_6_1
        q.to_parquet(out / f'by_year/controls_{year}.parquet', index=False)
        all_events.append(ep)
        balance.append(q)
        coverage.append(dict(year=year, events=len(ep), matched=int(ep.matched_at_signal.sum()),
                             complete=int((ep.incremental_ath.notna() & ep.excess_spy.notna()).sum())))
        print(coverage[-1], flush=True)
        raw_cache = {k: v for k, v in raw_cache.items() if k >= year}
    z = pd.concat(all_events, ignore_index=True)
    z['period'] = period_labels(z.date)
    z.to_parquet(out / 'events.parquet', index=False)
    q = pd.concat(balance, ignore_index=True)
    q.to_parquet(out / 'controls.parquet', index=False)
    pd.DataFrame(coverage).to_csv(out / 'coverage.csv', index=False)
    summaries, intervals, balances, availability = [], [], [], []
    for sample, mask in [('all_common', pd.Series(True, index=z.index)), ('top20', z.quintile_6_1.eq(5))]:
        natural = z.loc[mask]
        valid = natural.loc[natural.incremental_ath.notna() & natural.excess_spy.notna()]
        availability.append(dict(sample=sample, source_events=len(natural), annual_events=int(natural.excess_spy.notna().sum()),
            matched_at_signal=int(natural.matched_at_signal.sum()), complete_events=len(valid),
            unmatched_annual_excess=natural.loc[natural.excess_spy.notna() & ~natural.event_id.isin(valid.event_id), 'excess_spy'].mean()))
        b = q.loc[q.event_id.isin(valid.event_id)].copy()
        b['abs_momentum_gap'] = b.momentum_gap.abs()
        for c in ['momentum_gap', 'abs_momentum_gap', 'size_ratio', 'vol_ratio', 'control_percentile']:
            balances.append(dict(sample=sample, metric=c, mean=b[c].mean(), median=b[c].median(),
                                 q05=b[c].quantile(.05), q95=b[c].quantile(.95)))
        for weighting, f in [('all', valid), ('nonoverlap', valid.loc[valid.nonoverlap])]:
            for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                              *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
                summaries.append(dict(sample=sample, weighting=weighting, period=period, events=len(g),
                    stock=g.stock_return.mean(), controls=g.control_return_6_1.mean(), spy=g.spy_return.mean(),
                    excess_spy=g.excess_spy.mean(), incremental=g.incremental_ath.mean(), median=g.incremental_ath.median(),
                    positive=g.incremental_ath.gt(0).mean(), companies=g.permco.nunique(),
                    equal_company=g.groupby('permco').incremental_ath.mean().mean(),
                    equal_date=g.groupby('date').incremental_ath.mean().mean()))
        for period, f in [('all', valid), *[(p, valid.loc[valid.period.eq(p)]) for p in ['early', 'middle', 'recent']]]:
            print(f'Bootstrap {sample} {period} N={len(f)}', flush=True)
            cal = valid_nyse_sessions(f.date.min(), f.date.max())
            for block in [252, 504]:
                intervals.extend(dict(sample=sample, period=period, **r) for r in
                    crossed_intervals(f, 'incremental_ath', cal, block=block))
    pd.DataFrame(summaries).to_csv(out / 'summary.csv', index=False)
    pd.DataFrame(intervals).to_csv(out / 'uncertainty.csv', index=False)
    pd.DataFrame(balances).to_csv(out / 'balance.csv', index=False)
    pd.DataFrame(availability).to_csv(out / 'availability.csv', index=False)
    q.groupby(['date', 'control_permco']).size().rename('uses').to_csv(out / 'control_reuse.csv')
    config = dict(study_id=STUDY, horizon=252, momentum='6-1', controls=5, draws=2000, seed=20261016,
                  blocks=[252, 504], scalar_checks=scalar_checks, exploratory=True,
                  limitations=['No untouched holdout', 'Shared controls not independently clustered',
                               'Conditional certified-history population', 'Residual confounding; no causal alpha claim'])
    result = dict(config=config, inputs=inputs, source_manifest_sha256=sha256(SOURCE/'manifest.json'),
        code_sha256=sha256(Path(__file__)), matcher_sha256=sha256(ROOT/'src/ath_breakout/research/momentum_controls.py'),
        protocol_sha256=sha256(ROOT/'research/ath/ATH_INCREMENTAL_6_1_PLAN.md'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.rglob('*') if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(pd.DataFrame(summaries).query("period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
