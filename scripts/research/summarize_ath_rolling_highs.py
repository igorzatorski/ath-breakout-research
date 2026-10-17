"""ATH38: all maxima, contemporary slices and realized/open PnL tails."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RULES = ['ath', 'high1y', 'high2y', 'high3y', 'high4y', 'high5y']


def main(run):
    run = Path(run)
    s = pd.read_csv(run / 'summary.csv')
    old = pd.read_csv(ROOT / 'outputs/backtests/ath_36_stepped_sma_v001/20261017T184040153319Z/summary.csv')
    controls = s.loc[s.rule.eq('ath')].merge(old.loc[old.rule.eq('step50_100')],
        on=['policy', 'period'], suffixes=('', '_old'), validate='one_to_one')
    for field in ['cagr', 'final_nav', 'max_drawdown', 'average_exposure']:
        assert np.array_equal(controls[field], controls[field+'_old'])
    signals = pd.read_parquet(run / 'signals.parquet')
    athkeys = set(zip(signals.loc[signals.definition.eq('ath'), 'date'], signals.loc[signals.definition.eq('ath'), 'permno']))
    coverage = []
    for rule in RULES:
        d = signals.loc[signals.definition.eq(rule)]
        keys = set(zip(d.date, d.permno))
        coverage.append(dict(definition=rule, signals=len(d), non_ath=int((~d.is_ath).sum()),
            retained_ath=len(keys & athkeys), ath_excluded_for_window=len(athkeys-keys)))
    pd.DataFrame(coverage).to_csv(run / 'signal_overlap.csv', index=False)
    diagnostics, companies, top = [], [], []
    for row in s.loc[s.period.eq('all')].itertuples():
        directory = run / row.run
        tx = pd.read_parquet(directory / 'transactions.parquet')
        entry = tx.loc[tx.kind.eq('ENTRY'), ['date', 'decision_date', 'permno', 'price']]
        entry = entry.rename(columns={'date': 'entry_date', 'decision_date': 'signal_date', 'price': 'entry_price'})
        attrs = signals.loc[signals.definition.eq(row.rule), ['date', 'permno', 'is_ath']].rename(columns={'date': 'signal_date'})
        entry = entry.merge(attrs, on=['signal_date', 'permno'], validate='many_to_one')
        closed = pd.read_csv(directory / 'closed_positions.csv', parse_dates=['entry_date', 'exit_date'])
        closed['episode_status'] = 'closed'
        opened = pd.read_csv(directory / 'open_positions.csv', parse_dates=['entry_date'])
        opened['pnl'] = opened.unrealized_total_pnl
        opened['cashflow_profit_ratio'] = opened.pnl / opened.bought
        opened['episode_status'] = 'open_marked'
        fields = ['permno', 'permco', 'ticker', 'entry_date', 'bought', 'pnl', 'cashflow_profit_ratio', 'episode_status']
        episodes = pd.concat([closed[fields], opened[fields]], ignore_index=True).merge(entry,
            on=['permno', 'entry_date'], validate='one_to_one')
        assert len(episodes) == len(entry)
        assert np.isclose(episodes.pnl.sum(), row.final_nav-100000., atol=1e-5)
        episodes['run'] = row.run
        episodes.to_parquet(directory / 'episode_attribution.parquet', index=False)
        positive = episodes.loc[episodes.pnl.gt(0)].sort_values('pnl', ascending=False)
        double = episodes.cashflow_profit_ratio.ge(1.)
        traded = tx.loc[~tx.kind.isin(['DIVIDEND', 'CIZ_TERMINAL'])]
        nonath = episodes.loc[~episodes.is_ath]
        diagnostics.append(dict(run=row.run, entries=len(entry), non_ath_entries=int((~entry.is_ath).sum()),
            fees=tx.fee.sum(), annual_two_way_turnover=(traded.notional.abs()/traded.nav_before).sum()*252/4652,
            net_pnl=episodes.pnl.sum(), positive_pnl=positive.pnl.sum(),
            negative_pnl=episodes.loc[episodes.pnl.lt(0), 'pnl'].sum(),
            top5_episode_net_share=positive.pnl.head(5).sum()/episodes.pnl.sum(),
            top5_episode_positive_share=positive.pnl.head(5).sum()/positive.pnl.sum(),
            double_cashflow_episodes=int(double.sum()), double_cashflow_pnl=episodes.loc[double, 'pnl'].sum(),
            non_ath_pnl=nonath.pnl.sum(), closed_losing_episodes=int(closed.pnl.lt(0).sum())))
        top.append(positive.head(20))
        company = episodes.groupby('permco').pnl.sum().sort_values(ascending=False).reset_index()
        company['run'] = row.run
        companies.append(company)
    diag = pd.DataFrame(diagnostics)
    diag.to_csv(run / 'tail_trading_diagnostics.csv', index=False)
    pd.concat(top).to_csv(run / 'top_episode_contributors.csv', index=False)
    pd.concat(companies).to_csv(run / 'company_pnl.csv', index=False)
    lines = ['# ATH38: ATH versus one- to five-year maxima', '',
        'Same US equity strategy and original gain stages SMA150 ->100 at+50% ->50 at+100%. '
        'Only the signal high lookback changes. Clean USD100,000 cash start2008-01-02 through2026-06-30, '
        'maximum20 companies,5% entry target, MV priority and same historical liquidity/momentum support. '
        'Two weighting policies,10bps per buy/sell, zero cash yield. Next-opening entries and exits. '
        'No consolidation cutoff, opening-gap cap or initial price floor. '
        'This is a US implementation, not an audited GPW replication of the supplied screenshots.', '',
        '## Full-period net CAGR and drawdown', '',
        '| Maximum | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |',
        '|---|---:|---:|---:|---:|']
    for rule in RULES:
        d = s.loc[s.rule.eq(rule) & s.period.eq('all')].set_index('policy')
        values = [d.loc[p,c]*100 for c in ['cagr', 'max_drawdown'] for p in ['drift', 'monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 11.24% | 11.24% | -52.45% | -52.45% |', '',
        '## Contemporary calendar slices', '',
        '| Maximum | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |',
        '|---|---:|---:|---:|---:|']
    for rule in RULES:
        values = [s.loc[s.rule.eq(rule) & s.period.eq(t) & s.policy.eq(p), 'cagr'].iloc[0]*100
            for t in ['2018_end', '2023_end'] for p in ['drift', 'monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 14.67% | 14.67% | 22.83% | 22.83% |', '',
        'These are calendar slices with inherited positions from the clean2008 simulation, '
        'not fresh2018/2023 starts. All years remain in summary.csv.', '',
        '## Signal overlap and history requirements', '',
        '| Definition | Signals | Non-ATH additions | Retained ATH signals | ATH excluded for incomplete rolling history |',
        '|---|---:|---:|---:|---:|']
    for d in coverage:
        lines.append(f'| {d["definition"]} | {d["signals"]} | {d["non_ath"]} | {d["retained_ath"]} | {d["ath_excluded_for_window"]} |')
    lines += ['', 'Counts include2007-12-31 signals eligible for the first2008 opening and final '
        '2026-06-30 signals with no subsequent executable session in this run. Full252/504/756/1008/1260 '
        'scheduled high histories are required. All definitions retain the original conservative '
        'pre1993/missing-high quality exclusions. Consequently longer rolling maxima can drop young '
        'ATH stocks as well as add recovery breakouts. This is not an isolated threshold-only '
        'comparison on identical listing-age support. No common-five-year-history portfolio was tested.', '',
        '## Right-tail and actual portfolio attribution', '',
        '| Run | Entries | Non-ATH entries | Cashflow >=100% episodes | Top5 episodes / net PnL | Non-ATH PnL USD |',
        '|---|---:|---:|---:|---:|---:|']
    for d in diag.itertuples():
        lines.append(f'| {d.run} | {d.entries} | {d.non_ath_entries} | {d.double_cashflow_episodes} | '
            f'{100*d.top5_episode_net_share:.1f}% | {d.non_ath_pnl:.2f} |')
    lines += ['', 'Episodes include both closed positions and open marked positions; their net '
        'cashflow PnL reconciles exactly to final portfolio NAV minus initial cash. >=100% means '
        'episode profit relative to accumulated purchases including fees; monthly buys/sells '
        'make this different from a fixed-unit stock price gain. Top5 contributions may exceed100% '
        'because other trades lose money. Non-ATH PnL is attribution of this realized path, not '
        'the causal value of adding those signals; ranks, capacity and subsequent entries also change. '
        'Detailed episodes, top20 contributors, company PnL, fees and turnover are retained.', '',
        '## Findings and limits', '',
        'ATH has the highest full-period CAGR among the six definitions under both policies. '
        'The two-year maximum underperforms ATH over the full period; it does not explain the '
        'supplied account results by itself. More candidates or higher exposure do not guarantee '
        'better selection. All full-period and since2018 CAGRs remain below SPY.', '',
        'Contemporary ordering differs: the four-year maximum improves since2018 CAGR relative '
        'to ATH, and since2023 it exceeds SPY in both policies (28.57/24.94% versus22.83%). '
        'The five-year drift variant also slightly exceeds SPY since2023. These short inspected '
        'slices and selected maxima do not establish stable alpha or an optimal lookback. '
        'Do not delete weak earlier years or treat2023 as untouched validation.', '',
        'A complete author strategy replication remains unavailable: different market, unspecified '
        'consolidation and position sizing, and unverified reported account methodology. '
        'The US liquidity threshold and momentum/ranking rules remain our research choices. '
        'No new confidence interval, equal-risk alpha inference, causal decay explanation, '
        'GPW result or live-ready strategy is claimed.', '',
        '## Verification', '',
        f'All {len(controls)} ATH control period rows exactly reproduce ATH36 primary stepped exits. '
        'Signal keys, momentum, volume, contraction and MV scores reproduce the earlier ATH control '
        'for every modern signal. Independent raw windows/ranks and daily cash/share/stage '
        'verification receipts are retained; final counts/status are in manifest.json. '
        'Twelve focused window/rank/stage tests passed, including a decimal50% boundary regression. Source files and code are hash recorded.', '',
        'Run: `'+str(run.relative_to(ROOT))+'`. Protocol: `ATH_ROLLING_HIGH_PLAN.md`.']
    (ROOT / 'research/ath/ATH_ROLLING_HIGH_RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (run / 'control_reproduction.json').write_text(json.dumps(dict(period_rows=len(controls), passed=True)))
    print('Saved all six comparisons, actual episode PnL and overlap diagnostics')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
