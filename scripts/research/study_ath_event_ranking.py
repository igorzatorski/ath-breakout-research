"""Three same-date rankings, date-balanced outcomes and recent episodes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.event_ranking import (  # noqa: E402
    rank_events, common_dates, groups, contrast_matrix, balanced_draws, intervals,
)
from study_ath_consolidation_grid import describe  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402

SOURCE = ROOT/'outputs/research/ath/ath_26_filter_combinations_v001/20261017T133039984401Z'


def main():
    out = ROOT/f'outputs/research/ath/ath_27_event_ranking_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    print(out, flush=True)
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    assert sha256(SOURCE/'events.parquet') == manifest['artifacts']['events.parquet']
    raw = pd.read_parquet(SOURCE/'events.parquet')
    z = rank_events(raw)
    year = z.date.dt.year
    z['episode'] = np.select([year.between(2018, 2020), year.between(2021, 2022), year.ge(2023)],
        ['2018_2020', '2021_2022', '2023_partial2025'], default='before2018')
    annual = z.loc[z.excess_spy.notna()]
    assert len(annual) == 23712
    dates = common_dates(annual)
    z['primary_evaluation'] = z.date.isin(dates) & z.excess_spy.notna() & z.candidate_date_supported
    sensitivity_dates = common_dates(annual.loc[annual.nonoverlap], top_only=True)
    z['nonoverlap_top_evaluation'] = z.nonoverlap & z.date.isin(sensitivity_dates) & z.excess_spy.notna() & z.candidate_date_supported
    z.to_parquet(out/'events.parquet', index=False)
    coverage = [('original_annual', z.loc[z.excess_spy.notna()]),
        ('candidate_date_supported_annual', z.loc[z.excess_spy.notna() & z.candidate_date_supported]),
        ('primary_common_dates', z.loc[z.primary_evaluation]),
        ('excluded_from_primary', z.loc[z.excess_spy.notna() & ~z.primary_evaluation]),
        ('original_nonoverlap_annual', z.loc[z.excess_spy.notna() & z.nonoverlap]),
        ('nonoverlap_common_top_dates', z.loc[z.nonoverlap_top_evaluation])]
    pd.DataFrame([dict(sample=name, dates=f.date.nunique(), **describe(f)) for name, f in coverage]).to_csv(out/'coverage.csv', index=False)
    z.assign(annual=z.excess_spy.notna()).groupby([year.rename('year'), 'candidate_date_supported',
        'annual', 'primary_evaluation']).size().rename('events').to_csv(out/'support_by_year.csv')
    summaries, all_intervals, overlaps = [], [], []
    for evaluation, flag, top_only in [('primary', 'primary_evaluation', False),
        ('nonoverlap_top', 'nonoverlap_top_evaluation', True)]:
        f = z.loc[z[flag]]
        if f.empty:
            (out/f'{evaluation}_unavailable.json').write_text(json.dumps({'reason': 'No common supported dates'}))
            continue
        names, membership = groups(f, top_only=top_only)
        definitions, coefficients = contrast_matrix(names, top_only=top_only)
        definitions.to_csv(out/f'contrasts_{evaluation}.csv', index=False)
        np.save(out/f'coefficients_{evaluation}.npy', coefficients)
        for i in range(1, len(names)):
            if not names[i].endswith('Q5'):
                continue
            for j in range(i+1, len(names)):
                if names[j].endswith('Q5'):
                    a, b = membership[:, i], membership[:, j]
                    overlaps.append(dict(evaluation=evaluation, first=names[i], second=names[j],
                        intersection=int((a & b).sum()), union=int((a | b).sum()), jaccard=(a & b).sum()/(a | b).sum()))
        periods = [('all', f), *[(p, f.loc[f.period.eq(p)]) for p in ['early', 'middle', 'recent']],
            *[(p, f.loc[f.episode.eq(p)]) for p in ['2018_2020', '2021_2022', '2023_partial2025']],
            *[(str(y), a) for y, a in f.groupby(f.date.dt.year)]]
        for period, sample in periods:
            labels, selected = groups(sample, top_only=top_only)
            reference_by_date = sample.groupby('date').excess_spy.mean()
            for j, name in enumerate(labels):
                g = sample.loc[selected[:, j]]
                date_means = g.groupby('date')[['stock_return', 'spy_return', 'excess_spy']].mean()
                row = dict(evaluation=evaluation, period=period, group=name, dates=g.date.nunique(),
                    stock_equal_date=date_means.stock_return.mean(), spy_equal_date=date_means.spy_return.mean(),
                    excess_equal_date=date_means.excess_spy.mean(),
                    improvement_equal_date=(date_means.excess_spy-reference_by_date).mean(),
                    median_stock=g.stock_return.median(), sample_skew=g.stock_return.skew(), **describe(g))
                for level in [1, 2, 3]:
                    win = g.stock_return.ge(level-1e-12)
                    available = sample.stock_return.ge(level-1e-12).sum()
                    row[f'winners_{level*100}'] = int(win.sum())
                    row[f'fraction_{level*100}'] = win.mean()
                    row[f'retention_{level*100}'] = win.sum()/available if available else np.nan
                summaries.append(row)
        for block in [252, 504]:
            print(f'Date-balanced ranking bootstrap {evaluation} block{block}: {len(f)} events/{f.date.nunique()} dates', flush=True)
            points, samples = balanced_draws(f, membership, valid_nyse_sessions(f.date.min(), f.date.max()), block)
            np.savez_compressed(out/f'draws_{evaluation}_{block}.npz', points=points, samples=samples, groups=np.asarray(names))
            rows = intervals(points, samples, definitions, coefficients)
            rows.insert(0, 'evaluation', evaluation)
            rows.insert(1, 'block', block)
            all_intervals.append(rows)
    s = pd.DataFrame(summaries)
    s.to_csv(out/'summary.csv', index=False)
    pd.concat(all_intervals, ignore_index=True).to_csv(out/'uncertainty.csv', index=False)
    pd.DataFrame(overlaps).to_csv(out/'top_overlap.csv', index=False)
    print(s.loc[s.evaluation.eq('primary') & s.period.eq('all'),
        ['group', 'events', 'dates', 'stock_equal_date', 'spy_equal_date', 'excess_equal_date', 'improvement_equal_date']].to_string(index=False), flush=True)
    code = [Path(__file__), ROOT/'src/ath_breakout/research/event_ranking.py', ROOT/'scripts/research/study_ath_consolidation_grid.py']
    result = dict(study_id='ath_27_event_ranking_v001', inputs={str((SOURCE/'events.parquet').relative_to(ROOT)): sha256(SOURCE/'events.parquet'),
        str((SOURCE/'manifest.json').relative_to(ROOT)): sha256(SOURCE/'manifest.json')}, models=['M', 'MV', 'MVC'],
        min_candidates=5, volume_cap=2, contraction_half=42, draws=2000, seed=20261017, blocks=[252, 504],
        resampling='positive exponential company weights crossed with circular calendar blocks; approximate diagnostic',
        code={str(p.relative_to(ROOT)): sha256(p) for p in code}, protocol_sha256=sha256(ROOT/'research/ath/ATH_RANKING_PLAN.md'))
    result['artifacts'] = {p.name: sha256(p) for p in out.iterdir() if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(result, indent=2))
    print(out, flush=True)


if __name__ == '__main__':
    main()
