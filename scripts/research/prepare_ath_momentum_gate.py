"""Rebuild ATH/two-year highs with and without the mandatory momentum gate."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.momentum_lookbacks import momentum_excluding_recent  # noqa: E402
from ath_breakout.research.momentum_filter import rank_momentum  # noqa: E402
from ath_breakout.research.event_ranking import rank_events  # noqa: E402
from ath_breakout.research.range_contraction import contraction_features  # noqa: E402
from ath_breakout.research.volume_dryup import comparable_volume  # noqa: E402
from study_ath_signal import bounds, COLS  # noqa: E402
from audit_ath_baseline import sha256, BASE  # noqa: E402

RULES = {'ath_top20':None,'ath_all':None,'high2y_top20':504,'high2y_all':504}
OLD = ROOT / 'outputs/backtests/ath_38_rolling_highs_v001/20261017T191148442382Z'


def main():
    out = ROOT / f'outputs/backtests/ath_39_momentum_gate_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    (out / 'signals_by_year').mkdir(parents=True)
    (out / 'pools').mkdir()
    print(out, flush=True)
    (ROOT / 'outputs/backtests/ath_39_latest.txt').write_text(str(out))
    expected = {i['path']: i['sha256'] for i in json.loads((BASE / 'manifest.json').read_text())['inputs']}
    inputs = {}

    def checked(path, columns=None, ids=None):
        key = str(path.relative_to(ROOT))
        digest = sha256(path)
        assert digest == expected[key], key
        inputs[key] = digest
        return pd.read_parquet(path, columns=columns, filters=None if ids is None else [('permno', 'in', ids)])

    membership = checked(ROOT / 'data/processed/crsp/universe_memberships.parquet')
    ids = sorted(membership.loc[membership.effective_date.ge('2007-01-01'), 'permno'].unique())
    formation = membership[['effective_date', 'formation_date']].drop_duplicates().sort_values('effective_date')
    keys = pd.MultiIndex.from_frame(membership[['effective_date', 'permno']])
    seed = checked(ROOT / 'outputs/research/ath/shared_inputs/high_seed_before_1993.parquet')
    bound = np.fmax(seed.prior_comparable_high, seed.prior_comparable_close)
    prior = dict(zip(seed.loc[np.isfinite(bound), 'permno'], bound[np.isfinite(bound)]))
    legacy = set(seed.loc[~np.isfinite(seed.prior_comparable_high) | seed.prior_comparable_high.le(0)
        | seed.missing_high_rows.gt(0) | seed.prior_comparable_high.lt(seed.prior_comparable_close), 'permno'])
    gaps, tail, high_tail, annual, audit = set(), None, None, [], []
    original = pd.read_parquet(OLD / 'signals.parquet')
    original = original.loc[original.definition.isin(['ath','high2y'])]
    for year in range(1993, 2027):
        columns = list(dict.fromkeys(COLS + ['share_adjustment_factor']))
        d = checked(ROOT / f'data/raw/crsp/daily_by_year/daily_{year}.parquet', columns, ids)
        d = d.sort_values(['permno', 'date']).reset_index(drop=True)
        close, high, observed, bad = bounds(d)
        d['adjusted_close'], d['adjusted_high'], d['observed_bound'] = close, high, observed
        cumulative = d.groupby('permno').observed_bound.cummax().groupby(d.permno).ffill()
        d['prior_ath'] = np.fmax(cumulative.groupby(d.permno).shift(), d.permno.map(prior))
        before_bad = bad.groupby(d.permno).cummax().groupby(d.permno).shift(fill_value=False)
        d['history_uncertain'] = d.permno.isin(legacy) | d.permno.isin(gaps) | before_bad
        calendar = valid_nyse_sessions(f'{year}-01-01', min(pd.Timestamp(f'{year}-12-31'), pd.Timestamp('2026-06-30')))
        if year >= 2005:
            highs = d.pivot(index='date', columns='permno', values='adjusted_high').reindex(index=calendar, columns=ids)
            complete_high = highs if high_tail is None else pd.concat([high_tail, highs])
        if year >= 2007:
            lb = pd.concat([tail, d], ignore_index=True)
            cal = valid_nyse_sessions(f'{year-1}-01-01', min(pd.Timestamp(f'{year}-12-31'), pd.Timestamp('2026-06-30')))
            ix = pd.MultiIndex.from_frame(d[['date', 'permno']])

            def pivot(field):
                return lb.pivot(index='date', columns='permno', values=field).reindex(index=cal, columns=ids)

            rets = pivot('total_return')
            for label, window in [('6_1', 126), ('12_1', 252)]:
                f = momentum_excluding_recent(rets, window)
                d[f'momentum_{label}'] = f.stack().reindex(ix).to_numpy()
            lb['dollar_volume'] = (lb.close * lb.volume).where(lb.close.gt(0) & lb.volume.ge(0))
            adv = pivot('dollar_volume').rolling(21, min_periods=21).mean()
            d['adv21'] = adv.stack().reindex(ix).to_numpy()
            lb['adjusted_volume'] = comparable_volume(lb.volume, lb.share_adjustment_factor)
            volumes = pivot('adjusted_volume')
            volume_ratio = volumes / volumes.rolling(63, min_periods=63).mean().shift(1)
            d['volume_ratio_63'] = volume_ratio.stack().reindex(ix).to_numpy()
            _, _, contraction = contraction_features(pivot('adjusted_close'), 42)
            d['contraction_42'] = contraction.stack().reindex(ix).to_numpy()
            dates = pd.merge_asof(pd.DataFrame({'date': sorted(d.date.unique())}), formation,
                left_on='date', right_on='effective_date', direction='backward')
            d = d.merge(dates, on='date', how='left', validate='many_to_one')
            member = pd.MultiIndex.from_frame(d[['effective_date', 'permno']]).isin(keys)
            eligible = member & d.adv21.ge(1e7) & d.adjusted_close.notna() & d.prior_ath.notna()
            eligible &= ~d.history_uncertain & d.adjusted_high.notna()
            pool = rank_momentum(d.loc[eligible, ['date', 'permno', 'permco', 'momentum_6_1']]
                .rename(columns={'momentum_6_1': 'momentum'}))
            d = d.merge(pool[['date', 'permno', 'quintile', 'rank_population']],
                on=['date', 'permno'], how='left', validate='one_to_one')
            # Preserve original complete long-momentum support before candidate selection.
            valid = d.quintile.notna() & np.isfinite(d.momentum_12_1)
            valid &= np.isfinite(d.volume_ratio_63) & np.isfinite(d.contraction_42)
            valid &= d.date.ge('2007-12-31')
            sample = d.loc[valid].copy()
            ix = pd.MultiIndex.from_frame(sample[['date', 'permno']])
            sample['is_ath'] = sample.adjusted_close.gt(sample.prior_ath)
            year_frames = []
            rolling_cache = {}
            for label, window in RULES.items():
                if window is None:
                    maximum = sample.prior_ath.to_numpy()
                else:
                    if window not in rolling_cache:
                        rolling = complete_high.rolling(window, min_periods=window).max().shift(1).reindex(calendar)
                        rolling_cache[window] = rolling.stack().reindex(ix).to_numpy()
                    maximum = rolling_cache[window]
                candidate = sample.loc[sample.adjusted_close.gt(maximum)].copy()
                candidate['prior_high'] = maximum[sample.adjusted_close.gt(maximum)]
                if label.endswith('top20'):
                    candidate = candidate.loc[candidate.quintile.eq(5)].copy()
                candidate['definition'] = label
                candidate = rank_events(candidate)
                candidate['event_id'] = label + ':' + candidate.date.dt.strftime('%Y%m%d') + ':' + candidate.permno.astype(str)
                keep = ['event_id', 'definition', 'date', 'permno', 'permco', 'ticker', 'prior_high',
                    'prior_ath', 'adjusted_close', 'is_ath', 'momentum_6_1', 'volume_ratio_63',
                    'contraction_42', 'rank_population', 'quintile', 'momentum_12_1', 'score_MV']
                candidate = candidate[keep].sort_values(['date', 'score_MV', 'momentum_6_1', 'permno'],
                    ascending=[True, False, False, True])
                assert np.isfinite(candidate.score_MV).all()
                year_frames.append(candidate)
                audit.append(dict(year=year, definition=label, signals=len(candidate),
                    non_ath=int((~candidate.is_ath).sum()), missing_window=int((~np.isfinite(maximum)).sum())))
            result = pd.concat(year_frames, ignore_index=True)
            for current, previous in [('ath_top20','ath'),('high2y_top20','high2y')]:
                control = result.loc[result.definition.eq(current)]
                old = original.loc[original.date.dt.year.eq(year) & original.definition.eq(previous)]
                assert set(zip(control.date,control.permno))==set(zip(old.date,old.permno)),(year,current)
                paired = control.merge(old,on=['date','permno'],suffixes=('','_old'),validate='one_to_one')
                for field in ['momentum_6_1','volume_ratio_63','contraction_42','score_MV']:
                    assert np.allclose(paired[field],paired[field+'_old'],equal_nan=True,atol=1e-10),(year,current,field)
            result.to_parquet(out / f'signals_by_year/{year}.parquet', index=False)
            pool.to_parquet(out / f'pools/{year}.parquet', index=False)
            annual.append(result)
            print(f'Signals {year}: '+', '.join(f'{k}={len(result.loc[result.definition.eq(k)])}' for k in RULES), flush=True)
        if year >= 2005:
            high_tail = complete_high.tail(504)
        for sid, value in d.groupby('permno').observed_bound.max().dropna().items():
            prior[sid] = max(prior.get(sid, value), value)
        gaps.update(d.loc[bad.to_numpy(), 'permno'].unique())
        tail = d[columns + ['adjusted_close']].copy() if year >= 2006 else None
        if year < 2007:
            print(f'History warmup {year}', flush=True)
    signals = pd.concat(annual, ignore_index=True)
    signals.to_parquet(out / 'signals.parquet', index=False)
    np.save(out / 'security_ids.npy', np.array(sorted(signals.permno.unique())))
    pd.DataFrame(audit).to_csv(out / 'signal_coverage.csv', index=False)
    result = dict(study_id='ath_39_momentum_gate_v001', status='signals_prepared', inputs=inputs,
        definitions=RULES, original_ath_signals=len(original),
        code={str(Path(__file__).relative_to(ROOT)): sha256(Path(__file__))},
        protocol_sha256=sha256(ROOT / 'research/ath/ATH_MOMENTUM_GATE_PLAN.md'))
    (out / 'preparation.json').write_text(json.dumps(result, indent=2))
    print('PREPARED:', out, flush=True)


if __name__ == '__main__':
    main()
