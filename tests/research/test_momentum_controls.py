import numpy as np
import pandas as pd

from ath_breakout.research.momentum_controls import lagged_momentum, match_momentum_controls


def test_momentum_lag_missing_zero_and_no_future():
    r = pd.DataFrame({"x": np.full(300, .001)})
    m = lagged_momentum(r)
    assert np.isnan(m.iloc[250, 0])
    assert np.isclose(m.iloc[251, 0], 1.001**231 - 1)
    r.iloc[231:] = .9
    assert np.isclose(lagged_momentum(r).iloc[251, 0], m.iloc[251, 0])
    r.iloc[10, 0] = np.nan
    assert np.isnan(lagged_momentum(r).iloc[251, 0])
    r.iloc[10, 0] = -1
    assert lagged_momentum(r).iloc[251, 0] == -1


def test_matching_company_exclusion_calipers_and_ties():
    c = pd.DataFrame({"permno": range(1, 11), "permco": [1, 2, 2, 4, 5, 6, 7, 8, 9, 10],
                      "market_cap": [100.]*8+[1000., 100.], "vol63": [.2]*10,
                      "momentum": [.2]*9+[.301]})
    e = pd.DataFrame({"permno": [99], "permco": [1], "market_cap": [100.], "vol63": [.2], "momentum": [.2]})
    assert match_momentum_controls(e, c)[99] == [2, 4, 5, 6, 7]
    assert match_momentum_controls(e.assign(momentum=np.nan), c) == {}
    assert match_momentum_controls(e, c.iloc[:5]) == {}


def test_momentum_matches_direct_products_across_year_boundary():
    rng = np.random.default_rng(812)
    r = pd.DataFrame(rng.uniform(-.08, .08, (600, 3)), index=pd.bdate_range("2023-01-02", periods=600))
    r.iloc[120, 0] = np.nan
    r.iloc[300, 1] = -1
    r.iloc[310, 2] = -1.01
    m = lagged_momentum(r)
    for t in [251, 260, 320, 400, 599]:
        for c in range(3):
            window = r.iloc[t-251:t-20, c].to_numpy()
            expected = np.prod(1+window)-1 if np.isfinite(window).all() and (window >= -1).all() else np.nan
            assert np.isclose(m.iloc[t, c], expected, equal_nan=True, atol=1e-12)
