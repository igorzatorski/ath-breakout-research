"""Strict prior-high windows, complete histories and rank sensitivity."""
import numpy as np
import pandas as pd

from ath_breakout.research.event_ranking import rank_events


def test_signal_excludes_today_and_requires_complete_window():
    high = pd.Series([10., 12., 11., 15., 14.])
    prior = high.rolling(3, min_periods=3).max().shift(1)
    close = pd.Series([9., 11., 10., 14., 13.])
    assert pd.isna(prior.iloc[2])
    assert prior.iloc[3] == 12. and close.iloc[3] > prior.iloc[3]
    assert prior.iloc[4] == 15. and not close.iloc[4] > prior.iloc[4]
    high.iloc[1] = np.nan
    assert pd.isna(high.rolling(3, min_periods=3).max().shift(1).iloc[3])


def test_shorter_record_can_break_below_all_time_record():
    high = pd.Series([100., 40., 41., 42., 44.])
    short = high.rolling(3, min_periods=3).max().shift(1)
    ath = high.cummax().shift(1)
    close = 43.
    assert close > short.iloc[-1] and close < ath.iloc[-1]


def test_new_candidate_changes_same_date_priority():
    frame = pd.DataFrame(dict(date=pd.to_datetime(['2008-01-02']*3),
        momentum_6_1=[.2, .4, .3], volume_ratio_63=[1., 2., 1.5], contraction_42=[1., 1., 1.]))
    old = rank_events(frame.iloc[:2])
    new = rank_events(frame)
    assert new.score_MV.iloc[2] > new.score_MV.iloc[0]
    assert new.score_MV.iloc[0] != old.score_MV.iloc[0]
    assert np.isfinite(new.score_MV).all()
