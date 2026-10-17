"""Close-confirmed ATH overshoot in units of strictly prior simple ATR20."""
import numpy as np

THRESHOLDS = [.10, .25, .50, 1., 2.]


def prior_atr(high, low, close, window=20):
    valid = high.gt(0) & low.gt(0) & close.gt(0) & (high >= close) & (close >= low)
    valid &= np.isfinite(high) & np.isfinite(low) & np.isfinite(close)
    previous = close.shift(1).where(np.isfinite(close.shift(1)) & close.shift(1).gt(0))
    tr = np.maximum(high-low, np.maximum((high-previous).abs(), (low-previous).abs()))
    tr = tr.where(valid & previous.notna())
    return tr.rolling(window, min_periods=window).mean().shift(1)


def mask(frame, minimum):
    return np.ones(len(frame), dtype=bool) if minimum < 0 else frame.breakout_strength.ge(minimum-1e-12).to_numpy()


def band_codes(frame):
    return np.column_stack([mask(frame, t) for t in THRESHOLDS]).sum(axis=1)
