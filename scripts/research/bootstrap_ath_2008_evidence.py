"""Crossed-company/calendar draws for the frozen ATH34 evidence bundles."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from ath_breakout.research.filter_combinations import (  # noqa: E402
    STATES, config_name, bootstrap_means, contrasts, contrast_intervals,
)
from ath_breakout.research.event_ranking import (  # noqa: E402
    balanced_draws,contrast_matrix,intervals,
)


def bands(points,samples,labels):
    """Pointwise intervals plus original family-sized simultaneous differences."""
    rows=[]
    families={x['family'] for x in labels[1:]}
    radii={}
    for family in families:
        ix=[i for i,x in enumerate(labels) if i and x['family']==family]
        diff=samples[:,ix]-samples[:,[0]]
        estimate=points[ix]-points[0]
        complete=np.isfinite(diff).all(axis=1)
        radius=np.quantile(np.abs(diff[complete]-estimate).max(axis=1),.95) if complete.sum()>=.95*len(samples) else np.nan
        radii[family]=(radius,int(complete.sum()),len(ix))
    for j,label in enumerate(labels):
        values=samples[:,j]
        finite=values[np.isfinite(values)]
        level=np.quantile(finite,[.025,.975]) if len(finite)>=.95*len(samples) else [np.nan,np.nan]
        difference=samples[:,j]-samples[:,0]
        valid=difference[np.isfinite(difference)]
        ci=np.quantile(valid,[.025,.975]) if len(valid)>=.95*len(samples) else [np.nan,np.nan]
        radius,support,size=radii.get(label['family'],(np.nan,0,0))
        estimate=points[j]-points[0]
        rows.append(dict(**label,level_estimate=points[j],level_lower95=level[0],level_upper95=level[1],
            improvement=estimate,lower95=ci[0],upper95=ci[1],valid_draws=len(valid),
            family_lower95=estimate-radius,family_upper95=estimate+radius,
            family_complete_draws=support,family_size=size))
    return pd.DataFrame(rows)


def main(path,job):
    path=Path(path)
    frame=pd.read_parquet(path/f'{job}_frame.parquet')
    matrix=np.load(path/f'{job}_groups.npz')['groups']
    labels=json.loads((path/f'{job}_labels.json').read_text())
    assert matrix.shape==(len(frame),len(labels)) and matrix[:,0].all()
    rows=[]
    if job.startswith('rank_'):
        definitions,coefficients=contrast_matrix([x['variant'] for x in labels],top_only=job=='rank_nonoverlap')
        for block in [252,504]:
            print(job,'block',block,flush=True)
            points,samples=balanced_draws(frame,matrix,valid_nyse_sessions(frame.date.min(),frame.date.max()),block,draws=2000,seed=20261017)
            np.savez_compressed(path/f'draws_{job}_{block}.npz',points=points,samples=samples)
            f=intervals(points,samples,definitions,coefficients)
            f.insert(0,'job',job)
            f.insert(1,'block',block)
            rows.append(f)
    else:
        for weighting,keep in [('all',np.ones(len(frame),bool)),('nonoverlap',frame.nonoverlap.to_numpy(bool))]:
            f=frame.loc[keep].reset_index(drop=True)
            g=matrix[keep]
            counts=g.sum(axis=0)
            points=np.divide(g.T@f.excess_spy.to_numpy(),counts,out=np.full(g.shape[1],np.nan),where=counts>0)
            for block in [252,504]:
                print(job,weighting,'block',block,flush=True)
                samples=bootstrap_means(f,g,valid_nyse_sessions(f.date.min(),f.date.max()),block=block,draws=2000,seed=20261016)
                np.savez_compressed(path/f'draws_{job}_{weighting}_{block}.npz',points=points,samples=samples)
                result=bands(points,samples,labels)
                result.insert(0,'job',job)
                result.insert(1,'weighting',weighting)
                result.insert(2,'block',block)
                rows.append(result)
                if job=='main':
                    lookup={x['variant']:i for i,x in enumerate(labels) if x['family']=='combinations'}
                    indices=[0]+[lookup[config_name(s)] for s in STATES[1:]]
                    combo=contrast_intervals(points[indices],samples[:,indices],contrasts())
                    combo.insert(0,'weighting',weighting)
                    combo.insert(1,'block',block)
                    combo.to_csv(path/f'combination_contrasts_{weighting}_{block}.csv',index=False)
    result=pd.concat(rows,ignore_index=True)
    result.to_csv(path/f'uncertainty_{job}.csv',index=False)
    print('Completed',job,len(result),'interval rows',flush=True)


if __name__=='__main__':
    main(sys.argv[1],sys.argv[2])
