"""Closing-wealth excursions for descriptive long-horizon event studies."""
import numpy as np


def wealth_excursions(wealth):
    """Each row is one event; initial investment 1 is included in the peak."""
    peaks = np.maximum.accumulate(np.maximum(wealth, 1), axis=1)
    return np.minimum(wealth.min(axis=1), 1)-1, (wealth/peaks-1).min(axis=1)


def closing_wealth_paths(opens, closes, returns, terminals, entry_rows, columns, horizon):
    """Return event-row paths, retaining terminal wealth as cash after its Y day."""
    rows = entry_rows[:, None]+np.arange(horizon)[None, :]
    cols = columns[:, None]
    factor = 1+returns[rows, cols]
    term = terminals[rows, cols]
    after_terminal = np.cumsum(term, axis=1)-term > 0
    factor = np.where(after_terminal, 1, factor)
    factor[:, 0] = closes[entry_rows, columns]/opens[entry_rows, columns]
    return np.cumprod(factor, axis=1)
