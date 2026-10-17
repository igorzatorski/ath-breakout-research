"""Predeclared momentum windows and joint same-event lookback comparisons."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from ath_breakout.research.momentum_filter import GROUP_MATRIX, VARIANTS

LOOKBACKS = {"12_1": 252, "6_1": 126, "3_1": 63}


def momentum_excluding_recent(returns, lookback_sessions, skip_sessions=21):
    """At t, compound t-lookback+1 .. t-skip, inclusive; no missing sessions."""
    if (not isinstance(lookback_sessions, int) or not isinstance(skip_sessions, int)
            or skip_sessions < 0 or lookback_sessions <= skip_sessions):
        raise ValueError("Integer lookback greater than nonnegative skip required")
    window = lookback_sessions - skip_sessions
    valid = np.isfinite(returns) & returns.ge(-1)
    logs = np.log1p(returns.where(valid & returns.gt(-1), 0))
    sums = logs.rolling(window, min_periods=window).sum().shift(skip_sessions)
    count = valid.astype(int).rolling(window, min_periods=window).sum().shift(skip_sessions)
    zeros = returns.eq(-1).astype(int).rolling(window, min_periods=window).sum().shift(skip_sessions)
    return np.expm1(sums).where(count.eq(window)).mask(zeros.gt(0) & count.eq(window), -1)


def lookback_means(sums, counts):
    """Three lookbacks by nine same-definition groups/filters."""
    numerator = np.asarray(sums).reshape(3, 5) @ GROUP_MATRIX.T
    denominator = np.asarray(counts).reshape(3, 5) @ GROUP_MATRIX.T
    return np.divide(numerator, denominator, out=np.full((3, 9), np.nan), where=denominator > 0)


def joint_lookback_intervals(frame, metric, sessions, block=252, draws=2000, seed=20261016):
    """Same company/date weights for every lookback, group and contrast."""
    if frame.empty or not np.isfinite(frame[metric]).all():
        raise ValueError("Complete nonempty metric sample required")
    cal = pd.DatetimeIndex(sessions)
    n = len(cal)
    if not 1 <= block <= n:
        raise ValueError("Unsupported block length")
    positions = cal.get_indexer(frame.date)
    if (positions < 0).any():
        raise ValueError("Date outside calendar")
    company, labels = pd.factorize(frame.permco, sort=True)
    nc = len(labels)
    q = np.column_stack([frame[f"quintile_{label}"].to_numpy(int)-1 for label in LOOKBACKS])
    if (q < 0).any() or (q > 4).any():
        raise ValueError("Complete valid quintiles required")
    values = frame[metric].to_numpy(float)
    group = np.concatenate([q[:, i] + 5*i for i in range(3)])
    row = group*n + np.tile(positions, 3)
    column = np.tile(company, 3)
    sm = csr_matrix((np.tile(values, 3), (row, column)), shape=(15*n, nc))
    cm = csr_matrix((np.ones(3*len(frame)), (row, column)), shape=(15*n, nc))
    point = lookback_means(np.bincount(group, weights=np.tile(values, 3), minlength=15),
                           np.bincount(group, minlength=15))
    lengths = np.minimum(block, n-np.arange(0, n, block))
    rng = np.random.default_rng(seed)
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
        samples.append(lookback_means((sm @ cw).reshape(15, n) @ tw,
                                      (cm @ cw).reshape(15, n) @ tw))
    samples = np.asarray(samples)
    baseline = samples[:, 0, 0]
    baseline_point = point[0, 0]
    rows = []

    def add(label, variant, comparison, estimate, values):
        valid = values[np.isfinite(values)]
        if len(valid) < .95*draws:
            raise ValueError(f"Insufficient bootstrap support: {label} {variant}")
        lo, hi = np.quantile(valid, [.025, .975])
        rows.append(dict(lookback=label, variant=variant, comparison=comparison,
                         estimate=estimate, lower95=lo, upper95=hi,
                         valid_draws=len(valid), block=block))

    for i, label in enumerate(LOOKBACKS):
        for j, variant in enumerate(VARIANTS):
            add(label, variant, "level", point[i, j], samples[:, i, j])
            add(label, variant, "minus_baseline", point[i, j]-baseline_point,
                samples[:, i, j]-baseline)
            if i and j >= 6:
                add(label, variant, "minus_12_1_same_threshold", point[i, j]-point[0, j],
                    samples[:, i, j]-samples[:, 0, j])
        add(label, "Q5_minus_Q1", "spread", point[i, 5]-point[i, 1],
            samples[:, i, 5]-samples[:, i, 1])
    contrasts = samples[:, :, 6:9]-baseline[:, None, None]
    p = point[:, 6:9]-baseline_point
    valid = np.isfinite(contrasts).all(axis=(1, 2))
    if valid.sum() < .95*draws:
        raise ValueError("Insufficient joint nine-contrast support")
    radius = np.quantile(np.abs(contrasts[valid]-p).max(axis=(1, 2)), .95)
    for i, label in enumerate(LOOKBACKS):
        for j, variant in enumerate(VARIANTS[6:9]):
            rows.append(dict(lookback=label, variant=variant, comparison="minus_baseline_simultaneous9",
                             estimate=p[i, j], lower95=p[i, j]-radius,
                             upper95=p[i, j]+radius, valid_draws=int(valid.sum()), block=block))
    return rows
