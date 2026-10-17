"""Independent original-feature masks, summary and saved-draw checks for ATH34."""
import json
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from audit_ath_baseline import sha256  # noqa: E402


def main(path):
    path=Path(path)
    prep=json.loads((path/'preparation.json').read_text())
    for name,digest in prep['inputs'].items():assert sha256(ROOT/name)==digest
    original={}
    for number,directory in prep['sources'].items():
        f=ROOT/directory/'events.parquet'
        if f.exists():original[int(number)]=pd.read_parquet(f).set_index('event_id',drop=False)
    original_map={'consolidation':15,'proximity':16,'proximity_upper_reference':16,'contraction':18,
        'pre_volume':19,'breakout_volume':20,'close_quality':21,'record_age':22,'sma':23,'strength':24,'combinations':26}
    summary=pd.read_csv(path/'filter_summary.csv')
    checked_masks,checked_summary,checked_intervals=0,0,0
    for job in ['main','momentum','industry','unfiltered']:
        f=pd.read_parquet(path/f'{job}_frame.parquet')
        g=np.load(path/f'{job}_groups.npz')['groups']
        names=json.loads((path/f'{job}_labels.json').read_text())
        assert f.event_id.is_unique and f.date.ge('2008-01-01').all() and f.excess_spy.notna().all()
        for j,name in enumerate(names):
            family,label=name['family'],name['variant']
            if j==0:expected=np.ones(len(f),bool)
            else:
                x=original[original_map[family] if job=='main' else 12 if job=='momentum' else 25].reindex(f.event_id)
                if family=='consolidation':
                    match=re.fullmatch(r'length(\d+)_width(.+)',label)
                    expected=x[f'width_{int(match[1])}'].le(float(match[2])+1e-12)
                elif family in ['proximity','proximity_upper_reference']:
                    n=int(re.search(r'length(\d+)',label)[1])
                    expected=x[f'upper_{n}'].astype(bool)
                    if family=='proximity':expected &= x[f'depth_{n}'].le(float(label.split('_depth')[1])+1e-12)
                elif family in ['contraction','pre_volume','breakout_volume']:
                    match=re.fullmatch(r'window(\d+)_threshold(.+)',label)
                    value=x[f'ratio_{int(match[1])}']
                    threshold=float(match[2])
                    expected=value.ge(threshold-1e-12) if family=='breakout_volume' else value.le(threshold+1e-12)
                elif family=='close_quality':expected=x.close_quality.ge(float(label[7:])-1e-12)
                elif family=='strength':expected=x.breakout_strength.ge(float(label[7:])-1e-12)
                elif family=='record_age':
                    threshold=int(label[7:])
                    expected=x.age_exact.ge(threshold)|(x.age_exact.isna()&x.age_lower_bound.ge(threshold))
                elif family=='sma':expected=x[label]
                elif family=='industry':expected=x.industry_percentile.gt(float(label[7:]))
                elif family.startswith('momentum_'):
                    lookback,selection=label.rsplit('_',1)
                    q=x[f'quintile_{lookback}']
                    expected=q.eq(int(selection[1:])) if selection.startswith('Q') else q.ge({'top60':3,'top40':4,'top20':5}[selection])
                elif family=='combinations':
                    expected=pd.Series(True,index=x.index)
                    for feature,level in re.findall(r'([CVAB])([012])',label):
                        level=int(level)
                        if level==0:continue
                        if feature=='C':expected &= x[f'contraction_{42 if level==1 else 63}'].le(.75+1e-12)
                        elif feature=='V':expected &= x.volume_ratio_63.ge((1.5 if level==1 else 2.)-1e-12)
                        elif feature=='A':expected &= x.age_exact.fillna(x.age_lower_bound).ge(126 if level==1 else 252)
                        else:expected &= x.breakout_strength.ge((.5 if level==1 else 1.)-1e-12)
                else:raise ValueError(family)
            assert np.array_equal(np.asarray(expected,bool),g[:,j]),(job,name)
            checked_masks+=1
        label_index={(v['family'],v['variant']):j for j,v in enumerate(names)}
        for r in summary.loc[summary.job.eq(job)].itertuples():
            keep=g[:,label_index[(r.family,r.variant)]].copy()
            base=np.ones(len(f),bool)
            if r.weighting=='nonoverlap':base &= f.nonoverlap.to_numpy(bool)
            year=f.date.dt.year.to_numpy()
            if r.period=='2008_2017':base &= year<=2017
            elif r.period=='2018_2022':base &= (year>=2018)&(year<=2022)
            elif r.period=='2023_end':base &= year>=2023
            keep &= base
            values=f.excess_spy.to_numpy()[keep]
            actual=values.mean() if len(values) else np.nan
            assert keep.sum()==r.events
            assert np.isclose(actual,r.mean,equal_nan=True)
            assert np.isclose(actual-f.excess_spy.to_numpy()[base].mean(),r.improvement,equal_nan=True)
            checked_summary+=1
        intervals=pd.read_csv(path/f'uncertainty_{job}.csv')
        for weighting in ['all','nonoverlap']:
            for block in [252,504]:
                z=np.load(path/f'draws_{job}_{weighting}_{block}.npz')
                samples=z['samples']
                assert samples.shape==(2000,len(names))
                for r in intervals.loc[intervals.weighting.eq(weighting)&intervals.block.eq(block)].itertuples():
                    j=label_index[(r.family,r.variant)]
                    delta=samples[:,j]-samples[:,0]
                    finite=delta[np.isfinite(delta)]
                    bounds=np.quantile(finite,[.025,.975]) if len(finite)>=1900 else [np.nan,np.nan]
                    assert len(finite)==r.valid_draws
                    assert np.isclose(bounds[0],r.lower95,equal_nan=True)
                    assert np.isclose(bounds[1],r.upper95,equal_nan=True)
                    if j:
                        ix=[k for k,v in enumerate(names) if k and v['family']==r.family]
                        diff=samples[:,ix]-samples[:,[0]]
                        estimates=z['points'][ix]-z['points'][0]
                        complete=np.isfinite(diff).all(axis=1)
                        radius=np.quantile(np.max(np.abs(diff[complete]-estimates),axis=1),.95) if complete.sum()>=1900 else np.nan
                        assert np.isclose(r.family_lower95,r.improvement-radius,equal_nan=True)
                        assert np.isclose(r.family_upper95,r.improvement+radius,equal_nan=True)
                    checked_intervals+=1
    h=pd.read_csv(path/'horizon_summary.csv')
    assert h.loc[h['sample'].eq('horizon_common7')].groupby('period').events.nunique().eq(1).all()
    annual=h.loc[h['sample'].eq('horizon_available')&h.horizon.eq(252)&h.period.eq('all')].iloc[0]
    unfiltered=summary.loc[summary.job.eq('unfiltered')&summary.weighting.eq('all')&summary.period.eq('all')].iloc[0]
    assert annual.events==unfiltered.events and np.isclose(annual['mean'],unfiltered['mean'])
    ranking=pd.read_csv(path/'ranking_summary.csv')
    for job in ['rank_primary','rank_nonoverlap']:
        f=pd.read_parquet(path/f'{job}_frame.parquet')
        membership=np.load(path/f'{job}_groups.npz')['groups']
        names=json.loads((path/f'{job}_labels.json').read_text())
        points=np.array([f.loc[membership[:,j]].groupby('date').excess_spy.mean().mean() for j in range(len(names))])
        for block in [252,504]:
            z=np.load(path/f'draws_{job}_{block}.npz')
            assert np.allclose(points,z['points'])
        for j,name in enumerate(names):
            r=ranking.loc[ranking['sample'].eq(job)&ranking.period.eq('all')&ranking.variant.eq(name['variant'])].iloc[0]
            assert np.isclose(r['mean'],points[j])
    result=dict(source_hashes_checked=len(prep['inputs']),independent_masks=checked_masks,
        independent_summary_rows=checked_summary,pointwise_and_family_interval_rows=checked_intervals,
        ranking_point_groups=20,horizon_common_support_checked=True,passed=True)
    (path/'independent_verification.json').write_text(json.dumps(result,indent=2))
    print(result,flush=True)


if __name__=='__main__':
    main(sys.argv[1])
