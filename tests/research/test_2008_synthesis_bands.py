import importlib.util
from pathlib import Path

import numpy as np


def load():
    p=Path(__file__).resolve().parents[2]/'scripts/research/bootstrap_ath_2008_evidence.py'
    spec=importlib.util.spec_from_file_location('bands2008',p)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.bands


def test_simultaneous_band_keeps_empty_cells_and_baseline_pairing():
    samples=np.array([[1.,2.,np.nan],[2.,4.,np.nan],[3.,6.,np.nan],[4.,8.,np.nan]])
    labels=[dict(family='reference',variant='reference'),dict(family='grid',variant='a'),dict(family='grid',variant='empty')]
    r=load()(np.array([2.5,5.,np.nan]),samples,labels)
    assert r.loc[1,'improvement']==2.5
    assert r.loc[1,'lower95']==np.quantile([1.,2.,3.,4.],.025)
    assert np.isnan(r.loc[1,'family_lower95'])
    assert r.loc[2,'valid_draws']==0 and r.loc[1,'family_size']==2


def test_family_radius_uses_only_its_declared_family():
    points=np.array([0.,1.,10.])
    samples=np.array([[0.,.9,-100.],[0.,1.1,100.]])
    labels=[dict(family='reference',variant='reference'),dict(family='a',variant='a'),dict(family='b',variant='b')]
    r=load()(points,samples,labels)
    assert np.isclose(r.loc[1,'family_lower95'],.9)
