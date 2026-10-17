"""Fixed pre-window ATH anchors and past-only closing-price proximity."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

LENGTHS = [10, 21, 42, 63]
DEPTHS = [.05, .10, .15, .20]
CELLS = [(n, d) for n in LENGTHS for d in DEPTHS]


def proximity_features(prices, prior_ath, length):
    """Anchor before the first prior-window session; no moving ATH denominator."""
    clean = prices.where(np.isfinite(prices) & prices.gt(0))
    anchor = prior_ath.shift(length).where(lambda x: np.isfinite(x) & x.gt(0))
    low = clean.rolling(length, min_periods=length).min().shift(1)
    high = clean.rolling(length, min_periods=length).max().shift(1)
    return anchor, low, high, 1-low/anchor


def selected(frame, length, depth):
    if length == 0:
        return np.ones(len(frame), dtype=bool)
    upper = frame[f'upper_{length}'].to_numpy(bool)
    return upper if depth < 0 else upper & frame[f'depth_{length}'].le(depth+1e-12).to_numpy()


def joint_intervals(frame, sessions, block=252, draws=2000, seed=20261016):
    """Joint baseline, sixteen cells and four upper-only accounting references."""
    labels = [(0, 0.)]+CELLS+[(n, -1.) for n in LENGTHS]
    groups = np.column_stack([selected(frame, n, d) for n, d in labels])
    ng = len(labels)
    cal = pd.DatetimeIndex(sessions)
    n = len(cal)
    dates = cal.get_indexer(frame.date)
    values = frame.excess_spy.to_numpy(float)
    if frame.empty or (dates < 0).any() or not np.isfinite(values).all() or not 1 <= block <= n:
        raise ValueError('Complete outcomes and supported calendar required')
    company, names = pd.factorize(frame.permco, sort=True)
    if (company < 0).any():
        raise ValueError('Observed companies required')
    nc = len(names)
    event, group = np.nonzero(groups)
    sm = csr_matrix((values[event], (group*n+dates[event], company[event])), shape=(ng*n, nc))
    cm = csr_matrix((np.ones(len(event)), (group*n+dates[event], company[event])), shape=(ng*n, nc))
    counts = groups.sum(axis=0)
    point = np.divide(groups.T@values, counts, out=np.full(ng, np.nan), where=counts > 0)
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
        den = (cm@cw).reshape(ng, n)@tw
        num = (sm@cw).reshape(ng, n)@tw
        samples.append(np.divide(num, den, out=np.full(ng, np.nan), where=den > 0))
    samples = np.asarray(samples)
    diff = samples[:, 1:17]-samples[:, :1]
    estimates = point[1:17]-point[0]
    joint = np.isfinite(diff).all(axis=1)
    radius = np.quantile(np.abs(diff[joint]-estimates).max(axis=1), .95) if joint.sum() >= .95*draws else np.nan
    rows = []
    for j, (length, depth) in enumerate(labels):
        contrasts = [('level', j, None), ('minus_baseline', j, 0)]
        if 1 <= j <= 16:
            contrasts.append(('minus_anchor_only', j, 17+LENGTHS.index(length)))
        for contrast, a, b in contrasts:
            v = samples[:, a] if b is None else samples[:, a]-samples[:, b]
            estimate = point[a] if b is None else point[a]-point[b]
            valid = v[np.isfinite(v)]
            bounds = np.quantile(valid, [.025, .975]) if len(valid) >= .95*draws else [np.nan, np.nan]
            rows.append(dict(length=length, depth=depth, contrast=contrast, estimate=estimate,
                lower95=bounds[0], upper95=bounds[1], valid_draws=len(valid), block=block))
        if 1 <= j <= 16:
            rows.append(dict(length=length, depth=depth, contrast='minus_baseline_simultaneous16',
                estimate=estimates[j-1], lower95=estimates[j-1]-radius, upper95=estimates[j-1]+radius,
                valid_draws=int(joint.sum()), block=block))
    return rows
