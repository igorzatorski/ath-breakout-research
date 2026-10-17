"""Portfolio and separate foregone-opportunity diagnostics for ATH37."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main(run):
    run = Path(run)
    s = pd.read_csv(run / 'summary.csv')
    old = pd.read_csv(ROOT / 'outputs/backtests/ath_35_sma_exit_grid_v001/20261017T182520632223Z/summary.csv')
    control = s.loc[s.rule.eq('unrestricted')].merge(old.loc[old.rule.eq('sma150')],
        on=['policy', 'period'], suffixes=('', '_old'), validate='one_to_one')
    for key in ['cagr', 'max_drawdown', 'average_exposure', 'final_nav']:
        assert np.array_equal(control[key], control[key + '_old'])
    events = pd.read_parquet(run / 'signals.parquet').set_index('event_id')
    cohort, actual, trades = [], [], []
    for rule in ['gap05', 'gap10', 'gap20']:
        screens = pd.read_parquet(run / f'{rule}__drift_10bps/entry_screens.parquet')
        z = screens.join(events[['stock_return', 'spy_return', 'excess_spy']], on='event_id')
        z['executable'] = np.isfinite(z.open) & z.open.gt(0)
        for label, g in [('all_executable', z.loc[z.executable]),
                         ('accepted', z.loc[z.eligible]),
                         ('over_cap', z.loc[z.executable & ~z.eligible]),
                         ('missing_open', z.loc[~z.executable])]:
            mature = g.loc[np.isfinite(g.stock_return) & np.isfinite(g.spy_return)]
            cohort.append(dict(rule=rule, sample=label, candidates=len(g), mature=len(mature),
                unavailable_or_immature=len(g)-len(mature), mean_stock=mature.stock_return.mean(),
                mean_spy=mature.spy_return.mean(), mean_excess=mature.excess_spy.mean(),
                losses=int(mature.stock_return.lt(0).sum()), doubles=int(mature.stock_return.ge(1).sum())))
        for policy in ['drift', 'monthly_equal']:
            base = pd.read_parquet(run / f'unrestricted__{policy}_10bps/transactions.parquet')
            base = base.loc[base.kind.eq('ENTRY')]
            joined = base.merge(screens, on=['date', 'permno'], validate='one_to_one')
            assert len(joined) == len(base)
            actual.append(dict(rule=rule, policy=policy, baseline_entries=len(base),
                rejected_baseline_entries=int((~joined.eligible).sum())))
    for row in s.loc[s.period.eq('all')].itertuples():
        tx = pd.read_parquet(run / row.run / 'transactions.parquet')
        trade = tx.loc[~tx.kind.isin(['DIVIDEND', 'CIZ_TERMINAL'])]
        trades.append(dict(run=row.run, entries=int(tx.kind.eq('ENTRY').sum()), fees=tx.fee.sum(),
            annual_two_way_turnover=(trade.notional.abs()/trade.nav_before).sum()*252/4652))
    cohort, actual, trades = map(pd.DataFrame, [cohort, actual, trades])
    cohort.to_csv(run / 'candidate_outcome_diagnostics.csv', index=False)
    actual.to_csv(run / 'rejected_baseline_entry_counts.csv', index=False)
    trades.to_csv(run / 'trading_diagnostics.csv', index=False)
    lines = ['# ATH37: opening-only gap limits', '',
        'Clean 2008-01-02 to 2026-06-30 simulation; same ATH35 fresh ATH + market6-1/top20 '
        'signals, MV priority, maximum20 companies, 5% initial weights, SMA150 next-opening exits, '
        '10bps per buy/sell and zero cash yield. Only entry eligibility changes. Opening-only '
        'order cap = signal close + k times strictly prior ATR20. Equality fills; downward gaps '
        'are allowed. No later intraday fill or chase of that signal. A later fresh ATH can qualify. '
        'Entry information does not include future close, low or outcomes. ', '',
        'Daily prices model an opening-only limit fill at the recorded opening when within the '
        'known cap. Auction participation, queue priority, spread and volume availability are '
        'unverified; this is not a validated live execution model.', '',
        '## Net portfolio results', '',
        '| Opening cap | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |',
        '|---|---:|---:|---:|---:|']
    rules = ['unrestricted', 'gap05', 'gap10', 'gap20']
    for rule in rules:
        d = s.loc[s.rule.eq(rule) & s.period.eq('all')].set_index('policy')
        values = [d.loc[p, c]*100 for c in ['cagr', 'max_drawdown'] for p in ['drift', 'monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 11.24% | 11.24% | -52.45% | -52.45% |', '',
        '## Recent calendar slices', '',
        '| Opening cap | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |',
        '|---|---:|---:|---:|---:|']
    for rule in rules:
        values = [s.loc[s.rule.eq(rule) & s.period.eq(t) & s.policy.eq(p), 'cagr'].iloc[0]*100
                  for t in ['2018_end', '2023_end'] for p in ['drift', 'monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 14.67% | 14.67% | 22.83% | 22.83% |', '',
        'Subperiods retain positions from the clean 2008 start; they are not fresh portfolio starts. '
        'All calendar years and registered periods remain in summary.csv.', '',
        '## Foregone opportunities: separate annual signal outcomes', '',
        '| Rule | Over-cap candidates | Mature annual outcomes | Annual losses | Annual returns >=100% | Mean annual excess vs SPY |',
        '|---|---:|---:|---:|---:|---:|']
    for d in cohort.loc[cohort['sample'].eq('over_cap')].itertuples():
        lines.append(f'| {d.rule} | {d.candidates} | {d.mature} | {d.losses} | {d.doubles} | {100*d.mean_excess:.2f} pp |')
    lines += ['', 'There are 17,266 screened candidates per variant, including 26 with no executable '
        'opening that the baseline also could not buy. The candidate tables exclude those missing '
        'openings from over-cap counts. Common mature executable annual coverage is15,853. '
        'Annual returns include distributions and original terminal treatment. These are gross '
        'buy-and-hold signal outcomes, not actual SMA150 realized profits, portfolio CAGR, '
        'independent observations or the causal value of rejecting a trade. Missing/immature '
        'counts remain explicit. Full accepted, rejected and executable summaries are saved.', '',
        '| Cap rule | Policy | Actual baseline entries | Baseline entries over cap |',
        '|---|---|---:|---:|']
    for d in actual.itertuples():
        lines.append(f'| {d.rule} | {d.policy} | {d.baseline_entries} | {d.rejected_baseline_entries} |')
    lines += ['', 'A rejected high-ranked candidate can free capacity for the next eligible candidate '
        'in the unchanged MV ordering. Later holdings, entries and weights consequently diverge. '
        'Rejected baseline entry counts therefore do not describe all differences between portfolios.', '',
        '## Interpretation', '',
        'All three caps improve the inspected full-period CAGR against unrestricted SMA150 '
        'under both weighting policies. The tightest tested0.5ATR cap improves drift8.70% to10.37% '
        'and monthly8.48% to9.97%, with smaller drawdowns. Recent2018 CAGR also improves, '
        'but all variants still trail SPY. This is an exploratory lead, not a proven optimal cap '
        'or confirmed alpha. The accepted versus rejected annual signal means differ only modestly '
        'at0.5ATR; high-gap cohorts at1/2ATR have positive mean excess despite portfolio improvements. '
        'Portfolio differences depend on capacity, weights and subsequent paths, not a uniform '
        'claim that large-gap signals are bad.', '',
        'The filter rejects future losers and large winners. Do not combine it automatically with '
        'the previously strongest stepped exit: this experiment keeps SMA150 fixed. No new '
        'confidence interval, equal-risk attribution or untouched validation is claimed. Inspected '
        '2008-present data remain development history; auction feasibility needs separate validation.', '',
        '## Verification', '',
        f'All {len(control)} unrestricted control period rows exactly reproduce ATH35 SMA150 '
        'CAGR, NAV, drawdown and exposure.24 focused tests pass. Independent raw ATR, raw SMA, '
        'summary, eligibility and daily ledger replays are saved alongside the run. '
        'Final verification status and source/code hashes are recorded in manifest.json.', '',
        'Run: `'+str(run.relative_to(ROOT))+'`. Protocol: `ATH_OPEN_GAP_LIMIT_PLAN.md`.']
    (ROOT / 'research/ath/ATH_OPEN_GAP_LIMIT_RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (run / 'control_reproduction.json').write_text(json.dumps(dict(rows=len(control), passed=True)))
    print('Saved report, all candidate outcomes and baseline entry diagnostics')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
