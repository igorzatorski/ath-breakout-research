"""Joint exploratory uncertainty for a baseline and a registered filter family."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


def joint_grid_intervals(frame, groups, labels, sessions, block=252, draws=2000, seed=20261016):
    """Approximate event-company/date-block bands; labels include the baseline."""
    groups = np.asarray(groups, dtype=bool)
    if groups.shape != (len(frame), len(labels)) or not groups[:, 0].all():
        raise ValueError('Baseline membership and one label per group required')
    cal = pd.DatetimeIndex(sessions)
    n, ng = len(cal), len(labels)
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
    diff = samples[:, 1:]-samples[:, :1]
    estimates = point[1:]-point[0]
    joint = np.isfinite(diff).all(axis=1)
    radius = np.quantile(np.abs(diff[joint]-estimates).max(axis=1), .95) if joint.sum() >= .95*draws else np.nan
    rows = []
    for j, label in enumerate(labels):
        for contrast in ['level', 'minus_baseline']:
            values = samples[:, j] if contrast == 'level' else samples[:, j]-samples[:, 0]
            valid = values[np.isfinite(values)]
            bounds = np.quantile(valid, [.025, .975]) if len(valid) >= .95*draws else [np.nan, np.nan]
            rows.append(dict(**label, contrast=contrast, estimate=point[j]-(point[0] if contrast == 'minus_baseline' else 0),
                lower95=bounds[0], upper95=bounds[1], valid_draws=len(valid), block=block))
        if j:
            rows.append(dict(**label, contrast=f'minus_baseline_simultaneous{ng-1}', estimate=estimates[j-1],
                lower95=estimates[j-1]-radius, upper95=estimates[j-1]+radius, valid_draws=int(joint.sum()), block=block))
    return rows
