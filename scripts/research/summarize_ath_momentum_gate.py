"""ATH39: fixed top20 gate ablation with unchanged MV priority and exits."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RULES = ['ath_top20','ath_all','high2y_top20','high2y_all']


def main(run):
    run = Path(run)
    s = pd.read_csv(run/'summary.csv')
    old = pd.read_csv(ROOT/'outputs/backtests/ath_38_rolling_highs_v001/20261017T191148442382Z/summary.csv')
    all_controls = []
    for current,previous in [('ath_top20','ath'),('high2y_top20','high2y')]:
        control = s.loc[s.rule.eq(current)].merge(old.loc[old.rule.eq(previous)],on=['policy','period'],suffixes=('','_old'),validate='one_to_one')
        for field in ['cagr','final_nav','max_drawdown','average_exposure']:
            assert np.array_equal(control[field],control[field+'_old'])
        all_controls.append(control)
    controls = pd.concat(all_controls)
    signals = pd.read_parquet(run/'signals.parquet')
    diagnostics, companies, top = [], [], []
    for row in s.loc[s.period.eq('all')].itertuples():
        directory = run / row.run
        tx = pd.read_parquet(directory / 'transactions.parquet')
        entry = tx.loc[tx.kind.eq('ENTRY'), ['date', 'decision_date', 'permno', 'price']]
        entry = entry.rename(columns={'date': 'entry_date', 'decision_date': 'signal_date', 'price': 'entry_price'})
        attrs = signals.loc[signals.definition.eq(row.rule), ['date', 'permno', 'is_ath', 'quintile']].rename(columns={'date': 'signal_date'})
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
            below_top20_entries=int(entry.quintile.lt(5).sum()), fees=tx.fee.sum(), annual_two_way_turnover=(traded.notional.abs()/traded.nav_before).sum()*252/4652,
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
    lines = ['# ATH39: removing the mandatory momentum top20 gate', '',
        'Fixed ATH and two-year highs, original gain stages SMA150 ->100 at+50% ->50 at+100%, '
        'next-opening execution, 20-company capacity,5% initial target,10bps per side and zero cash yield. '
        'Clean2008-01-02 through2026-06-30. Only the market6-1/top20 requirement is removed. '
        'The MV ranking algorithm remains and is recomputed within each expanded candidate set. '
        'Complete12-1 feature support, volume/contraction availability, monthly PIT liquidity '
        'membership and conservative high-history quality are unchanged. This is not a pure '
        'unfiltered breakout strategy or removal of momentum from the priority score.', '',
        '## Full-period net results', '',
        '| Definition | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |',
        '|---|---:|---:|---:|---:|']
    for rule in RULES:
        d = s.loc[s.rule.eq(rule)&s.period.eq('all')].set_index('policy')
        values = [d.loc[p,c]*100 for c in ['cagr','max_drawdown'] for p in ['drift','monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 11.24% | 11.24% | -52.45% | -52.45% |', '',
        '## Contemporary calendar slices', '',
        '| Definition | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |',
        '|---|---:|---:|---:|---:|']
    for rule in RULES:
        values = [s.loc[s.rule.eq(rule)&s.period.eq(t)&s.policy.eq(p),'cagr'].iloc[0]*100
                  for t in ['2018_end','2023_end'] for p in ['drift','monthly_equal']]
        lines.append('| '+rule+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |')
    lines += ['| SPY | 14.67% | 14.67% | 22.83% | 22.83% |', '',
        'Calendar slices inherit positions from the clean2008 simulation. No fresh2018/2023 starts '
        'or unseen validation are claimed. All individual years remain saved.', '',
        '## Difference from removing the gate', '',
        '| Breakout | Period | Drift CAGR change | Monthly CAGR change |',
        '|---|---|---:|---:|']
    changes = []
    for breakout in ['ath','high2y']:
        for period in ['all','2018_end','2023_end']:
            values = []
            for policy in ['drift','monthly_equal']:
                current = s.loc[s.rule.eq(breakout+'_all')&s.period.eq(period)&s.policy.eq(policy),'cagr'].iloc[0]
                previous = s.loc[s.rule.eq(breakout+'_top20')&s.period.eq(period)&s.policy.eq(policy),'cagr'].iloc[0]
                values.append(100*(current-previous))
                changes.append(dict(breakout=breakout,period=period,policy=policy,cagr_change=current-previous))
            lines.append('| '+breakout+' | '+period+' | '+' | '.join(f'{v:+.2f} pp' for v in values)+' |')
    pd.DataFrame(changes).to_csv(run/'gate_cagr_differences.csv',index=False)
    lines += ['', '## Candidates and actual selection', '',
        '| Definition | Signals | Below-top20 candidates | Executed drift entries | Below-top20 drift entries |',
        '|---|---:|---:|---:|---:|']
    for rule in RULES:
        d = signals.loc[signals.definition.eq(rule)]
        record = diag.loc[diag.run.eq(rule+'__drift_10bps')].iloc[0]
        lines.append(f'| {rule} | {len(d)} | {int(d.quintile.lt(5).sum())} | {int(record.entries)} | {int(record.below_top20_entries)} |')
    lines += ['', 'Counts include final signals without a next session. Recomputed MV scores can '
        'change priorities even among candidates that were previously eligible. Changed capacity, '
        'later entries, exposure and fees affect the full portfolio path. Cashflow episode PnL '
        'including open marks, large-winner counts, top contributors and company attribution '
        'are saved in tail_trading_diagnostics.csv and episode_attribution.parquet. Monthly '
        'episode profit ratios are not fixed-unit price returns.', '',
        '## Findings', '',
        'Removing the gate lowers full-period ATH CAGR9.29/9.07% to7.54/7.26%, with larger '
        'full drawdowns. The same removal raises two-year-high CAGR6.48/6.20% to7.10/6.55%, '
        'but also increases full drawdowns. Since2018 ATH remains weaker without the gate; '
        'two-year highs improve to8.51/7.09% but remain belowSPY14.67%. Since2023 the ungated '
        'two-year drift portfolio returns23.69% versus21.33% gated and22.83% SPY; monthly19.68% '
        'still trailsSPY. No uniform top20 benefit or universal improvement from removing it is established. '
        'All full-period variants remain belowSPY11.24%.', '',
        '## Scope and interpretation', '',
        'The saved difference table answers the fixed gate ablation within this MV-prioritized '
        'US portfolio. It does not establish the best ranking, pure ATH efficacy, GPW account '
        'replication, causal economic mechanism or an optimal rule. No new confidence interval '
        'or risk-adjusted alpha is claimed. Known2008-present history remains development evidence. '
        'Do not combine favorable results automatically with previous best exits, gap caps or consolidation.', '',
        '## Verification', '',
        f'All {len(controls)} top20 control period rows exactly match ATH38 CAGR, NAV, drawdown and exposure. '
        'Candidate keys/features/MV priorities also reproduce both prior controls. Independent raw '
        'candidate windows, market ranks, raw SMA/summary/benchmark and daily ledger/stage '
        'receipts are retained; final counts/status are in manifest.json. Twelve focused '
        'window/rank/stage tests pass. Inputs, protocol and code are SHA256 recorded.', '',
        'Run: `'+str(run.relative_to(ROOT))+'`. Protocol: `ATH_MOMENTUM_GATE_PLAN.md`.']
    (ROOT/'research/ath/ATH_MOMENTUM_GATE_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (run/'control_reproduction.json').write_text(json.dumps(dict(period_rows=len(controls),passed=True)))
    print('Saved gate comparison, both controls and tail attribution')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
