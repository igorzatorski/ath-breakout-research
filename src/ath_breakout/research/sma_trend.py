"""Signal-close SMA positions and two fixed trend alignments."""
import numpy as np

WINDOWS = [20, 50, 100, 200]
FILTERS = ['price_gt20', 'price_gt50', 'price_gt100', 'price_gt200', 'sma100_gt200', 'sma50_gt100_gt200']


def signal_sma(prices, window):
    return prices.rolling(window, min_periods=window).mean()


def greater(a, b):
    return (a-b) > 1e-12*np.maximum(np.abs(a), np.abs(b))


def memberships(frame):
    result = {f'price_gt{n}': greater(frame.signal_close, frame[f'sma_{n}']) for n in WINDOWS}
    result['sma100_gt200'] = greater(frame.sma_100, frame.sma_200)
    result['sma50_gt100_gt200'] = greater(frame.sma_50, frame.sma_100) & result['sma100_gt200']
    return result


def mask(frame, name):
    return np.ones(len(frame), dtype=bool) if name == 'reference' else frame[name].to_numpy(bool)
