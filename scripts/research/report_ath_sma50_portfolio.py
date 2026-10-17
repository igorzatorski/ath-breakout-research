"""Generate the English ATH28 result note and bounded inline chart payloads."""
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
VIS = Path('C:/Users/zrogi/.codex/visualizations/2026/10/15/01a1413b-a041-7851-a657-39b90b6c77d1')


def main(path):
    path = Path(path)
    s = pd.read_csv(path/'summary.csv')
    report = ['# First ATH portfolio: SMA50 exit and two weighting policies', '',
        'Exploratory development-history backtest completed 2026-10-17. Both fixed versions underperform SPY over the full history and since 2010; neither establishes a useful net edge. Monthly equal weighting improves this inspected result slightly, but drawdowns remain worse than SPY. This does not isolate the causal benefit of SMA50 versus another exit.', '',
        '## Frozen implementation', '',
        '1994-01-03 to 2026-06-30, 8,177 sessions; USD100,000 initial cash. All25,250 pre-outcome ATH + market6-1/top20 candidates from ATH27; no annual-outcome availability mask. Fresh next-session-open signals only, ordered by saved momentum/volume score. Up to20 distinct companies, target5% of opening wealth at entry. Close below SMA50 triggers next observed open sale. No holding cap, take-profit or rank-drop exit. No extra consolidation, industry or other filter stack.', '',
        'Drift leaves existing quantities unchanged. Monthly equal resets every current holding to5% of post-cost opening wealth after month-end; it does not force monthly replacement. Fewer20 eligible holdings leave cash. Cash earns0%; dividends are cash, not automatically reinvested in the issuer. Fractional shares, no leverage/tax. Primary costs10bps per buy/sell, with0bps gross reference. SPY is total-return buy-and-hold from the first opening, with the same one-time entry fee. Final holdings are marked, not forcibly sold.', '',
        '## Full-history results', '',
        '| Version | CAGR | SPY CAGR | CAGR gap (pp) | Maximum drawdown | Average invested | Final USD |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in s.loc[s.period.eq('all')].itertuples():
        report.append(f'| {r.run} | {r.cagr:.2%} | {r.spy_cagr:.2%} | {100*r.cagr_gap:+.2f} | {r.max_drawdown:.2%} | {r.average_exposure:.2%} | {r.final_nav:,.0f} |')
    report += ['', 'SPY maximum drawdown is55.19%; net final wealth is USD2,845,973. CAGR uses252 sessions per year. These are compounded portfolio returns, not the earlier arithmetic mean annual event returns or CAPM alpha.', '',
        '## Calendar subperiods, 10bps', '',
        '| Period | Drift CAGR | Monthly equal CAGR | SPY CAGR |', '| --- | ---: | ---: | ---: |']
    for period in ['1994_2009', '2010_2017', '2018_end', '2018_2020', '2021_2022', '2023_end']:
        a = s.loc[s.period.eq(period) & s.run.eq('drift_10bps')].iloc[0]
        b = s.loc[s.period.eq(period) & s.run.eq('monthly_equal_10bps')].iloc[0]
        report.append(f'| {period} | {a.cagr:.2%} | {b.cagr:.2%} | {a.spy_cagr:.2%} |')
    report += ['', 'These are actual continuing portfolio calendar returns, not portfolios restarted in each subperiod. The recent window ends2026-06-30. All annual rows are retained in summary.csv.', '',
        '## Exposure, costs and trade distribution', '',
        '| Diagnostic, net | Drift | Monthly equal |', '| --- | ---: | ---: |']
    diagnostics = []
    for name in ['drift_10bps', 'monthly_equal_10bps']:
        d = path/name
        e = pd.read_csv(d/'equity.csv')
        c = pd.read_csv(d/'closed_positions.csv', parse_dates=['entry_date', 'exit_date'])
        audit = json.loads((d/'accounting_audit.json').read_text())
        loss = c.pnl.lt(0)
        diagnostics.append([f'{e.positions.mean():.2f}', f'{e.exposure.ge(.95).mean():.2%}',
            f'{e.positions.eq(20).mean():.2%}', f'{audit["fees"]:,.0f}', str(len(c)),
            f'{loss.mean():.2%}', f'{c.cashflow_profit_ratio.median():.2%}',
            f'{c.loc[loss,"cashflow_profit_ratio"].mean():.2%}', f'{c.loc[~loss,"cashflow_profit_ratio"].mean():.2%}',
            f'{(c.exit_date-c.entry_date).dt.days.median():.0f}',
            f'{s.loc[s.run.eq(name)&s.period.eq("all"),"maximum_weight"].iloc[0]:.2%}'])
    labels = ['Average names', 'Days at least95% invested', 'Days with20 names', 'Total nominal fees USD',
        'Closed position episodes', 'Closed episodes losing money', 'Median episode cashflow profit ratio',
        'Mean losing episode cashflow ratio', 'Mean non-losing episode cashflow ratio', 'Median calendar holding days', 'Largest daily single-name weight']
    report += [f'| {label} | {a} | {b} |' for label, a, b in zip(labels, *diagnostics)]
    report += ['', 'The desired near100% exposure was not consistently reached under fresh-signal rules. This is an implementation consequence, not a tested market-allocation filter. Do not attribute all underperformance to cash: equity selection, exit timing, weighting and costs are jointly present; no cash-matched counterfactual was run.', '',
        'A right tail exists, but frequent small losses do not by themselves guarantee an attractive portfolio. Episode ratios include all purchases, sales and dividends; with monthly additions/trims they are cashflow profit ratios, not time-weighted stock returns. Open episodes are excluded from this closed-trade table. Observed average losing episodes are about9%, so SMA50 is not a hard5% loss cap. Monthly trimming reduces concentration but also sells parts of winners.', '',
        '## Accounting and verification', '',
        'Seven focused tests passed: next-open gap exits, no same-day signal use, ex-date entitlement, once-only terminal settlement, monthly fees/target conservation, company uniqueness, deferred exits, missing-price reconciliation, split consistency and simultaneous split/dividend example. Ruff passed.', '',
        'Independent transaction replay checks cash, shares, prices, fees, source-signal identity, next-session entry timing, SMA decision and deferred-exit timing, daily company/capacity constraints, holdings NAV, full CAGR and drawdown. Raw CRSP reconstruction checks16,174,106 close/SMA cells. See independent_verification.json and raw_panel_verification.json.', '',
        'Each variant has4 carried stale-close position-days,5 deferred exit-days and4 return comparisons skipped because the previous source close is missing. There are31 unique held security-days with unavailable SMA50; no new SMA decision is possible then. All ending holdings have observed prices. Monthly policies have9 deferred-rebalance days. Valid matched regular-return checks total119,895 drift /120,407 monthly, maximum error below0.000001. These price/SMA gaps are retained, not silently excluded.', '',
        'Technical amendments during blocked runs: terminal nonordinary cash is settled through the CIZ Y return once; source-return checks require matching observed previous-close endpoints; CIZ dividends on simultaneous split dates use the pre-event share basis (current cumulative factor times period price factor). Strategy parameters were unchanged. Earlier incomplete directories are failed technical attempts, not candidate strategy results.', '',
        'Terminal returns already include delisting effects; no second delisting return is applied. Normal cash-ledger distributions are not also compounded via total_return. Splits preserve adjusted economic units. This remains a simplified model: ex-date cash availability rather than payment dates, a fixed proportional execution cost rather than market impact, possible stale quotes and historical-source revisions. No live trading or WRDS connection was needed.', '',
        '## Decision and next experiment', '',
        'Keep this as the first reproducible portfolio reference, not an adopted live strategy. Do not optimize SMA length, rebalance frequency or filter combinations from these outcomes. First diagnose the already saved trade paths: how many winners were sold on a temporary SMA50 break, how much subsequent recovery occurred, and whether large losses were gap-driven or slow exits. Use fixed252-session post-entry paths for descriptive comparison, explicitly conditional on observed exits; that will not itself prove a better executable strategy. A later rule change needs its own frozen comparator and cost/exposure controls.', '',
        'All inspected history is development data. No untouched holdout, risk-adjusted alpha or statistical superiority of one weighting rule has been established.', '',
        '## Reproduce', '',
        '```powershell', '.venv/Scripts/python.exe scripts/research/backtest_ath_sma50_portfolio.py',
        f'.venv/Scripts/python.exe scripts/research/verify_ath_sma50_portfolio.py {path.as_posix()}',
        f'.venv/Scripts/python.exe scripts/research/verify_ath_sma50_panels.py {path.as_posix()}', '```', '',
        f'Run: `{path.as_posix()}`. Protocol: `research/ath/ATH_SMA50_PORTFOLIO_PLAN.md`. Daily equity, holdings, closed/open cashflows, transactions, skipped reasons, summaries and hashes are retained.']
    (ROOT/'research/ath/ATH_SMA50_PORTFOLIO_RESULTS.md').write_text('\n'.join(report)+'\n', encoding='utf-8')
    rows = []
    for name, label in [('drift_10bps', 'ATH SMA50 drift, net'), ('monthly_equal_10bps', 'ATH SMA50 monthly equal, net')]:
        e = pd.read_csv(path/name/'equity.csv', parse_dates=['date']).set_index('date')
        monthly = e.resample('ME').last()
        for date, r in monthly.iterrows():
            actual = min(date, e.index[-1])
            rows.append(dict(date=actual.strftime('%Y-%m-%d'), strategy=label, nav=round(r.nav, 2)))
            if name == 'drift_10bps':
                rows.append(dict(date=actual.strftime('%Y-%m-%d'), strategy='SPY total return, net', nav=round(r.spy_nav, 2)))
    source = dict(label='ATH28 frozen local CRSP/SPY backtest', files=[{'label': 'ATH28 equity.csv and summary.csv'}, {'label': 'ATH_SMA50_PORTFOLIO_RESULTS.md'}],
        metricDefinitions=[{'label': 'Portfolio value', 'definition': 'Closing wealth from USD100,000;10bps per buy/sell; dividends in cash for strategy and reinvested for SPY.'}],
        filters=['Fresh ATH +6-1/top20 signals ranked by momentum/volume', 'Maximum20 distinct companies;5% target per entry', 'Close below SMA50 sold at next observed opening'],
        caveats=['Monthly endpoints are displayed; drawdowns and statistics use all8177 daily sessions.', 'Cash earns0%; actual average exposure is about74-75%.', 'All history is inspected development data; no confirmed alpha.'])
    payload = dict(schemaVersion=1, id='ath-sma50-portfolio', queryId='ath28-ledger', title='First ATH portfolio versus SPY, after costs',
        description='USD100,000 initial wealth; monthly closing observations,1994-01 to2026-06.',
        chart=dict(type='line', x='date', y='nav', series='strategy', showXAxisLabel=False, yLabel='Portfolio value (USD)'), rows=rows, source=source, theme='codex-classic')
    (VIS/'ath-sma50-portfolio.json').write_text(json.dumps(payload, allow_nan=False), encoding='utf-8')
    preview = s.loc[s.period.isin(['all', '2010_2017', '2018_end', '2023_end']) & s.run.str.endswith('10bps'),
        ['run', 'period', 'cagr', 'spy_cagr', 'max_drawdown', 'average_exposure']].to_dict('records')
    receipt = dict(schemaVersion=1, items=[dict(id='ath28-results', title='ATH SMA50 first portfolio backtest', queries=[dict(id='ath28-ledger', source=source,
        reportingPeriod='1994-01-03 to2026-06-30', columns=list(preview[0]), rows=preview,
        preview=dict(kind='aggregate', note='Full and selected calendar subperiod summaries; all annual rows remain in the saved study.'),
        methods=[dict(language='calculation', code='CAGR = (ending wealth / starting wealth)^(252 / sessions) - 1; maximum drawdown uses every daily close including initial capital.')])])])
    (VIS/'ath-sma50-sources.json').write_text(json.dumps(receipt, allow_nan=False), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1])
