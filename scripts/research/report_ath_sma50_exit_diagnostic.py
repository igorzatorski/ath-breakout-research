"""Write English ATH29 evidence and bounded inline chart inputs."""
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
VIS = Path('C:/Users/zrogi/.codex/visualizations/2026/10/15/01a1413b-a041-7851-a657-39b90b6c77d1')


def main(path):
    path = Path(path)
    events = pd.read_parquet(path/'exit_events.parquet')
    s = pd.read_csv(path/'paired_summary.csv')
    losses = pd.read_csv(path/'loss_decomposition.csv')
    q = events.loc[events.policy.eq('drift_10bps')&events.paired_status.eq('complete')]
    quantiles = q[['sale_return','hold_return']].quantile([.01,.05,.5,.95,.99])
    quantiles.to_csv(path/'primary_quantiles.csv',index_label='quantile')
    primary = s.loc[s.policy.eq('drift_10bps')&s.period.eq('all')].iloc[0]
    large = events.loc[events.policy.eq('drift_10bps')&events.actual_profit_ratio.le(-.2)]
    gaps = large.dropna(subset=['all_holding_gap_return'])
    lines = ['# ATH29: what the SMA50 exits cut', '',
        'SMA50 truncated both tails in this inspected sample: it prevented many much larger eventual losses, but also sold many stocks that subsequently recovered or became large winners. The remaining execution gap after the sale decision explains only a small share of realized losses. This is a descriptive trade-path study, not a new portfolio backtest or proof of a better exit.', '',
        '## Scope and comparison', '',
        'ATH28 signals and portfolio rules are unchanged. Analyze both10bps policies, with drift primary. Every SMA50 sale is decomposed using actual ledger cashflows. For the paired path study, compare one original share-equivalent sold at its actual SMA50 opening then held in cash versus the same unit kept until session252 from entry (entry counts as1). Both pay10bps entry/exit cost; dividends remain cash; terminal CIZ proceeds settle once with no second fee. Endpoint is fixed from entry, not252 days after exit. Results are episode returns, not CAGR.', '',
        'Primary:3,100 SMA50 exits;2,982 complete paired paths. Exclude103 immature horizons and15 paths with missing observations, with no outcome-based exclusion. Monthly:3,111 exits;2,993 complete pairs, also103 immature and15 missing. No SMA sale occurs at or beyond the252nd session in these saved episodes. The123 terminal exits in each original portfolio and still-open positions are outside this SMA-exit-conditioned cohort. Future terminal events after an SMA sale are retained in hypothetical holding paths,147 in the primary complete cohort.', '',
        '## Same episodes, same endpoint', '',
        '| Metric | SMA50 sale then cash | Hold to session252 |', '| --- | ---: | ---: |',
        f'| Mean return | {q.sale_return.mean():.2%} | {q.hold_return.mean():.2%} |',
        f'| Median return | {q.sale_return.median():.2%} | {q.hold_return.median():.2%} |',
        f'| Loss of at least20% | {q.sale_return.le(-.2).mean():.2%} | {q.hold_return.le(-.2).mean():.2%} |',
        f'| Loss of at least50% | {q.sale_return.le(-.5).mean():.2%} | {q.hold_return.le(-.5).mean():.2%} |',
        f'| 5th percentile | {quantiles.loc[.05,"sale_return"]:.2%} | {quantiles.loc[.05,"hold_return"]:.2%} |',
        f'| 95th percentile | {quantiles.loc[.95,"sale_return"]:.2%} | {quantiles.loc[.95,"hold_return"]:.2%} |', '',
        f'Keeping the unit finishes ahead in{primary.hold_ahead_frequency:.2%} of pairs; mean paired advantage{100*primary.mean_hold_minus_sale:.2f} pp, median{100*primary.median_hold_minus_sale:.2f} pp. Of{int(primary.losing_sales):,} losing standardized sales,{int(primary.losing_sale_then_positive_endpoint):,} ({primary.losing_sale_recovery_frequency:.2%}) become positive by the fixed endpoint.', '',
        f'{int(primary.final_doublers)} episodes finish at least+100% if held; their average sale return is{primary.final_doubler_sale_return_mean:.2%}. Excluding those final doublers reduces the mean hold-minus-sale difference to{100*primary.hold_advantage_without_doublers:.2f} pp. This is a hindsight-conditional concentration diagnostic, not a permissible exclusion or signal. A post-sale closing-price maximum at least10% above the fill occurs in{primary.subsequent_10pct_price_rebound:.2%}; the maximum cannot be earned without a future-aware exit.', '',
        '## Mean paired hold-minus-sale difference by entry cohort', '',
        '| Entry cohort | Drift pairs | Drift difference (pp) | Monthly pairs | Monthly difference (pp) |', '| --- | ---: | ---: | ---: | ---: |']
    for period in ['1994_2009','2010_2017','2018_end','2023_end']:
        a = s.loc[s.policy.eq('drift_10bps')&s.period.eq(period)].iloc[0]
        b = s.loc[s.policy.eq('monthly_equal_10bps')&s.period.eq(period)].iloc[0]
        lines.append(f'| {period} | {int(a.complete_pairs)} | {100*a.mean_hold_minus_sale:.2f} | {int(b.complete_pairs)} | {100*b.mean_hold_minus_sale:.2f} |')
    lines += ['', 'Recent entry cohorts are restricted by annual maturity through2026-06-30. The same company can appear repeatedly and holdings overlap; no independent-observation confidence interval or statistical/causal superiority is claimed. Monthly comparisons are standardized original units and do not reproduce the rebalanced cashflow return.', '',
        '## Were large losses caused by the final execution gap?', '',
        '| Policy / loss group | Episodes | Mean realized ratio | Loss already present before execution | Execution movement share of dollar losses | Exit-fee share |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in losses.itertuples():
        lines.append(f'| {r.policy} / {r.group} | {r.count} | {r.mean_profit_ratio:.2%} | {r.pre_execution_loss_usd/r.total_loss_usd:.2%} | {r.execution_movement_share:.2%} | {r.exit_fees_usd/r.total_loss_usd:.2%} |')
    lines += ['', 'The components reconcile exactly to actual episode PnL, including prior rebalance flows and entitled dividends. Execution movement is decision close to actual fill; deferred fills may span several sessions. Dollar shares are net signed contributions, so favorable movements offset adverse ones. They do not claim every losing trade had an adverse gap.', '',
        f'Large drift losses mean actual episode loss at least20%:137 episodes, average realized ratio-27.86%, with average entry-to-decision price return-26.20%. All-holding gap decomposition has complete prices for{len(gaps)} of137 episodes. Their average additive entry-price contribution is{100*gaps.all_holding_gap_return.mean():.2f} pp from all overnight moves and{100*gaps.all_holding_intraday_return.mean():.2f} pp from intraday moves. {int(gaps.worst_overnight_gap.le(-.2).sum())}/{len(gaps)} experienced at least one overnight gap of-20% or worse. These are additive price contributions, not compounded gap-only investment returns, and differ from net cashflow returns.', '',
        'Thus the final sale gap is not the dominant accounting source of these losses. SMA50 can lie far below a rapidly rising entry price, so a first close below it can already mean a severe entry loss. Earlier overnight gaps also matter in some cases; the analysis does not establish that every loss was slow or avoidable.', '',
        '## Examples, primary actual large dollar losses', '',
        '| Ticker at entry | Entry | Sale | Realized return | Entry-to-decision price return | Decision-to-fill movement |', '| --- | --- | --- | ---: | ---: | ---: |']
    for r in large.nsmallest(5,'actual_pnl').itertuples():
        lines.append(f'| {r.ticker} | {r.entry_date.date()} | {r.exit_date.date()} | {r.actual_profit_ratio:.2%} | {r.price_return_at_decision:.2%} | {r.execution_window_return:.2%} |')
    lines += ['', '## Interpretation and next step', '',
        'The intended asymmetry is not delivered automatically by one moving average. SMA50 gives meaningful left-tail protection versus keeping the selected stocks for a year, while truncating part of the right tail; for some entries it still permits very large losses. Those are three distinct observations, not evidence to abandon all stops or select a longer SMA after seeing results.', '',
        'A possible next separately frozen hypothesis is to distinguish initial loss control from the rule used to follow an established winner. Do not implement that from this report alone or select thresholds from the largest historical winners. First agree on one simple pair of rules and a fixed portfolio comparator; retain capacity, reinvestment, ranking, costs and exposure controls.', '',
        'The same-unit comparison holds sale proceeds idle; the actual portfolio may redeploy them, and a hold-to252 portfolio would occupy slots and block other entries. Repeated episodes may overlap in the same company. The measured15.18 pp mean difference cannot be added to portfolio CAGR, interpreted as alpha, or used to claim a buy-and-hold portfolio wins. Equal episode weighting differs from actual capital weights. The paired sample is selected by the original exit rule and is not an independent holdout. Missing-price exclusions may affect comparisons. SPY was not newly retested here: ATH28 remains the portfolio-level benchmark evidence.', '',
        '## Verification and files', '',
        'Four focused synthetic tests passed, including ex-date entitlement, terminal-once treatment, invalid paths and all-holding gap versus last-gap decomposition. Actual PnL reconciled for all6,211 SMA exits across the two policies, maximum error below USD0.000001. Primary standardized sale returns match actual drift episode returns to1.4e-15. Independent raw CRSP reconstruction of79 paths, including terminal cases, has zero return discrepancy. All10 aggregate rows were independently checked. Further602,894 distinct regular source-return checks across primary forward paths reconcile adjusted prices/distributions to CIZ within0.000001; no unexplained error. Source hashes verified for38 inputs; Ruff passed.', '',
        f'Run: `{path.as_posix()}`. Saved event-level paths, both-policy summaries, coverage, quantiles, loss decomposition, top20 losses, independent checks and manifest. Source ATH28 is unchanged. Reproduce with `scripts/research/diagnose_ath_sma50_exits.py`, then `verify_ath_sma50_exit_diagnostic.py RUN` and `report_ath_sma50_exit_diagnostic.py RUN`.']
    (ROOT/'research/ath/ATH_SMA50_EXIT_DIAGNOSTIC_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    rows = [dict(percentile=f'P{int(v*100):02d}',rule=label,return_percent=round(100*quantiles.loc[v,col],3))
        for v in quantiles.index for col,label in [('sale_return','SMA50 sale, then cash'),('hold_return','Hold original unit to session252')]]
    source = dict(label='ATH29 fixed-unit exit diagnosis',files=[{'label':'ATH29 exit_events.parquet'},{'label':'ATH_SMA50_EXIT_DIAGNOSTIC_RESULTS.md'}],
        metricDefinitions=[{'label':'Episode return','definition':'Net return on one original unit over252 sessions from entry; SMA50 proceeds remain cash after sale;10bps entry/exit costs.'}],
        filters=['Drift policy SMA50 exits','2982 complete mature paired paths','Entry cohorts1994-2025 with endpoint by2026-06-30'],
        caveats=['Exit-conditioned descriptive sample; not executable portfolio CAGR or alpha.','Repeated and overlapping episodes are not independent.','103 immature and15 missing paths excluded; terminal exits and still-open source positions are outside this cohort.'])
    chart = dict(schemaVersion=1,id='ath-sma50-exit-tails',title='SMA50 cuts both tails',description='Return percentiles on the same2982 original-unit paths;10bps costs.',
        chart=dict(type='bar',x='percentile',y='return_percent',series='rule',xLabel='Episode return percentile',yLabel='Net episode return (%)'),rows=rows,source=source,theme='codex-classic')
    (VIS/'ath-sma50-exit-tails.json').write_text(json.dumps(chart,allow_nan=False),encoding='utf-8')
    receipt = dict(schemaVersion=1,items=[dict(id='ath29-diagnosis',title='SMA50 tail protection, foregone recoveries and realized loss decomposition',queries=[dict(id='ath29-pairs',source=source,
        reportingPeriod='Entry history1994 through mature2025 cohorts; endpoints no later than2026-06-30',columns=list(rows[0]),rows=rows,
        preview=dict(kind='aggregate',note='Selected primary empirical return quantiles; no confidence bounds.'),
        methods=[dict(language='calculation',code='Paired difference = hold-unit net return at entry session252 minus actual SMA50 sale-unit net return with proceeds in zero-interest cash. Actual PnL = pre-execution PnL + remaining quantity*(fill - decision close) - exit fee.')])])])
    summary_rows = s.loc[s.policy.eq('drift_10bps')].to_dict('records')
    receipt['items'][0]['queries'].append(dict(id='ath29-summary',source=source,
        reportingPeriod='1994 onward, mature fixed252-session entry cohorts through2026-06-30',
        columns=list(summary_rows[0]),rows=summary_rows,preview=dict(kind='aggregate',note='Primary paired path means and recovery frequencies by entry cohort.')))
    loss_source = dict(label='ATH29 actual SMA50 sale ledger',files=[{'label':'loss_decomposition.csv'}],
        metricDefinitions=[{'label':'Execution movement share','definition':'Net dollar movement from SMA decision close to fill divided by actual dollar losses within the stated losing-episode group.'}],
        filters=['Actual SMA50 exits in both10bps policies','Large losses defined by actual episode cashflow ratio at most-20%'],
        caveats=['All losses includes small losses; the large-loss group is a subset.','This final decision-to-fill movement excludes earlier overnight gaps.'])
    loss_rows = losses.to_dict('records')
    receipt['items'][0]['queries'].append(dict(id='ath29-loss-decomposition',source=loss_source,
        reportingPeriod='Actual source exits1994-01 to2026-06',columns=list(loss_rows[0]),rows=loss_rows,
        preview=dict(kind='aggregate',note='Exact actual-dollar reconciliation by policy and losing-episode group.')))
    (VIS/'ath-sma50-exit-sources.json').write_text(json.dumps(receipt,allow_nan=False),encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1])
