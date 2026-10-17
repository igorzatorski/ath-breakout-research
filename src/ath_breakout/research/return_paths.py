"""Descriptive closing-wealth paths; no exit simulation or hindsight trading."""
import numpy as np
import pandas as pd

PROFIT_LEVELS = [.5, 1., 2., 3.]
LOSS_LEVELS = [.1, .2, .3]
BIN_EDGES = [-np.inf, -.5, -.2, 0., .2, .5, 1., 2., 3., np.inf]
BIN_LABELS = ['<-50%', '-50 to <-20%', '-20 to <0%', '0 to <20%', '20 to <50%',
              '50 to <100%', '100 to <200%', '200 to <300%', '>=300%']


def path_metrics(wealth):
    """Entry-based adverse/favorable excursions and first close-threshold hits."""
    w = np.asarray(wealth, dtype=float)
    if w.ndim != 2 or w.shape[1] == 0 or not np.isfinite(w).all() or (w < 0).any():
        raise ValueError('Finite nonnegative event-row wealth paths required')
    peak = np.maximum.accumulate(np.maximum(w, 1.), axis=1)
    result = dict(mae=np.minimum(w.min(axis=1), 1.)-1,
                  mfe=np.maximum(w.max(axis=1), 1.)-1,
                  max_drawdown=(w/peak-1).min(axis=1))
    for level in PROFIT_LEVELS:
        key = str(int(level*100))
        hits = w >= 1+level-1e-12
        reached = hits.any(axis=1)
        first = hits.argmax(axis=1)
        result[f'ever_{key}'] = reached
        result[f'first_{key}'] = np.where(reached, first+1, np.nan)
        before = np.arange(w.shape[1])[None, :] < first[:, None]
        low = np.minimum(np.where(before, w, 1.).min(axis=1), 1.)-1
        result[f'mae_before_{key}'] = np.where(reached, low, np.nan)
    return pd.DataFrame(result)


def distribution(frame, column):
    x = frame[column]
    labels = pd.cut(x, BIN_EDGES, labels=BIN_LABELS, right=False)
    rows = []
    for label in BIN_LABELS:
        v = x.loc[labels.eq(label)]
        rows.append(dict(bin=label, events=len(v), fraction=len(v)/len(x),
                         mean=v.mean(), contribution=v.sum()/len(x)))
    return rows
