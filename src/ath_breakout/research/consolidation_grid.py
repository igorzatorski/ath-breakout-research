"""Past-only close-range features and joint exploratory grid uncertainty."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

LENGTHS = [10, 21, 42, 63, 126]
WIDTHS = [.05, .10, .15, .20, .30]
CELLS = [(length, width) for length in LENGTHS for width in WIDTHS]


def past_width(prices, length):
    """Full scheduled prior window, excluding the current observation."""
    clean = prices.where(np.isfinite(prices) & prices.gt(0))
    return (clean.rolling(length, min_periods=length).max()
            / clean.rolling(length, min_periods=length).min()-1).shift(1)


def membership(frame):
    return np.column_stack([np.ones(len(frame), dtype=bool)] +
        [frame[f'width_{length}'].le(width+1e-12).to_numpy() for length, width in CELLS])


def grid_intervals(frame, sessions, block=252, draws=2000, seed=20261016):
    """Joint event-company and circular signal-date block bootstrap."""
    cal = pd.DatetimeIndex(sessions)
    n = len(cal)
    dates = cal.get_indexer(frame.date)
    if frame.empty or (dates < 0).any() or not 1 <= block <= n:
        raise ValueError('Nonempty frame and supported calendar required')
    groups = membership(frame)
    values = frame.excess_spy.to_numpy(float)
    if not np.isfinite(values).all() or frame.permco.isna().any():
        raise ValueError('Complete outcomes and company identifiers required')
    company, names = pd.factorize(frame.permco, sort=True)
    nc = len(names)
    event, group = np.nonzero(groups)
    shape = (26*n, nc)
    sm = csr_matrix((values[event], (group*n+dates[event], company[event])), shape=shape)
    cm = csr_matrix((np.ones(len(event)), (group*n+dates[event], company[event])), shape=shape)
    counts = groups.sum(axis=0)
    point = np.divide(groups.T@values, counts, out=np.full(26, np.nan), where=counts > 0)
    rng = np.random.default_rng(seed)
    lengths = np.minimum(block, n-np.arange(0, n, block))
    samples = []
    for _ in range(draws):
        starts = rng.integers(0, n, len(lengths))
        ends = starts+lengths
        delta = np.zeros(n+1)
        np.add.at(delta, starts, 1)
        np.add.at(delta, np.minimum(ends, n), -1)
        wrap = ends > n
        delta[0] += wrap.sum()
        np.add.at(delta, ends[wrap]-n, -1)
        tw = np.cumsum(delta[:-1])
        cw = rng.multinomial(nc, np.full(nc, 1/nc))
        den = (cm@cw).reshape(26, n)@tw
        num = (sm@cw).reshape(26, n)@tw
        samples.append(np.divide(num, den, out=np.full(26, np.nan), where=den > 0))
    samples = np.asarray(samples)
    contrasts = samples[:, 1:]-samples[:, :1]
    estimates = point[1:]-point[0]
    joint = np.isfinite(contrasts).all(axis=1)
    radius = np.quantile(np.abs(contrasts[joint]-estimates).max(axis=1), .95) if joint.sum() >= .95*draws else np.nan
    rows = []
    for j, (length, width) in enumerate([(0, 0.)]+CELLS):
        for contrast in ['level', 'minus_baseline']:
            v = samples[:, j] if contrast == 'level' else samples[:, j]-samples[:, 0]
            valid = v[np.isfinite(v)]
            bounds = np.quantile(valid, [.025, .975]) if len(valid) >= .95*draws else [np.nan, np.nan]
            rows.append(dict(length=length, width=width, contrast=contrast, estimate=point[j]-(point[0] if contrast == 'minus_baseline' else 0),
                lower95=bounds[0], upper95=bounds[1], valid_draws=len(valid), block=block))
        if j:
            rows.append(dict(length=length, width=width, contrast='minus_baseline_simultaneous25', estimate=estimates[j-1],
                lower95=estimates[j-1]-radius, upper95=estimates[j-1]+radius, valid_draws=int(joint.sum()), block=block))
    return rows
