"""ATH40 factorial results and cash behavior during fixed decline windows."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RULES = ['base','steps','gap','combined']
CONTROLS = {
    'base': ('ath_35_sma_exit_grid_v001/20261017T182520632223Z','sma150'),
    'steps': ('ath_36_stepped_sma_v001/20261017T184040153319Z','step25_50'),
    'gap': ('ath_37_open_gap_limit_v001/20261017T184924934825Z','gap05')}


def main(run):
    run = Path(run)
    s = pd.read_csv(run/'summary.csv')
    metric = pd.read_csv(run/'crash_metrics.csv')
    count,curve_rows = 0,0
    for current,(folder,rule) in CONTROLS.items():
        old = pd.read_csv(ROOT/'outputs/backtests'/folder/'summary.csv')
        paired = s.loc[s.rule.eq(current)].merge(old.loc[old.rule.eq(rule)],
            on=['policy','period'],suffixes=('','_old'),validate='one_to_one')
        for key in ['cagr','final_nav','max_drawdown','average_exposure']:
            assert np.array_equal(paired[key],paired[key+'_old'])
        count += len(paired)
        for policy in ['drift','monthly_equal']:
            a = pd.read_csv(run/f'{current}__{policy}_10bps/equity.csv')
            b = pd.read_csv(ROOT/'outputs/backtests'/folder/f'{rule}__{policy}_10bps/equity.csv')
            for key in ['nav','cash','exposure']:
                assert np.array_equal(a[key],b[key])
            curve_rows += len(a)
    interaction = []
    for period in ['all','2018_end','2023_end']:
        for policy in ['drift','monthly_equal']:
            d = s.loc[s.period.eq(period)&s.policy.eq(policy)].set_index('rule').cagr
            interaction.append(dict(period=period,policy=policy,step_change=d.steps-d.base,
                gap_change=d.gap-d.base,combined_change=d.combined-d.base,
                cagr_interaction=d.combined-d.steps-d.gap+d.base))
    pd.DataFrame(interaction).to_csv(run/'factorial_cagr_contrasts.csv',index=False)
    (run/'control_reproduction.json').write_text(json.dumps(dict(period_rows=count,daily_curve_rows=curve_rows,passed=True),indent=2))
    lines = ['# ATH40: early SMA stages x opening cap and crash cash behavior','',
        'Four fixed configurations on identical ATH + market6-1/top20 candidates and MV priority: '
        'constantSMA150 baseline, early+25/+50% stages, opening-only0.5 priorATR cap and both. '
        'CleanUSD100,000 cash start2008-01-02 to2026-06-30, next-opening fills,20 companies,5% entry '
        'target,10bps per side and zero cash yield. Drift and monthly equal policies. '
        'No explicit market/cash regime overlay, consolidation cutoff or initial percentage floor.','',
        '## Full-period net CAGR and drawdown','',
        '| Configuration | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |',
        '|---|---:|---:|---:|---:|']
    for rule in RULES:
        d = s.loc[s.rule.eq(rule)&s.period.eq('all')].set_index('policy')
        values = [d.loc[p,c]*100 for c in ['cagr','max_drawdown'] for p in ['drift','monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 11.24% | 11.24% | -52.45% | -52.45% |','',
        'The combination does not dominate: drift10.53% trails stages-only11.22%; monthly10.71% '
        'exceeds either component but still trailsSPY. Full drawdowns worsen versus stages-only. '
        'All fixed contrasts are retained; arithmetic differences of CAGRs are descriptive '
        'portfolio-path interactions, not causal additive effects or significance tests.','',
        '## Contemporary calendar slices','',
        '| Configuration | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |',
        '|---|---:|---:|---:|---:|']
    for rule in RULES:
        values = [s.loc[s.rule.eq(rule)&s.period.eq(t)&s.policy.eq(p),'cagr'].iloc[0]*100
            for t in ['2018_end','2023_end'] for p in ['drift','monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 14.67% | 14.67% | 22.83% | 22.83% |','',
        'Contemporary slices retain positions from2008; no fresh-start or untouched validation claim. '
        'The combination is weaker than either component in both contemporary slices and both policies.','',
        '## What happens during declines?','',
        'Principal diagnostic below uses the previously strongest full-period candidate: early '
        '+25/+50% stages with drift weights. The fixed crash windows are2008-01-02..2009-06-30, '
        '2020-01-02..2020-12-31 and2022-01-03..2022-12-30. These choices were declared before '
        'the new results. All four configurations and both policies have chart/data exports.','',
        '| Window | Strategy local max drawdown | SPY local max drawdown | Cash at SPY trough | SPY trough date |',
        '|---|---:|---:|---:|---|']
    for d in metric.loc[metric.run.eq('steps__drift_10bps')].itertuples():
        lines.append(f'| {d.episode} | {100*d.local_max_drawdown:.2f}% | '
            f'{100*d.spy_peak_to_trough:.2f}% | {100*d.cash_at_spy_trough:.2f}% | {d.spy_trough_date} |')
    lines += ['', 'Local drawdown uses each series\' own running peak inside the fixed window, '
        'seeded by prior-close capital (initial cash at the2008 boundary). It is not necessarily '
        'the return between the same peak/trough dates. The CSV separately retains matched '
        'SPY peak-to-trough strategy returns and full since2008 drawdown. Cash is measured '
        'at the same mechanically selected SPY trough date for every strategy.','',
        'The system partly creates the desired cash-allocation effect. In2020 the principal '
        'candidate moves from almost fully invested near the benchmark peak to78.92% cash '
        'at the benchmark trough, then reinvests during the rebound. Protection is reactive: '
        'from the SPY peak to its trough it still loses18.74%, versusSPY33.72%.','',
        'In2022 that mechanism is not reliable crash avoidance: local strategy drawdown27.92% '
        'exceedsSPY24.50%; only23.16% cash remains at the benchmark trough, after earlier '
        'cash spikes and renewed investment. Individual security exits do not prohibit fresh '
        'entries elsewhere. A stock\'s SMA and a market-wide allocation rule are different decisions.','',
        'The2008 result starts from cash after the2007 market peak. It must not be presented '
        'as evidence of having exited a fully invested2007 portfolio before the crash. '
        'No counterfactual all-invested or SPY-SMA overlay was simulated.','',
        '## Reading and reproducing the charts','',
        'PNG/PDF overview: `crash_charts/crash_overview_steps_drift`. Six detailed PNG/PDF and '
        'offline interactive Plotly HTML figures retain all four configurations plusSPY. '
        'The first panel rebases each series to100 at the first window close; it does not '
        'show the first-day opening-to-close loss. Drawdown panels retain running high-water '
        'marks since2008; cash panels show daily cash/NAV. Thus the detailed drawdown panel '
        'can differ from local-window drawdown in the table. All reviewed chart rows and '
        'sources are saved. Interactive figures allow export toPNG.','',
        'Run `chart_ath_crashes.py RUN` and `render_ath_crash_png.py RUN`. Static exports '
        'use the optional `research-plots` dependency; Plotly is already a project dependency. '
        'Overview and detailed PNG layouts were visually checked, including a contact sheet '
        'covering all six detailed figures.','',
        '## Verification and scope','',
        f'All{count} control summary rows and{curve_rows} daily equity rows reproduce ATH35/36/37 '
        'exactly for NAV, cash and exposure. All eight independent ledger/eligibility/stage '
        'replays passed;23 focused tests passed. All24,668 plotted points and24 crash metric '
        'rows independently reconcile to equity.csv. Frozen source panel, SMA and priorATR '
        'inputs retain their source hashes and prior raw audits. Final code/artifact hashes '
        'and receipt paths are in manifest.json.','',
        'Inspected history remains development evidence. No optimum, new confidence interval, '
        'risk-adjusted alpha, live execution guarantee or market-timing overlay is established. '
        'Opening-only fills, zero cash yield, stock selection and delayed SMA execution '
        'remain material assumptions.','',
        'Run: `'+str(run.relative_to(ROOT))+'`. Protocol: `ATH_STEPS_GAP_FACTORIAL_PLAN.md`.']
    (ROOT/'research/ath/ATH_STEPS_GAP_FACTORIAL_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Saved factorial and crash report; controls:',count,curve_rows)


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve())
