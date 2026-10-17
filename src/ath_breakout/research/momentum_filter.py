"""Contemporaneous momentum ranks and joint exploratory filter comparisons."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

VARIANTS = ["baseline", "Q1", "Q2", "Q3", "Q4", "Q5", "top60", "top40", "top20"]
GROUP_MATRIX = np.array([[1, 1, 1, 1, 1], *np.eye(5).tolist(),
                         [0, 0, 1, 1, 1], [0, 0, 0, 1, 1], [0, 0, 0, 0, 1]])


def rank_momentum(pool):
    """Mid-distribution rank within each date's observed eligible PERMNO pool."""
    if pool.duplicated(["date", "permno"]).any():
        raise ValueError("Duplicate eligible security/date")
    z = pool.loc[np.isfinite(pool.momentum)].copy()
    z["rank_population"] = z.groupby("date").momentum.transform("size")
    z["momentum_percentile"] = (
        z.groupby("date").momentum.rank(method="average") - .5
    ) / z.rank_population
    z["quintile"] = quintiles(z.momentum_percentile)
    return z


def quintiles(percentiles):
    """Right-closed quintiles; equal feature values remain in the same group."""
    p = np.asarray(percentiles, dtype=float)
    if (~np.isfinite(p)).any() or (p < 0).any() or (p > 1).any():
        raise ValueError("Finite percentiles in [0, 1] required")
    return np.ceil(p * 5).clip(1, 5).astype(int)


def variant_mask(frame, variant):
    if variant == "baseline":
        return np.ones(len(frame), dtype=bool)
    if variant.startswith("Q") and variant in VARIANTS:
        return frame.quintile.eq(int(variant[1])).to_numpy()
    if variant in ["top60", "top40", "top20"]:
        return frame.quintile.ge({"top60": 3, "top40": 4, "top20": 5}[variant]).to_numpy()
    raise ValueError("Unknown variant")


def grouped_means(sums, counts):
    """Means for baseline, disjoint quintiles and nested fixed filters."""
    numerator = GROUP_MATRIX @ sums
    denominator = GROUP_MATRIX @ counts
    return np.divide(numerator, denominator, out=np.full(9, np.nan), where=denominator > 0)


def joint_filter_intervals(frame, metric, sessions, block=252, draws=2000, seed=20261016):
    """Crossed company/calendar bootstrap, all filters sharing each draw."""
    if frame.empty or not np.isfinite(frame[metric]).all():
        raise ValueError("Nonempty complete metric sample required")
    cal = pd.DatetimeIndex(sessions)
    n = len(cal)
    if block < 1 or block > n:
        raise ValueError("Unsupported block")
    positions = cal.get_indexer(frame.date)
    if (positions < 0).any():
        raise ValueError("Event outside calendar")
    company, labels = pd.factorize(frame.permco, sort=True)
    nc = len(labels)
    q = frame.quintile.to_numpy(int) - 1
    if (q < 0).any() or (q > 4).any():
        raise ValueError("Invalid quintile")
    values = frame[metric].to_numpy(float)
    row = q * n + positions
    sm = csr_matrix((values, (row, company)), shape=(5 * n, nc))
    cm = csr_matrix((np.ones(len(frame)), (row, company)), shape=(5 * n, nc))
    point = grouped_means(np.bincount(q, weights=values, minlength=5),
                          np.bincount(q, minlength=5))
    lengths = np.minimum(block, n - np.arange(0, n, block))
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(draws):
        starts = rng.integers(0, n, len(lengths))
        ends = starts + lengths
        delta = np.zeros(n + 1)
        np.add.at(delta, starts, 1)
        np.add.at(delta, np.minimum(ends, n), -1)
        wrap = ends > n
        delta[0] += wrap.sum()
        np.add.at(delta, ends[wrap] - n, -1)
        tw = np.cumsum(delta[:-1])
        cw = rng.multinomial(nc, np.full(nc, 1 / nc))
        sums = (sm @ cw).reshape(5, n) @ tw
        counts = (cm @ cw).reshape(5, n) @ tw
        samples.append(grouped_means(sums, counts))
    samples = np.array(samples)
    rows = []
    for i, name in enumerate(VARIANTS):
        for comparison, p, v in [("level", point[i], samples[:, i]),
                                 ("minus_baseline", point[i]-point[0], samples[:, i]-samples[:, 0])]:
            valid = v[np.isfinite(v)]
            if len(valid) < .95 * draws:
                raise ValueError("Insufficient valid group bootstrap draws")
            lo, hi = np.quantile(valid, [.025, .975])
            rows.append(dict(variant=name, comparison=comparison, estimate=p,
                             lower95=lo, upper95=hi, valid_draws=len(valid), block=block))
    d = samples[:, 5] - samples[:, 1]
    valid = d[np.isfinite(d)]
    if len(valid) < .95 * draws:
        raise ValueError("Insufficient Q5-Q1 observations")
    lo, hi = np.quantile(valid, [.025, .975])
    rows.append(dict(variant="Q5_minus_Q1", comparison="spread", estimate=point[5]-point[1],
                     lower95=lo, upper95=hi, valid_draws=len(valid), block=block))
    # Approximate simultaneous band for the three predeclared filter contrasts.
    contrasts = samples[:, 6:9] - samples[:, [0]]
    p = point[6:9] - point[0]
    valid = np.isfinite(contrasts).all(axis=1)
    radius = np.quantile(np.abs(contrasts[valid] - p).max(axis=1), .95)
    for i, name in enumerate(VARIANTS[6:9]):
        rows.append(dict(variant=name, comparison="minus_baseline_simultaneous3",
                         estimate=p[i], lower95=p[i]-radius, upper95=p[i]+radius,
                         valid_draws=int(valid.sum()), block=block))
    return rows
