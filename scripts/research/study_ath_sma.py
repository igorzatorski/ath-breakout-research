"""Six frozen stock SMA position and alignment filters on annual ATH outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.sma_trend import WINDOWS, FILTERS, signal_sma, memberships, mask  # noqa: E402
from ath_breakout.research.filter_grid import joint_grid_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_23_sma_trend_v001'


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
    tail, features = None, []
    for year in range(1993, 2027):
        path = ROOT/f'data/raw/crsp/daily_by_year/daily_{year}.parquet'
        raw = checked(path, manifest['inputs'][str(path.relative_to(ROOT))],
            ['permno', 'date', 'close', 'price_adjustment_factor'])
        factor = raw.price_adjustment_factor
        raw['p'] = (raw.close/factor).where(np.isfinite(factor) & factor.gt(0) & np.isfinite(raw.close) & raw.close.gt(0))
        current = raw[['permno', 'date', 'p']]
        if year >= 1994:
            e = events.loc[events.date.dt.year.eq(year), ['event_id', 'permno', 'date']].copy()
            ids = e.permno.unique()
            lb = pd.concat([tail.loc[tail.permno.isin(ids)], current.loc[current.permno.isin(ids)]], ignore_index=True)
            prices = lb.pivot(index='date', columns='permno', values='p').reindex(
                valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31'))
            ix = pd.MultiIndex.from_frame(e[['date', 'permno']])
            e['signal_close'] = prices.stack().reindex(ix).to_numpy()
            for n in WINDOWS:
                e[f'sma_{n}'] = signal_sma(prices, n).stack().reindex(ix).to_numpy()
            features.append(e.drop(columns=['date', 'permno']))
            print(f'Stock SMA {year}: {len(e)} signals', flush=True)
        tail = current
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    for name, values in memberships(z).items():
        z[name] = values
    z['feature_complete'] = z[['signal_close']+[f'sma_{n}' for n in WINDOWS]].notna().all(axis=1)
    z['period'] = period_labels(z.date)
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.feature_complete]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in [('original', annual),
        ('common_features', base), ('missing_features', annual.loc[~annual.feature_complete])]]).to_csv(out/'coverage.csv', index=False)
    audit = []
    for name in FILTERS:
        required = ['signal_close', f'sma_{name.removeprefix("price_gt")}'] if name.startswith('price_gt') else (
            ['sma_100', 'sma_200'] if name == 'sma100_gt200' else ['sma_50', 'sma_100', 'sma_200'])
        observed = annual[required].notna().all(axis=1)
        audit.append(dict(filter=name, annual_events=len(annual), naturally_observed=int(observed.sum()),
            naturally_pass=int((observed & annual[name]).sum()), naturally_fail=int((observed & ~annual[name]).sum()),
            missing=int((~observed).sum()), common_pass=int(base[name].sum()), common_fail=int((~base[name]).sum())))
    pd.DataFrame(audit).to_csv(out/'feature_audit.csv', index=False)
    summaries, intervals, complements = [], [], []
    labels = ['reference']+FILTERS
    for weighting, f in [('all', base), ('nonoverlap', base.loc[base.nonoverlap])]:
        for period, g in [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
                          *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]:
            for name in labels:
                membership = mask(g, name)
                keep = g.loc[membership]
                row = dict(weighting=weighting, period=period, filter=name,
                    improvement=keep.excess_spy.mean()-g.excess_spy.mean(), median_stock=keep.stock_return.median(),
                    sample_skew=keep.stock_return.skew(), **describe(keep))
                for level in [1, 2, 3]:
                    count = keep.stock_return.ge(level-1e-12).sum()
                    available = g.stock_return.ge(level-1e-12).sum()
                    row[f'winners_{level*100}'] = int(count)
                    row[f'fraction_{level*100}'] = count/len(keep) if len(keep) else np.nan
                    row[f'retention_{level*100}'] = count/available if available else np.nan
                summaries.append(row)
                if name != 'reference':
                    complements.append(dict(weighting=weighting, period=period, filter=name, **describe(g.loc[~membership])))
        groups = np.column_stack([mask(f, name) for name in labels])
        for block in [252, 504]:
            print(f'Joint bootstrap {weighting} block={block}', flush=True)
            intervals.extend(dict(weighting=weighting, **r) for r in joint_grid_intervals(f, groups,
                [dict(filter=name) for name in labels], valid_nyse_sessions(f.date.min(), f.date.max()), block=block))
    s = pd.DataFrame(summaries)
    s.to_csv(out/'summary.csv', index=False)
    pd.DataFrame(intervals).to_csv(out/'uncertainty.csv', index=False)
    pd.DataFrame(complements).to_csv(out/'complement_summary.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/sma_trend.py', ROOT/'src/ath_breakout/research/filter_grid.py',
            ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id=STUDY, filters=FILTERS, windows=WINDOWS, baseline_events=len(base), original_annual_events=len(annual),
        inputs=inputs, seed=20261016, draws=2000, blocks=[252, 504],
        code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        source_manifest_sha256=sha256(SOURCE/'manifest.json'),
        protocol_sha256=sha256(ROOT/'research/ath/ATH_SMA_PLAN.md'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
