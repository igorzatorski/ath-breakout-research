"""Five frozen ATR-normalized ATH breakout magnitude cutoffs."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.breakout_strength import THRESHOLDS, prior_atr, mask, band_codes  # noqa: E402
from ath_breakout.research.filter_grid import joint_grid_intervals  # noqa: E402
from ath_breakout.research.period_diagnostic import period_labels  # noqa: E402
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_12_momentum_lookbacks_v001/20261016T203150435062Z'
STUDY = 'ath_24_breakout_strength_v001'


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
            ['permno', 'date', 'high', 'low', 'close', 'price_adjustment_factor'])
        factor = raw.price_adjustment_factor.where(np.isfinite(raw.price_adjustment_factor) & raw.price_adjustment_factor.gt(0))
        for col in ['high', 'low', 'close']:
            raw[col] = (raw[col]/factor).where(np.isfinite(raw[col]) & raw[col].gt(0))
        current = raw[['permno', 'date', 'high', 'low', 'close']]
        if year >= 1994:
            e = events.loc[events.date.dt.year.eq(year), ['event_id', 'permno', 'date', 'prior_ath']].copy()
            ids = e.permno.unique()
            lb = pd.concat([tail.loc[tail.permno.isin(ids)], current.loc[current.permno.isin(ids)]], ignore_index=True)
            cal = valid_nyse_sessions(f'{year-1}-01-01', f'{year}-12-31')
            arrays = {col: lb.pivot(index='date', columns='permno', values=col).reindex(cal) for col in ['high', 'low', 'close']}
            ix = pd.MultiIndex.from_frame(e[['date', 'permno']])
            atr = prior_atr(arrays['high'], arrays['low'], arrays['close'])
            e['signal_close'] = arrays['close'].stack().reindex(ix).to_numpy()
            e['atr20_prior'] = atr.stack().reindex(ix).to_numpy()
            e['overshoot'] = e.signal_close-e.prior_ath
            e['breakout_strength'] = (e.overshoot/e.atr20_prior).where(e.atr20_prior.gt(0) & np.isfinite(e.atr20_prior) & e.overshoot.gt(0))
            features.append(e.drop(columns=['date', 'permno', 'prior_ath']))
            print(f'Breakout magnitude {year}: {len(e)} signals', flush=True)
        tail = current
    z = events.merge(pd.concat(features, ignore_index=True), on='event_id', validate='one_to_one')
    z['feature_complete'] = z.breakout_strength.notna() & np.isfinite(z.breakout_strength)
    z['period'] = period_labels(z.date)
    z.to_parquet(out/'events.parquet', index=False)
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    base = annual.loc[annual.feature_complete]
    pd.DataFrame([dict(sample=name, **describe(f)) for name, f in [('original', annual),
        ('common_features', base), ('missing_features', annual.loc[~annual.feature_complete])]]).to_csv(out/'coverage.csv', index=False)
    pd.DataFrame([dict(status=name, events=int(keep.sum())) for name, keep in [
        ('available', annual.feature_complete), ('missing_atr', annual.atr20_prior.isna()),
        ('nonpositive_atr', annual.atr20_prior.le(0)), ('missing_close', annual.signal_close.isna()),
        ('nonpositive_overshoot', annual.overshoot.le(0))]]).to_csv(out/'feature_audit.csv', index=False)
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
    codes = band_codes(base)
    pd.DataFrame([dict(band=label, **describe(base.loc[codes == i])) for i, label in enumerate(
        ['lt0.10', '0.10_to0.25', '0.25_to0.50', '0.50_to1.00', '1.00_to2.00', 'ge2.00'])]).to_csv(out/'strength_bands.csv', index=False)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/breakout_strength.py', ROOT/'src/ath_breakout/research/filter_grid.py',
            ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id=STUDY, thresholds=THRESHOLDS, atr_window=20, baseline_events=len(base), original_annual_events=len(annual),
        inputs=inputs, seed=20261016, draws=2000, blocks=[252, 504],
        code={str(p.relative_to(ROOT)): sha256(p) for p in code},
        source_manifest_sha256=sha256(SOURCE/'manifest.json'),
        protocol_sha256=sha256(ROOT/'research/ath/ATH_BREAKOUT_STRENGTH_PLAN.md'))
    result['artifacts'] = {str(p.relative_to(out)): sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(s.query("weighting=='all' and period=='all'").to_string(index=False), flush=True)
    print(out, flush=True)


if __name__ == '__main__':
    main()
