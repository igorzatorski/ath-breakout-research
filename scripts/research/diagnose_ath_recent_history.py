"""ATH31: reconcile saved portfolio periods, exposure paths and recent losses."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'outputs/backtests/ath_30_initial_risk_trend_v001/20261017T154917914966Z'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT/f'outputs/research/ath/ath_31_recent_history_diagnostic_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    hashes = {k.replace('\\','/'):v for k,v in manifest['artifacts'].items()}
    inputs = {str((SOURCE/'manifest.json').relative_to(ROOT)):sha(SOURCE/'manifest.json')}
    summaries,annual,contributions = [],[],[]
    for directory in sorted(SOURCE.glob('*_10bps')):
        rule,policy = directory.name.split('__')
        policy = policy.removesuffix('_10bps')
        for name in ['equity.csv','holdings.parquet','transactions.parquet']:
            f = directory/name
            digest = sha(f)
            assert digest==hashes[str(f.relative_to(SOURCE)).replace('\\','/')]
            inputs[str(f.relative_to(ROOT))]=digest
        e = pd.read_csv(directory/'equity.csv',parse_dates=['date'])
        e['lag_exposure'] = e.exposure.shift(1,fill_value=0.)
        for label,mask in [('1994_2009',e.date.dt.year.le(2009)),('2010_2017',e.date.dt.year.between(2010,2017)),
            ('2018_end',e.date.dt.year.ge(2018)),('2021_2022',e.date.dt.year.between(2021,2022)),('2023_end',e.date.dt.year.ge(2023))]:
            f=e.loc[mask]
            r,b=f.daily_return.to_numpy(),f.spy_return.to_numpy()
            matched=f.lag_exposure.to_numpy()*b
            def cagr(x):
                return float(np.expm1(np.log1p(x).mean()*252))
            actual,spy,proxy=cagr(r),cagr(b),cagr(matched)
            total_gap=actual-spy
            exposure_component=proxy-spy
            remaining=actual-proxy
            assert np.isclose(total_gap,exposure_component+remaining)
            summaries.append(dict(rule=rule,policy=policy,period=label,sessions=len(f),cagr=actual,spy_cagr=spy,
                exposure_proxy_cagr=proxy,average_exposure=f.exposure.mean(),cagr_gap=total_gap,
                exposure_comparator_difference=exposure_component,remaining_comparator_difference=remaining))
        for year,f in e.loc[e.date.dt.year.ge(2018)].groupby(e.date.dt.year):
            actual=float(np.expm1(np.log1p(f.daily_return).sum()))
            spy=float(np.expm1(np.log1p(f.spy_return).sum()))
            annual.append(dict(rule=rule,policy=policy,year=int(year),label='2026 H1' if year==2026 else str(year),
                total_return=actual,spy_total_return=spy,excess_pp=100*(actual-spy),sessions=len(f)))
        h=pd.read_parquet(directory/'holdings.parquet')
        t=pd.read_parquet(directory/'transactions.parquet')
        start,end=pd.Timestamp('2021-01-01'),pd.Timestamp('2022-12-31')
        prior,last=e.loc[e.date.lt(start)].iloc[-1],e.loc[e.date.le(end)].iloc[-1]
        v0=h.loc[h.date.eq(prior.date)].groupby('permno').value.sum()
        v1=h.loc[h.date.eq(last.date)].groupby('permno').value.sum()
        flows=t.loc[t.date.between(start,end)].groupby('permno').cash_delta.sum()
        pnl=v1.sub(v0,fill_value=0.).add(flows,fill_value=0.)
        assert np.isclose(pnl.sum(),last.nav-prior.nav,atol=max(1e-5,prior.nav*1e-10))
        labels=t.loc[t.date.le(end)].groupby('permno').ticker.last()
        for sid,value in pnl.items():
            contributions.append(dict(rule=rule,policy=policy,permno=int(sid),ticker=labels.get(sid,''),
                pnl_usd=value,contribution_to_period_total_return=value/prior.nav))
    s=pd.DataFrame(summaries)
    s.to_csv(out/'exposure_period_summary.csv',index=False)
    pd.DataFrame(annual).to_csv(out/'annual_returns.csv',index=False)
    pd.DataFrame(contributions).to_csv(out/'2021_2022_security_pnl.csv',index=False)
    older=ROOT/'research/ath/ATH_PERIOD_DIAGNOSTIC_RESULTS.md'
    inputs[str(older.relative_to(ROOT))]=sha(older)
    lines=['# ATH31: why historical and contemporary results differ','',
        'Primary practical focus is2018 through2026-06-30, with2023 onward as a short recent sensitivity. Earlier periods are context, not evidence that a current edge exists. This diagnosis reads frozen ATH30 outputs; it introduces no strategy, parameter, entry filter, exclusion or new holdout. Known recent history remains development data.','',
        '## What is established','',
        'There are two separate evidence layers: the earlier fixed252-session signal study and the actual capital-constrained portfolio. Their arithmetic event means and calendar CAGRs must not be mixed.','',
        'The saved ATH13 event study reports early1994-2009 stock mean21.57%, matching-window SPY4.46%, excess17.11 pp; recent2018-complete2025 signals stock11.34%, SPY13.58%, excess-2.23 pp. The19.34 pp excess decline reconciles to10.23 pp lower stock mean and9.12 pp stronger SPY (rounding applies). Under the fixed company nonoverlap sensitivity, stock means14.92% versus14.19% barely change and SPY explains most of the difference. Repeated-signal weighting therefore matters. These are inherited documented ATH13 results, not freshly recomputed event estimates here.','',
        'The same earlier study reports1998/1999 cohorts contribute14.65 pp of the early17.11 pp net excess mean. Events beating SPY by more than200 pp fall from4.24% of early events to0.86% recently. This explains much of the arithmetic concentration pattern, not a causal market mechanism. ATH13 uncertainty does not establish structural decay, crowding, sector causation or statistical superiority.','',
        '## Portfolio growth and exposure comparison','',
        'For each saved day create a zero-cost synthetic series r_proxy,t = previous-close strategy exposure * SPY total return,t. Cash earns0%. Apply the actual previous-day exposure path before restricting calendar subperiods. This controls approximately for the pattern of stock/cash exposure, including timing, rather than just average invested capital. It omits intraday entry/exit exposure, rebalancing/impact costs and security differences; it is not an executable backtest or risk-matched/factor-adjusted alpha.','',
        'The arithmetic identity between CAGRs is exact: strategy minus SPY = proxy minus SPY + strategy minus proxy. Its terms are comparisons to a synthetic reference, not independent economic causes or a unique attribution.','',
        '| Period | Rule | Weights | Portfolio CAGR | SPY CAGR | Exposure-path SPY proxy | Mean invested |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for r in s.loc[s.rule.isin(['sma200','floor5_sma200'])&s.period.isin(['2010_2017','2018_end','2021_2022','2023_end'])].itertuples():
        lines.append(f'| {r.period} | {r.rule} | {r.policy} | {r.cagr:.2%} | {r.spy_cagr:.2%} | {r.exposure_proxy_cagr:.2%} | {r.average_exposure:.2%} |')
    lines+=['','Since2018, SMA200 drift returns8.15% versus14.67% SPY and12.30% synthetic exposure-path SPY. Cash/exposure timing therefore does not explain the entire underperformance. The fixed-floor candidate drift returns8.40% versus11.03% proxy, also below its proxy. Since2023, SMA200 drift20.53% is close to20.77% proxy, while the floor candidate20.22% exceeds19.42% proxy. Their remaining gap versus full SPY is much smaller than in the broader modern period. This changes interpretation by period without establishing alpha.','',
        '## The2021-2022 interruption','',
        'In the actual calendar portfolio, SMA200 drift annualized-13.63% and floor+SMA200 drift-17.04%, while SPY annualized+2.64%. These are two-year calendar CAGRs, not the annual forward outcomes of2021 signals. The source portfolios therefore lost money in names/weights/exits that behaved much worse than broad SPY over this interval. Even same-exposure proxies are much better (+1.22% and-2.04%). This is a measurable episode, not proof that a particular sector, economic shock or market microstructure caused it.','',
        'The saved2021_2022_security_pnl.csv reconciles every security contribution to start-to-end portfolio wealth change using ending marked value minus starting value plus intervening trade/dividend cashflows. Labels use only source transactions through2022-end. No future classifications or winner deletion. Nominal dollar contributions are path/capital-weighted and not comparable across strategies as independent stock effects.','',
        '## Interpretation and research priorities','',
        'The supported explanation is a combination: old average signal results depended strongly on rare extreme winners and repeat weighting; contemporary SPY is a stronger comparison; and the capital-constrained strategy suffered a large2021-2022 loss episode. Execution rules, exposure and weighting change the observed portfolio result, with longer SMA200 avoiding some SMA50 truncation but not fixing the broader modern shortfall.','',
        'Economic causes such as more efficient breakout pricing, strategy crowding, sector composition, benchmark concentration or valuation changes remain unestablished. Do not narrate them as findings without an explicitly defined comparison and appropriate historical data.','',
        'Use2018 onward as the principal diagnostic window and2023 onward as a short sensitivity; retain2010-2017 and older history for robustness and context. Do not delete2021/2022 or keep only a favorable recent start date. Before new parameters, compare modern signal opportunity quality, current-portfolio concentration/exposure and risk-factor returns under frozen definitions. Longer history can test robustness; it cannot rescue absent modern performance.','',
        '## Verification and files','',
        f'Run: `{out.relative_to(ROOT).as_posix()}`. Hash-checked24 source files from eight net variants,40 exposure/period rows,72 annual observations and eight exact2021-2022 security-PnL reconciliations. Every CAGR uses geometric daily compounding and252-session annualization; annual chart rows use unannualized calendar total returns, with2026 explicitly first-half only. Source ATH30 is unchanged.']
    (ROOT/'research/ath/ATH_RECENT_HISTORY_DIAGNOSTIC.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result=dict(study_id='ath_31_recent_history_diagnostic_v001',status='completed_descriptive_diagnostic',
        source=str(SOURCE.relative_to(ROOT)),inputs=inputs,code_sha256=sha(Path(__file__)),
        artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        report_sha256=sha(ROOT/'research/ath/ATH_RECENT_HISTORY_DIAGNOSTIC.md'),
        verification=dict(source_files=24,period_rows=len(s),annual_rows=len(annual),pnl_reconciliations=8))
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    print(out)
    print(s.loc[s.policy.eq('drift')&s.rule.isin(['sma200','floor5_sma200'])].to_string(index=False))


if __name__=='__main__':
    main()
