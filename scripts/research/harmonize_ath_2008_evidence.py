"""ATH34: saved-feature, common-period synthesis; no source or parameter changes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from ath_breakout.research import (  # noqa: E402
    consolidation_grid as consolidation, proximity_grid as proximity,
    range_contraction as contraction, volume_dryup as dryup,
    breakout_volume as volume, close_quality as quality, record_age as age,
    sma_trend as sma, breakout_strength as strength, industry_momentum as industry,
    filter_combinations as combinations, event_ranking as ranking,
)
from audit_ath_baseline import sha256  # noqa: E402


def periods(frame):
    year=frame.date.dt.year
    return [('all',np.ones(len(frame),bool)),('2008_2017',year.le(2017).to_numpy()),
        ('2018_2022',year.between(2018,2022).to_numpy()),('2023_end',year.ge(2023).to_numpy())]


def describe(frame,metric='excess_spy'):
    if frame.empty:
        return dict(events=0,companies=0,dates=0,mean=np.nan,median=np.nan,stock=np.nan,spy=np.nan,
            loss_frequency=np.nan,equal_company=np.nan,equal_security=np.nan,equal_date=np.nan,last_signal=None)
    return dict(events=len(frame),companies=frame.permco.nunique(),dates=frame.date.nunique(),
        mean=frame[metric].mean(),median=frame[metric].median(),stock=frame.stock_return.mean(),spy=frame.spy_return.mean(),
        loss_frequency=frame.stock_return.lt(0).mean(),equal_company=frame.groupby('permco')[metric].mean().mean(),
        equal_security=frame.groupby('permno')[metric].mean().mean(),equal_date=frame.groupby('date')[metric].mean().mean(),
        last_signal=str(frame.date.max().date()))


def prepare():
    out=ROOT/f'outputs/research/ath/ath_34_2008_evidence_synthesis_v001/{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
    out.mkdir(parents=True)
    inputs,sources={},{}

    def load(number,file='events.parquet'):
        families=list((ROOT/'outputs/research/ath').glob(f'ath_{number:02d}_*'))
        if number==4:
            families=[f for f in families if f.name.endswith('v002')]
        assert len(families)==1,(number,families)
        runs=sorted([d for d in families[0].iterdir() if (d/'manifest.json').exists()])
        directory=runs[-1]
        manifest=json.loads((directory/'manifest.json').read_text())
        hashes={k.replace('\\','/'):v for k,v in manifest['artifacts'].items()}
        path=directory/file
        digest=sha256(path)
        assert digest==hashes[file]
        inputs[str(path.relative_to(ROOT))]=digest
        inputs[str((directory/'manifest.json').relative_to(ROOT))]=sha256(directory/'manifest.json')
        sources[str(number)]=str(directory.relative_to(ROOT))
        return pd.read_parquet(path)

    raw=load(12)
    assert raw.event_id.is_unique
    annual=raw.loc[raw.date.ge('2008-01-01')&raw.excess_spy.notna()].copy()
    common=annual.loc[annual.common_momentum].copy()
    reference=common.loc[common.quintile_6_1.eq(5)].sort_values(['date','event_id']).reset_index(drop=True)
    reference.to_parquet(out/'feature_reference_original.parquet',index=False)
    family_specs=[('consolidation',15),('proximity',16),('contraction',18),('pre_volume',19),
        ('breakout_volume',20),('close_quality',21),('record_age',22),('sma',23),('strength',24)]
    frames,coverage={},[]
    complete=np.ones(len(reference),bool)
    for family,number in family_specs:
        x=load(number).set_index('event_id',drop=False).reindex(reference.event_id)
        assert np.allclose(x.stock_return,reference.stock_return,equal_nan=True)
        assert np.allclose(x.excess_spy,reference.excess_spy,equal_nan=True)
        if family=='close_quality':valid=x.quality_status.eq('ok').to_numpy()
        elif family=='record_age':valid=x.age_classified.fillna(False).to_numpy(bool)
        else:valid=x.feature_complete.fillna(False).to_numpy(bool)
        complete &= valid
        frames[family]=x.reset_index(drop=True)
        coverage.append(dict(family=family,original_reference=len(reference),within_family_supported=int(valid.sum())))
    combo=load(26).set_index('event_id',drop=False).reindex(reference.event_id).reset_index(drop=True)
    complete &= combo.combination_support.to_numpy(bool)
    main=reference.loc[complete].reset_index(drop=True)
    groups=[np.ones(len(main),bool)]
    labels=[dict(family='reference',variant='reference')]

    def add(family,variant,mask):
        labels.append(dict(family=family,variant=variant))
        groups.append(np.asarray(mask,dtype=bool))
    for family,_ in family_specs:
        f=frames[family].loc[complete].reset_index(drop=True)
        if family=='consolidation':
            for n,w in consolidation.CELLS:add(family,f'length{n}_width{w:g}',f[f'width_{n}'].le(w+1e-12))
        elif family=='proximity':
            for n,d in proximity.CELLS:add(family,f'length{n}_depth{d:g}',proximity.selected(f,n,d))
            for n in proximity.LENGTHS:add('proximity_upper_reference',f'length{n}_upper_only',proximity.selected(f,n,-1.))
        elif family in ['contraction','pre_volume','breakout_volume']:
            module={'contraction':contraction,'pre_volume':dryup,'breakout_volume':volume}[family]
            for n,t in module.CELLS:add(family,f'window{n}_threshold{t:g}',module.mask(f,n,t))
        elif family=='close_quality':
            for t in quality.THRESHOLDS:add(family,f'minimum{t:g}',quality.mask(f,t))
        elif family=='record_age':
            for t in age.MINIMUM_AGES:add(family,f'minimum{t}',age.mask(f,t))
        elif family=='sma':
            for name in sma.FILTERS:add(family,name,f[name])
        elif family=='strength':
            for t in strength.THRESHOLDS:add(family,f'minimum{t:g}',strength.mask(f,t))
    c=combo.loc[complete].reset_index(drop=True)
    masks=combinations.memberships(c)
    for i,state in enumerate(combinations.STATES[1:],1):add('combinations',combinations.config_name(state),masks[:,i])
    keep_cols=['event_id','permno','permco','date','stock_return','spy_return','excess_spy','nonoverlap']

    def bundle(name,frame,membership,names):
        frame[keep_cols].to_parquet(out/f'{name}_frame.parquet',index=False)
        np.savez_compressed(out/f'{name}_groups.npz',groups=np.asarray(membership,dtype=bool))
        (out/f'{name}_labels.json').write_text(json.dumps(names,indent=2))
    bundle('main',main,np.column_stack(groups),labels)
    for row in coverage:row['global_common_supported']=len(main)
    coverage.append(dict(family='combinations',original_reference=len(reference),within_family_supported=int(combo.combination_support.sum()),global_common_supported=len(main)))
    momgroups=[np.ones(len(common),bool)]
    momlabels=[dict(family='reference',variant='reference')]
    for lookback in ['12_1','6_1','3_1']:
        q=common[f'quintile_{lookback}']
        for minimum,name in [(3,'top60'),(4,'top40'),(5,'top20')]:
            momlabels.append(dict(family='momentum_primary9',variant=f'{lookback}_{name}'))
            momgroups.append(q.ge(minimum).to_numpy())
        for quintile in range(1,6):
            momlabels.append(dict(family='momentum_quintiles',variant=f'{lookback}_Q{quintile}'))
            momgroups.append(q.eq(quintile).to_numpy())
    bundle('momentum',common,np.column_stack(momgroups),momlabels)
    ind=load(25)
    ind=ind.loc[ind.date.ge('2008-01-01')&ind.excess_spy.notna()&ind.feature_complete].copy()
    ig=[np.ones(len(ind),bool)]+[industry.mask(ind,t) for t in industry.THRESHOLDS]
    il=[dict(family='reference',variant='reference')]+[dict(family='industry',variant=f'minimum{t:g}') for t in industry.THRESHOLDS]
    bundle('industry',ind,np.column_stack(ig),il)
    coverage.append(dict(family='industry',original_reference=len(reference),within_family_supported=len(ind),global_common_supported=None))
    bundle('unfiltered',annual,np.ones((len(annual),1),bool),[dict(family='reference',variant='unfiltered_ATH')])
    pd.DataFrame(coverage).to_csv(out/'coverage.csv',index=False)
    summaries=[]
    for job in ['main','momentum','industry','unfiltered']:
        f=pd.read_parquet(out/f'{job}_frame.parquet')
        matrix=np.load(out/f'{job}_groups.npz')['groups']
        names=json.loads((out/f'{job}_labels.json').read_text())
        for weighting,eligible in [('all',np.ones(len(f),bool)),('nonoverlap',f.nonoverlap.to_numpy(bool))]:
            for period,dates in periods(f):
                base=f.loc[eligible&dates]
                for j,name in enumerate(names):
                    selected=f.loc[eligible&dates&matrix[:,j]]
                    summaries.append(dict(job=job,weighting=weighting,period=period,**name,
                        baseline_mean=base.excess_spy.mean(),improvement=selected.excess_spy.mean()-base.excess_spy.mean(),**describe(selected)))
    pd.DataFrame(summaries).to_csv(out/'filter_summary.csv',index=False)
    metrics=[]

    def metric_rows(sample,f,metric):
        f=f.loc[f[metric].notna()&f.date.ge('2008-01-01')]
        for weighting,eligible in [('all',np.ones(len(f),bool)),('nonoverlap',f.nonoverlap.to_numpy(bool))]:
            for period,dates in periods(f):
                metrics.append(dict(sample=sample,metric=metric,weighting=weighting,period=period,**describe(f.loc[eligible&dates],metric)))
    metric_rows('unfiltered_annual_ATH',annual,'excess_spy')
    metric_rows('common_momentum_annual',common,'excess_spy')
    metric_rows('ATH6_1_top20',reference,'excess_spy')
    metric_rows('momentum12_matched_controls',annual,'new_excess')
    incremental=load(14)
    incremental=incremental.loc[incremental.common_momentum&incremental.quintile_6_1.eq(5)]
    metric_rows('incremental_ATH6_1_matched',incremental,'incremental_ath')
    car=annual.loc[annual.stock_car.notna()].copy()
    metric_rows('CAPM_CAR_all_supported',car,'stock_car')
    car=car.loc[car.old_valid_controls.eq(5)&car.momentum_valid_controls.eq(5)&car.old_car.notna()&car.momentum_car.notna()].copy()
    car['incremental_car']=car.stock_car-car.momentum_car
    metric_rows('CAPM_CAR_common',car,'stock_car')
    metric_rows('CAPM_CAR_incremental_common',car,'incremental_car')
    pd.DataFrame(metrics).to_csv(out/'signal_control_capm_summary.csv',index=False)
    horizons=pd.concat([load(4,'forward_returns.parquet'),load(6,'annual_returns.parquet'),load(7,'long_returns.parquet')],ignore_index=True)
    assert not horizons.duplicated(['event_id','horizon']).any()
    identity=raw[['event_id','permco','nonoverlap']]
    horizons=horizons.drop(columns=['nonoverlap'],errors='ignore').merge(identity,on='event_id',validate='many_to_one')
    horizons=horizons.loc[horizons.date.ge('2008-01-01')]
    pivot=horizons.pivot(index='event_id',columns='horizon',values='excess_spy')
    assert set(pivot.columns)=={5,21,63,126,252,504,756}
    common_ids=pivot.index[pivot.notna().all(axis=1)]
    hrows=[]
    for sample,universe in [('horizon_available',horizons),('horizon_common7',horizons.loc[horizons.event_id.isin(common_ids)])]:
        for horizon,g in universe.groupby('horizon'):
            g=g.loc[g.excess_spy.notna()]
            for period,mask in periods(g):hrows.append(dict(sample=sample,horizon=int(horizon),period=period,**describe(g.loc[mask])))
    pd.DataFrame(hrows).to_csv(out/'horizon_summary.csv',index=False)
    ranks=load(27)
    ranks=ranks.loc[ranks.date.ge('2008-01-01')]
    rankrows=[]
    for job,flag,top_only in [('rank_primary','primary_evaluation',False),('rank_nonoverlap','nonoverlap_top_evaluation',True)]:
        f=ranks.loc[ranks[flag]].copy()
        names,membership=ranking.groups(f,top_only=top_only)
        bundle(job,f,membership,[dict(family='ranking',variant=name) for name in names])
        for period,dates in periods(f):
            for j,name in enumerate(names):
                selected=f.loc[dates&membership[:,j]]
                info=describe(selected)
                info['event_weighted_mean']=info['mean']
                info['mean']=info['equal_date']
                info['stock']=selected.groupby('date').stock_return.mean().mean()
                info['spy']=selected.groupby('date').spy_return.mean().mean()
                rankrows.append(dict(sample=job,period=period,variant=name,**info))
    pd.DataFrame(rankrows).to_csv(out/'ranking_summary.csv',index=False)
    config=dict(study_id='ath_34_2008_evidence_synthesis_v001',status='prepared',inputs=inputs,sources=sources,
        source_reference_events=len(reference),common_feature_events=len(main),common_momentum_events=len(common),
        groups=len(labels),single_feature_variants=sum(x['family'] not in ['reference','combinations','proximity_upper_reference'] for x in labels),
        main_source_dates=[str(main.date.min().date()),str(main.date.max().date())],draws=2000,blocks=[252,504],seed=20261016,
        protocol_sha256=sha256(ROOT/'research/ath/ATH_2008_EVIDENCE_SYNTHESIS_PLAN.md'))
    (out/'preparation.json').write_text(json.dumps(config,indent=2))
    print(out,flush=True)
    print({k:v for k,v in config.items() if k not in ['inputs','sources']},flush=True)
    print(pd.DataFrame(metrics).query("weighting=='all' and period=='all'").to_string(index=False),flush=True)


if __name__=='__main__':
    prepare()
