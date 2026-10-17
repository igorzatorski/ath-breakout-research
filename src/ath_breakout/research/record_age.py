"""Past-record creation positions, excluding ties and the signal observation."""
import numpy as np
import pandas as pd

MINIMUM_AGES = [5, 21, 63, 126, 252]


def previous_record_positions(frame, positions, carried):
    new_record = frame.observed_bound.notna() & (frame.prior_ath.isna() | frame.observed_bound.gt(frame.prior_ath))
    current = pd.Series(np.where(new_record, positions, np.nan), index=frame.index).groupby(frame.permno).ffill()
    before = current.groupby(frame.permno).shift().fillna(frame.permno.map(carried))
    updated = carried.copy()
    updated.update(current.groupby(frame.permno).max().dropna().to_dict())
    return before, updated


def classified(frame):
    return frame.age_exact.notna() | frame.age_lower_bound.ge(252)


def mask(frame, minimum):
    if minimum < 0:
        return np.ones(len(frame), dtype=bool)
    return (frame.age_exact.ge(minimum) | (frame.age_exact.isna() & frame.age_lower_bound.ge(minimum))).to_numpy()


def band_codes(frame):
    return np.column_stack([mask(frame, n) for n in MINIMUM_AGES]).sum(axis=1)
