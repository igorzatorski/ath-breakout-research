"""Equal past-half closing ranges; no current-day or outcome inputs."""
import numpy as np

from ath_breakout.research.consolidation_grid import past_width

HALVES = [5, 10, 21, 42, 63]
RATIOS = [.50, .75, 1.00]
CELLS = [(n, r) for n in HALVES for r in RATIOS]


def contraction_features(prices, half):
    recent = past_width(prices, half)
    earlier = recent.shift(half)
    ratio = (recent/earlier).where(earlier.gt(1e-12) & np.isfinite(earlier) & np.isfinite(recent))
    return earlier, recent, ratio


def mask(frame, half, ratio):
    return np.ones(len(frame), dtype=bool) if half == 0 else frame[f'ratio_{half}'].le(ratio+1e-12).to_numpy()
