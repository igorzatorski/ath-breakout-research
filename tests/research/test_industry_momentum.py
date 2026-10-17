import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.industry_momentum import attach_industry, prepare_history, industry_ranks, mask, sic_mapping


def test_effective_changes_inclusive_endpoints_and_gaps():
    h = prepare_history(pd.DataFrame({'permno': [1, 1], 'effective_from': ['2000-01-01', '2000-01-04'],
        'effective_to': ['2000-01-02', '2000-01-05'], 'siccd': [100, 200]}))
    assert h.permno.dtype == np.dtype('int64')
    q = pd.DataFrame({'permno': [1]*6, 'date': pd.date_range('1999-12-31', periods=6)})
    mapping = np.zeros(10000, int)
    mapping[100], mapping[200] = 1, 2
    z = attach_industry(q, h, mapping)
    assert z.industry.tolist() == [0, 1, 1, 0, 2, 2]
    bad = pd.concat([h, h.iloc[:1]])
    with pytest.raises(ValueError, match='Overlapping'):
        prepare_history(bad)


def test_mid_distribution_ties_peer_support_and_strict_threshold():
    f = pd.DataFrame({'date': pd.Timestamp('2000-01-01'), 'industry': [1]*20+[2]*2+[0],
        'momentum': [1.]*20+[0., 1., 2.], 'classification_status': ['classified']*22+['invalid_sic']})
    z = industry_ranks(f)
    assert z.iloc[:20].industry_percentile.eq(.5).all()
    assert z.iloc[:20].industry_supported.all()
    assert not mask(z.iloc[:20], .5).any()
    assert not z.iloc[20:].industry_supported.any()


def test_mapping_unknown_codes_and_non_tied_ranks():
    text = '\n'.join(f'{i} Group Industry'+('\n 7370-7379' if i == 6 else '') for i in range(1, 13))
    mapping, names = sic_mapping(text)
    assert len(names) == 12 and mapping[0] == 0 and mapping[9999] == 0
    assert mapping[100] == 12 and mapping[7372] == 6
    f = pd.DataFrame({'date': pd.Timestamp('2000-01-01'), 'industry': 1,
        'momentum': np.arange(20), 'classification_status': 'classified'})
    z = industry_ranks(f)
    assert np.allclose(z.industry_percentile, (np.arange(20)+.5)/20)
    assert mask(z, .8).sum() == 4
