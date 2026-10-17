"""English ATH30 results, risk/concentration evidence and bounded inline inputs."""
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
VIS = Path('C:/Users/zrogi/.codex/visualizations/2026/10/15/01a1413b-a041-7851-a657-39b90b6c77d1')
LABELS = {'sma50':'SMA50 baseline','floor5_sma50':'Entry floor5% + SMA50',
    'sma200':'SMA200 control','floor5_sma200':'Entry floor5% + SMA200 candidate'}


def main(path):
    path = Path(path)
    s = pd.read_csv(path/'summary.csv')
    full = s.loc[s.period.eq('all')&s.cost_bps.eq(10)]
    lines = ['# ATH30: original-entry risk floor and longer trend following', '',
        'The fixed5% entry-floor plus SMA200 candidate improves on SMA50 in both weighting policies, but only slightly exceeds full-history SPY and still underperforms SPY since2018. The attribution controls are informative: extending the trend leg to200 sessions is favorable over the full inspected history; adding the5% floor reduces full-history CAGR at either SMA. No optimal exit or current alpha is established.', '',
        '## Frozen design', '',
        'Same25,250 pre-outcome ATH +6-1/top20 signals and MV priority as ATH28,1994-01-03 to2026-06-30,8,177 sessions, USD100,000 initial cash, maximum20 companies,5% entry target. Fresh next-opening signals only. Exits free slots, so actual executed entries and reinvestment change endogenously; source signals and candidate ranking are unchanged.', '',
        'Candidate: close strictly below95% of the original opening purchase price OR below arithmetic SMA200 including the current close; sell at the next observed opening. The floor stays fixed through monthly rebalances and is price-based, not dividend-adjusted or trailing. Both legs remain active throughout; no profit activation threshold. With missing SMA200 the trend leg is suspended and the floor remains active. No forced signal exclusion. This close-triggered floor is not an intraday stop and cannot cap execution losses at5%.', '',
        'Exactly four exit definitions were registered before results: SMA50, floor+SMA50, SMA200 and floor+SMA200. Both existing weighting policies at10bps per buy/sell. Candidate-only0bps is a gross reference. No threshold/SMA search. Monthly equal resets held weights to5% without replacing securities; drift retains quantities. Cash yield0%, fractional shares, no leverage/taxes. SPY total-return buy-and-hold receives the same initial entry fee. Holdings remain marked at the end.', '',
        '## Full-history net results', '',
        '| Exit | Drift CAGR | Monthly equal CAGR | Drift max drawdown | Monthly max drawdown |', '| --- | ---: | ---: | ---: | ---: |']
    for rule in LABELS:
        a = full.loc[full.rule.eq(rule)&full.policy.eq('drift')].iloc[0]
        b = full.loc[full.rule.eq(rule)&full.policy.eq('monthly_equal')].iloc[0]
        lines.append(f'| {LABELS[rule]} | {a.cagr:.2%} | {b.cagr:.2%} | {a.max_drawdown:.2%} | {b.max_drawdown:.2%} |')
    lines += ['| SPY | 10.87% | 10.87% | -55.19% | -55.19% |', '',
        'The candidate exceeds SMA50 by3.67 pp drift /2.54 pp monthly in CAGR, but its SPY gap is only+0.76/+0.15 pp. The candidate drift drawdown is worse than the original SMA50 drawdown; adding a trade-level floor does not guarantee a smaller portfolio drawdown.', '',
        'Gross candidate CAGR is12.26% drift /11.79% monthly. Net candidate final wealth is approximately USD3.55m /2.97m versus SPY USD2.85m. CAGR annualizes252 sessions and is not a mean episode return.', '',
        '## Calendar portfolio periods, net', '',
        '| Period | Weight policy | SMA50 | Floor + SMA50 | SMA200 | Floor + SMA200 | SPY |', '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for period in ['1994_2009','2010_2017','2018_end','2018_2020','2021_2022','2023_end']:
        for policy in ['drift','monthly_equal']:
            q = s.loc[s.period.eq(period)&s.policy.eq(policy)&s.cost_bps.eq(10)].set_index('rule')
            vals = ' | '.join(f'{q.loc[rule,"cagr"]:.2%}' for rule in LABELS)
            lines.append(f'| {period} | {policy} | {vals} | {q.spy_cagr.iloc[0]:.2%} |')
    lines += ['', 'These are continuing portfolio calendar returns, not restarts and not forward signal-cohort means. All inspected dates are development history. Since2018 the candidate returns8.40%/6.14% against14.67% SPY. Since2023 the candidate returns20.22%/16.12% against22.83% SPY. The unconstrained SMA200 control also lags SPY in both these recent windows.', '',
        '## Trade risk, exposure and concentration', '',
        '| Exit / weighting | Mean invested | Largest daily name weight | Closed losing episodes | Mean losing cashflow ratio | Median holding calendar days | Top5 company share of net dollar PnL |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    diagnostics = []
    for r in full.itertuples():
        d = path/r.run
        c = pd.read_csv(d/'closed_positions.csv',parse_dates=['entry_date','exit_date'])
        o = pd.read_csv(d/'open_positions.csv')
        combined = pd.concat([c[['permco','ticker','pnl']],o.rename(columns={'unrealized_total_pnl':'pnl'})[['permco','ticker','pnl']]])
        companies = combined.groupby('permco').agg(ticker=('ticker','last'),pnl=('pnl','sum')).sort_values('pnl',ascending=False)
        companies.to_csv(d/'company_pnl.csv')
        loss = c.pnl.lt(0)
        top5 = companies.head(5).pnl.sum()/companies.pnl.sum()
        median_days = (c.exit_date-c.entry_date).dt.days.median()
        diagnostics.append(dict(run=r.run,rule=r.rule,policy=r.policy,closed_positions=len(c),
            loss_frequency=loss.mean(),mean_loss_ratio=c.loc[loss,'cashflow_profit_ratio'].mean(),
            median_holding_days=median_days,top5_company_share_net_pnl=top5))
        lines.append(f'| {LABELS[r.rule]} / {r.policy} | {r.average_exposure:.2%} | {r.maximum_weight:.2%} | {loss.mean():.2%} | {c.loc[loss,"cashflow_profit_ratio"].mean():.2%} | {median_days:.0f} | {top5:.2%} |')
    pd.DataFrame(diagnostics).to_csv(path/'trade_concentration_summary.csv',index=False)
    lines += ['', 'Closed ratios include buys, sales, fees and dividends. Under monthly rebalancing they are cashflow ratios rather than time-weighted stock returns. Ending-open holdings contribute to company PnL but not closed-loss statistics; all values are nominal dollars. A high top-company share is a concentration diagnostic, not a reason to remove those companies after seeing results.', '',
        'Candidate drift loses on roughly79% of closed episodes, with average loser about-7.55%; a5% close threshold is not a5% realized-loss guarantee. The floor reduces average loser size versus SMA200 alone but sells many more episodes at losses. Candidate drift can allocate over43% of current wealth to one winner despite its5% entry target; SMA200 alone reaches49%. Monthly resets limit these observed maxima to about10%. Full-period SMA200 lead therefore is not a clean equal-risk comparison to SPY.', '',
        '## What the controls establish and what they do not', '',
        'At either SMA, the fixed5% floor lowers full-history net CAGR. At either floor setting, SMA200 improves full-history CAGR over SMA50. These are fixed system-level comparisons with different holding durations, exposure, vacancies, costs and executed entries, not an isolated causal stock-level exit treatment. Recent outcomes vary; the floor is not uniformly harmful in every subperiod.', '',
        'Do not select SMA200 as an optimum from this experiment. Keep it as an exploratory longer-trend reference. A next controlled diagnostic should compare exposure/risk and concentration, then risk-adjusted portfolio returns, before claiming an entry or exit alpha. Current historical recent underperformance and source/missingness limitations remain material. No new filter, portfolio-size or cash-allocation rule was tested.', '',
        '## Validation and data limitations', '',
        'Twelve focused tests passed: five new exit/anchor cases plus seven existing ledger regressions. They cover strict equality, next-open gaps, longer-trend holding, fixed anchor after rebalances, floor with missing SMA, combined triggers, terminal-once behavior and same-open sale/reentry. Both SMA50 controls reproduce the saved daily NAV/cash/count/fees/benchmark and every transaction from ATH28.', '',
        'Independent replay reconstructs every first qualifying exit close and earliest tradable opening, original-entry anchors, pending exits, cash/share/dividend/fee accounting, terminal settlement, source signal timing, daily holdings, company capacity and monthly targets. All ten variants are checked. Raw reconstruction verifies16,174,106 SMA200 cells;400 calendar summaries and ten SPY curves are independently checked. Closed plus ending-open PnL reconciles to final wealth. See baseline_replay.json, independent_verification_*.json and raw_feature_summary_verification.json.', '',
        'The first run was invalidated by an implementation error: a same-open exit/reentry could inherit the old effective floor for that day. Independent first-trigger verification detected it, a regression test was added, and all variants rerun without changing strategy parameters. The invalid directory is retained with failure metadata and is not research evidence.', '',
        'Missing trend, stale-close and deferred-fill cases are preserved and reported per variant below. Missing trend means that trend leg cannot issue a new decision; it does not remove the position. Stale quotes are carried rather than invented executable prices; inspect ending stale status before any live use.', '',
        '| Run | Missing trend position-days | Stale close position-days | Deferred exit-days |', '| --- | ---: | ---: | ---: |']
    for directory in sorted(path.glob('*bps')):
        a = json.loads((directory/'accounting_audit.json').read_text())
        lines.append(f'| {directory.name} | {a["missing_trend_position_days"]} | {a["stale_position_days"]} | {a["deferred_exit_days"]} |')
    lines += ['', 'As in ATH28, dividends are available on ex-date rather than actual payment date, execution costs are fixed proportional estimates rather than impact models, and historical data is current-vintage. Cash receives no interest. No statistical superiority, independent holdout, optimal threshold or confirmed alpha is claimed.', '',
        '## Files and reproduction', '',f'Run: `{path.as_posix()}`.',
        'Protocol: `research/ath/ATH_INITIAL_RISK_TREND_PLAN.md`. Engine extension preserves the original ATH28 engine. Commands: `backtest_ath_initial_risk_trend.py`; `verify_ath_initial_risk_trend.py RUN [RULE]`; `verify_ath_initial_risk_features.py RUN`; `report_ath_initial_risk_trend.py RUN`. Saved summary.csv includes all400 variant/period rows. Full decisions, transactions, daily holdings/equity, company PnL, closed and open cashflows, skipped reasons and source hashes are retained.']
    (ROOT/'research/ath/ATH_INITIAL_RISK_TREND_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    periods = [('all','Full history'),('2010_2017','2010-2017'),('2018_end','2018-Jun2026'),('2023_end','2023-Jun2026')]
    rows = []
    for period,label in periods:
        q = s.loc[s.period.eq(period)&s.policy.eq('drift')&s.cost_bps.eq(10)].set_index('rule')
        for rule in ['sma50','floor5_sma200','sma200']:
            rows.append(dict(period=label,strategy=LABELS[rule],cagr_percent=round(100*q.loc[rule,'cagr'],3)))
        rows.append(dict(period=label,strategy='SPY total return',cagr_percent=round(100*q.spy_cagr.iloc[0],3)))
    source = dict(label='ATH30 frozen portfolio comparison',files=[{'label':'ATH30 summary.csv'},{'label':'ATH_INITIAL_RISK_TREND_RESULTS.md'}],
        metricDefinitions=[{'label':'CAGR','definition':'Compounded portfolio growth annualized at252 sessions;10bps per buy/sell; zero interest on cash.'}],
        filters=['Same fresh ATH +6-1/top20 source candidates and MV ranking','Maximum20 companies with5% entry targets','Chart uses drift weighting and continuing calendar portfolios'],
        caveats=['All inspected history is development data; no confirmed alpha.','Different exit rules change exposure, concentration, vacancies and executed entries.','SMA200 is a fixed attribution control, not an optimized parameter.'])
    chart = dict(schemaVersion=1,id='ath-initial-risk-trend',title='Longer trends help the full history; recent periods still lag SPY',
        description='Net calendar CAGR, drift weights; full history1994-01 through2026-06.',chart=dict(type='bar',x='period',y='cagr_percent',series='strategy',showXAxisLabel=False,yLabel='Portfolio CAGR (%)'),rows=rows,source=source,theme='codex-classic')
    (VIS/'ath-initial-risk-trend.json').write_text(json.dumps(chart,allow_nan=False),encoding='utf-8')
    preview = s.loc[s.period.isin(['all','2018_end','2023_end'])&s.cost_bps.eq(10),
        ['rule','policy','period','cagr','spy_cagr','max_drawdown','average_exposure','maximum_weight']].to_dict('records')
    receipt = dict(schemaVersion=1,items=[dict(id='ath30-results',title='Original-entry floor and trend exit comparison',queries=[dict(id='ath30-summaries',
        source=source,reportingPeriod='1994-01-03 through2026-06-30; selected continuing calendar subperiods',columns=list(preview[0]),rows=preview,
        preview=dict(kind='aggregate',note='Full and recent net summaries for both fixed weighting policies; all400 rows retained in the run.'),
        methods=[dict(language='calculation',code='CAGR=(final NAV / initial subperiod NAV)^(252 / sessions)-1. Floor=.95*original entry opening; close strictly below floor or current SMA triggers next observed opening sale.')])])])
    (VIS/'ath-initial-risk-sources.json').write_text(json.dumps(receipt,allow_nan=False),encoding='utf-8')


if __name__=='__main__':
    main(sys.argv[1])
