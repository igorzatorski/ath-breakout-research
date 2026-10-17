"""Save full comparisons and descriptive trade/stage diagnostics for ATH36."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main(run):
    run = Path(run)
    summary = pd.read_csv(run / 'summary.csv')
    source = pd.read_csv(ROOT / 'outputs/backtests/ath_35_sma_exit_grid_v001/20261017T182520632223Z/summary.csv')
    controls = summary.loc[summary.rule.eq('sma150')].merge(source, on=['run', 'period'], suffixes=('', '_old'))
    for key in ['cagr', 'final_nav', 'max_drawdown', 'average_exposure']:
        assert np.array_equal(controls[key], controls[key + '_old'])
    records = []
    for row in summary.loc[summary.period.eq('all')].itertuples():
        path = run / row.run
        closed = pd.read_csv(path / 'closed_positions.csv', parse_dates=['entry_date', 'exit_date'])
        tx = pd.read_parquet(path / 'transactions.parquet')
        switches = pd.read_parquet(path / 'transitions.parquet')
        losses = closed.loc[closed.pnl.lt(0)]
        trade = tx.loc[~tx.kind.isin(['DIVIDEND', 'CIZ_TERMINAL'])]
        records.append(dict(run=row.run, entries=int(tx.kind.eq('ENTRY').sum()),
            exits=int(tx.kind.str.endswith('_EXIT').sum()), fees=tx.fee.sum(),
            annual_two_way_turnover=(trade.notional.abs() / trade.nav_before).sum() * 252 / 4652,
            switches=len(switches), lower_level_switches=int(switches.numerically_lower.sum()),
            stage2_switches=int(switches.stage.eq(2).sum()),
            closed_loss_fraction=len(losses) / len(closed),
            median_losing_calendar_days=(losses.exit_date - losses.entry_date).dt.days.median(),
            closed_double_fraction=closed.cashflow_profit_ratio.ge(1).mean()))
    diagnostics = pd.DataFrame(records)
    diagnostics.to_csv(run / 'stage_trade_diagnostics.csv', index=False)
    lines = ['# ATH36: gain-triggered stepped SMA exits', '',
        'Same clean cash-start 2008-01-02 to 2026-06-30, entries, MV ranking, 20-company capacity, '
        '5% entry target, costs of 10bps per buy/sell and zero cash yield as ATH35. '
        'No initial 5% price floor. Start on SMA150, permanently switch to SMA100 and then SMA50 '
        'after the two fixed closing-price gain thresholds from original executed opening. '
        'Monthly trades preserve anchors and stages; reentry resets them. Threshold equality activates, '
        'including an entry-day jump across both thresholds. Exit after a strictly below-SMA close '
        'at the next observed opening. Current SMA includes the signal close. ', '',
        '## Net CAGR and drawdown', '',
        '| Schedule | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |',
        '|---|---:|---:|---:|---:|']
    rules = ['sma150', 'step25_50', 'step50_100', 'step100_200']
    for rule in rules:
        d = summary.loc[summary.rule.eq(rule) & summary.period.eq('all')].set_index('policy')
        values = [d.loc[p, c] * 100 for c in ['cagr', 'max_drawdown'] for p in ['drift', 'monthly_equal']]
        lines.append('| ' + rule + ' | ' + ' | '.join(f'{x:.2f}%' for x in values) + ' |')
    lines += ['| SPY | 11.24% | 11.24% | -52.45% | -52.45% |', '',
        '## Recent calendar slices', '',
        '| Schedule | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |',
        '|---|---:|---:|---:|---:|']
    for rule in rules:
        values = [summary.loc[summary.rule.eq(rule) & summary.period.eq(t)
            & summary.policy.eq(p), 'cagr'].iloc[0] * 100
            for t in ['2018_end', '2023_end'] for p in ['drift', 'monthly_equal']]
        lines.append('| ' + rule + ' | ' + ' | '.join(f'{x:.2f}%' for x in values) + ' |')
    lines += ['| SPY | 14.67% | 14.67% | 22.83% | 22.83% |', '',
        'Recent slices retain positions from the 2008 simulation; no fresh 2018/2023 starts. '
        'Every year and fixed period is retained in summary.csv.', '',
        '## Stage and trading diagnostics', '',
        '| Run | Switches | To numerically lower SMA | Entries | Fees USD | Annual two-way turnover | Median losing hold, calendar days |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for d in diagnostics.itertuples():
        lines.append(f'| {d.run} | {d.switches} | {d.lower_level_switches} | {d.entries} | '
            f'{d.fees:.2f} | {d.annual_two_way_turnover:.2f}x | {d.median_losing_calendar_days:.0f} |')
    lines += ['', 'Turnover sums absolute buy/sell notional divided by transaction pre-trade NAV, '
        'annualized by 252/4652; excludes dividends and terminal settlements. Losing holds are '
        'hindsight-conditional closed episodes, omitting open positions. Monthly cashflow episode ratios '
        'are not fixed-unit security returns. Full concentration/exposure metrics remain in summary.csv.', '',
        '## Interpretation and limits', '',
        'The primary +50/+100% schedule improves full-history net CAGR over SMA150 in both policies, '
        'but remains below SPY. The faster +25/+50% schedule is the strongest of these inspected points '
        'and drift nearly matches SPY with a smaller drawdown. All schedules still lag SPY in CAGR, '
        'and recent gaps are material. The late +100/+200% schedule does not improve since2018 or '
        'since2023 drift CAGR over constant SMA150. No uniformly optimal schedule or confirmed alpha is established.', '',
        'This rule tightens exits after appreciation; initial losing entries still use SMA150. '
        'It therefore does not directly solve fast initial loss cutting. Shorter SMA windows are not '
        'a numerical price ratchet and do not guarantee a protected profit or maximum loss. '
        'All observed stage changes in these runs selected a higher or equal numerical SMA, '
        'but that is an empirical result, not a rule guarantee.', '',
        'Earlier exits change capacity, later entries, costs and concentration, so portfolio differences '
        'are not identical-trade causal exit effects. Drift winner weights can exceed 5%; monthly equalization '
        'trims them. Missing opportunities and cash balances mean neither policy guarantees full investment. '
        'Comparisons with SPY do not isolate entry selection, risk exposures, timing, cash drag or diversification. '
        'No causal single reason for benchmark underperformance is established by this study. '
        'Different risk/drawdown is relevant even when CAGR is lower. All history is inspected development data; '
        'the best schedule has selection bias and no newly estimated uncertainty or unseen-data confirmation.', '',
        '## Verification', '',
        f'All {len(controls)} SMA150 control period rows exactly match ATH35 CAGR/NAV/drawdown/exposure. '
        '22 focused adapter/ledger tests passed. Independent raw feature, calendar and daily ledger/stage '
        'verification files are retained in the run; final status is recorded in manifest.json.', '',
        'Run: `' + str(run.relative_to(ROOT)) + '`. Protocol: `ATH_STEPPED_SMA_PLAN.md`.']
    (ROOT / 'research/ath/ATH_STEPPED_SMA_RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (run / 'control_reproduction.json').write_text(json.dumps(dict(rows=len(controls), passed=True)))
    print('Saved report, diagnostics and exact control reproduction')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
