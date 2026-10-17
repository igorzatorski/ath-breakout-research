"""Pre-signal mean split-adjusted share-volume contraction."""
import numpy as np

HALVES = [5, 10, 21, 42, 63]
RATIOS = [.50, .75, 1.00]
CELLS = [(n, r) for n in HALVES for r in RATIOS]


def comparable_volume(volume, share_factor):
    valid = np.isfinite(volume) & volume.ge(0) & np.isfinite(share_factor) & share_factor.gt(0)
    result = (volume*share_factor).where(valid)
    return result.where(np.isfinite(result))


def volume_features(volumes, half):
    clean = volumes.where(np.isfinite(volumes) & volumes.ge(0))
    recent = clean.rolling(half, min_periods=half).mean().shift(1)
    earlier = recent.shift(half)
    ratio = (recent/earlier).where(earlier.gt(0) & np.isfinite(earlier) & np.isfinite(recent))
    return earlier, recent, ratio


def mask(frame, half, ratio):
    return np.ones(len(frame), dtype=bool) if half == 0 else frame[f'ratio_{half}'].le(ratio+1e-12).to_numpy()
