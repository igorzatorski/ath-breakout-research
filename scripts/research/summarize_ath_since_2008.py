"""User-requested2008 scope summary from frozen ATH30 continuing portfolios."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'outputs/backtests/ath_30_initial_risk_trend_v001/20261017T154917914966Z'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out=ROOT/f'outputs/research/ath/ath_32_scope_2008_summary_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    source=json.loads((SOURCE/'manifest.json').read_text())
    hashes={k.replace('\\','/'):v for k,v in source['artifacts'].items()}
    inputs={str((SOURCE/'manifest.json').relative_to(ROOT)):sha(SOURCE/'manifest.json')}
    rows=[]
    for d in sorted(SOURCE.glob('*_10bps')):
        file=d/'equity.csv'
        digest=sha(file)
        assert digest==hashes[str(file.relative_to(SOURCE)).replace('\\','/')]
        inputs[str(file.relative_to(ROOT))]=digest
        e=pd.read_csv(file,parse_dates=['date'])
        f=e.loc[e.date.ge('2008-01-01')]
        previous=e.iloc[f.index[0]-1]
        curve=np.r_[previous.nav,f.nav.to_numpy()]
        spy=np.r_[previous.spy_nav,f.spy_nav.to_numpy()]
        n=len(f)
        rule,policy=d.name.split('__')
        growth=(curve[-1]/curve[0])**(252/n)-1
        assert np.isclose(growth,np.expm1(np.log1p(f.daily_return).mean()*252))
        rows.append(dict(rule=rule,policy=policy.removesuffix('_10bps'),start=str(f.date.min().date()),
            end=str(f.date.max().date()),sessions=n,cagr=growth,spy_cagr=(spy[-1]/spy[0])**(252/n)-1,
            max_drawdown=np.min(curve/np.maximum.accumulate(curve)-1),
            spy_max_drawdown=np.min(spy/np.maximum.accumulate(spy)-1),average_exposure=f.exposure.mean(),
            inherited_positions=int(previous.positions),interpretation='continuing ATH30 portfolio slice; not cash restart'))
    s=pd.DataFrame(rows)
    s.to_csv(out/'since_2008.csv',index=False)
    lines=['# ATH research overview:2008 onward is primary','',
        'Updated2026-10-17 at the user request. Main evaluation window is2008-01-02 through2026-06-30. Treat2018 onward and2023 onward as nested stability diagnostics. Pre2008 history is context/robustness, not the main evidence for present usefulness. This supersedes the earlier2018-primary scope without deleting historical records.','',
        '## What exists','',
        '- Reproducible local US-equity CRSP data, including distributions and terminal effects, historical monthly liquidity universe and history-quality restrictions. Data begins1993 and endsJune2026; source signals begin1994. This is a broad conditional sample of liquid stocks, not all US stocks.',
        '- Saved ATH definitions, next-opening execution, fixed forward horizons, same-window SPY and matched non-ATH controls, momentum and event-level CAPM checks, repeated-event and tail/period diagnostics.',
        '- Exploratory entry families: momentum12-1/6-1/3-1; consolidation width/length, prior-ATH proximity and range contraction; pre-breakout and signal-day volume; closing location; prior-record age; price/SMA alignment; ATR-normalized breakout strength; historical-industry momentum; fixed combinations and M/MV/MVC rankings.',
        '- Actual capital-constrained portfolios: maximum20 companies,5% entry target, drift versus monthly equal weighting, fresh ATH plus6-1/top20 source candidates prioritized by MV. ExitsSMA50/SMA200, with/without a fixed5% original-entry price floor; next observed opening execution,10bps per trade and selected gross references. Cash earns0%.',
        '- English protocols, code, focused tests, independent accounting/decision audits, saved event/transaction/holdings outputs, registry and Notion reports. Failed technical attempts are retained and excluded from conclusions.','',
        '## Current2008-onward portfolio slice, after costs','',
        '**Important:** these are continuing portfolios simulated from1994, cropped to2008. They inherit18-20 positions and their original entry anchors at the boundary. They are not new USD100,000 cash-start2008 simulations. No rules, security selection, positions or capital path were changed to create this summary.','',
        '| Exit | Drift CAGR | Monthly equal CAGR | Drift max drawdown | Monthly max drawdown |',
        '| --- | ---: | ---: | ---: | ---: |']
    labels={'sma50':'SMA50','floor5_sma50':'5% floor + SMA50','sma200':'SMA200','floor5_sma200':'5% floor + SMA200'}
    for rule,label in labels.items():
        a=s.loc[s.rule.eq(rule)&s.policy.eq('drift')].iloc[0]
        b=s.loc[s.rule.eq(rule)&s.policy.eq('monthly_equal')].iloc[0]
        lines.append(f'| {label} | {a.cagr:.2%} | {b.cagr:.2%} | {a.max_drawdown:.2%} | {b.max_drawdown:.2%} |')
    lines+=['| SPY | 11.26% | 11.26% | -52.30% | -52.30% |','',
        'All eight saved net variants trail SPY in CAGR over this window. Some have lower drawdowns and lower equity exposure, so this is not a risk-adjusted alpha test. CAGR annualization uses252 sessions; maximum drawdown starts from the immediately preceding2007 closing wealth, with the pre2008 peak reset for this window.','',
        '## What the evidence supports','',
        '- A positive right tail exists, but the average event and portfolio outcomes depend strongly on period, repeated-company weighting, concentration and exposure. Positive skew alone does not establish a profitable net strategy.',
        '- Standalone ATH alpha is not robustly established. Earlier event CAPM and matched-control findings have material weighting/model/sampling limitations and do not measure the alpha of these actual portfolios.',
        '- SMA50 truncated some future recoveries/large winners and protected against some much larger later losses in the exit-conditioned252-session path study. SMA200 improves CAGR versusSMA50 in both current2008-onward weighting comparisons. This does not establish an optimal length.',
        '- The5% close-triggered floor lowers2008-onward CAGR at either SMA. It is not an intraday stop or a guarantee of a5% realized loss; it does not guarantee smaller portfolio drawdown.',
        '- Entry-filter and MV ranking means produced exploratory leads, especially momentum, signal-day volume and breakout strength. No validated mandatory full filter stack, monotonic ranking or modern incremental advantage is established.','',
        '## What remains unknown','',
        '- Whether pure ATH adds incremental information above momentum and common risk exposures in the principal2008-onward sample. Earlier full-history statistics cannot silently become2008-specific claims.',
        '- Whether candidate filters improve that same modern baseline after dependence, overlapping observations, multiplicity and selection are handled. Not every earlier filter result has been recomputed and reviewed for2008 onward.',
        '- Whether portfolio returns contain positive risk-adjusted net alpha after exposure, concentration, factor risks, more realistic execution and cash interest are addressed.',
        '- Which exit, sizing, ranking or rebalance rule generalizes. Current rules are tested prototypes, not optimal settings. Exit changes alter vacancies and executed entries, so portfolio comparisons are joint system effects.',
        '- Whether results survive an independent unseen period. All inspected history is development data. The economic explanation for period differences remains unestablished.','',
        '## Proposed next sequence','',
        '1. Freeze a clean2008 cash-start reference and compare it with the inherited-position slice before adopting principal-period portfolio claims. Keep existing signals/ranking/costs and both existing weighting policies unchanged.',
        '2. Re-express saved baseline/filter evidence on the same2008-onward population with frozen subperiods and full coverage disclosures; do not run a new parameter search or select only favorable dates.',
        '3. Diagnose concentration/exposure and portfolio risk-adjusted returns, retaining SPY and simple matched comparators. Address candidate hypotheses one at a time after reviewing this evidence.',
        '4. Freeze any eventual rule before independent validation. No live-ready strategy, optimum or confirmed alpha is claimed.','',
        '## Scope of this update','',
        f'Run: `{out.relative_to(ROOT).as_posix()}`. Eight source-equity hashes and geometric-return identities checked;4,652 sessions per variant. This is a saved-output scope/summary update, not a new backtest, filter or validation period.']
    report=ROOT/'research/ath/ATH_RESEARCH_OVERVIEW_2008.md'
    report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result=dict(study_id='ath_32_scope_2008_summary_v001',status='completed_saved_output_summary',
        source=str(SOURCE.relative_to(ROOT)),inputs=inputs,code_sha256=sha(Path(__file__)),
        report_sha256=sha(report),artifacts={'since_2008.csv':sha(out/'since_2008.csv')},
        primary_window=['2008-01-02','2026-06-30'],boundary='inherited positions; no cash restart')
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    print(out)
    print(s.to_string(index=False))


if __name__=='__main__':
    main()
