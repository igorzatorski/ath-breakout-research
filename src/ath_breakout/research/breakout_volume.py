"""Signal-day volume relative to a strictly prior scheduled-session mean."""
import numpy as np

LOOKBACKS = [5, 10, 21, 42, 63]
THRESHOLDS = [1., 1.5, 2., 3.]
CELLS = [(n, r) for n in LOOKBACKS for r in THRESHOLDS]


def breakout_volume_features(volumes, lookback):
    clean = volumes.where(np.isfinite(volumes) & volumes.ge(0))
    prior = clean.rolling(lookback, min_periods=lookback).mean().shift(1)
    ratio = (clean/prior).where(prior.gt(0) & np.isfinite(prior) & np.isfinite(clean))
    return prior, clean, ratio


def mask(frame, lookback, threshold):
    return np.ones(len(frame), dtype=bool) if lookback == 0 else frame[f'ratio_{lookback}'].ge(threshold-1e-12).to_numpy()
