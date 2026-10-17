"""Signal-day closing location with explicit invalid and zero-range handling."""
import numpy as np
import pandas as pd

THRESHOLDS = [.50, .70, .85, .95]


def closing_location(prices):
    h, l, c = prices.high, prices.low, prices.close
    finite = np.isfinite(h) & np.isfinite(l) & np.isfinite(c) & h.gt(0) & l.gt(0) & c.gt(0)
    consistent = h.ge(l) & c.ge(l) & c.le(h)
    flat = finite & consistent & h.eq(l)
    valid = finite & consistent & h.gt(l)
    status = pd.Series(np.select([~finite, finite & ~consistent, flat],
        ['missing_or_nonpositive', 'inconsistent_ohlc', 'zero_range'], default='ok'), index=prices.index)
    q = ((c-l)/(h-l)).where(valid)
    return pd.DataFrame({'close_quality': q, 'quality_status': status}, index=prices.index)


def mask(frame, threshold):
    return np.ones(len(frame), dtype=bool) if threshold < 0 else frame.close_quality.ge(threshold-1e-12).to_numpy()


def band_codes(frame):
    """Disjoint bands use the same registered boundary tolerance as filters."""
    return np.column_stack([mask(frame, t) for t in THRESHOLDS]).sum(axis=1)
