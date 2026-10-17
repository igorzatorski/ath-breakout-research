"""Lagged total-return momentum and fixed contemporaneous matching."""
import numpy as np


def lagged_momentum(returns):
    """At t compound t-251..t-21; require every scheduled session."""
    valid = np.isfinite(returns) & returns.ge(-1)
    positive = returns.gt(-1) & valid
    logs = np.log1p(returns.where(positive, 0))
    sums = logs.rolling(231, min_periods=231).sum().shift(21)
    count = valid.astype(int).rolling(231, min_periods=231).sum().shift(21)
    zero = returns.eq(-1).astype(int).rolling(231, min_periods=231).sum().shift(21)
    result = np.expm1(sums).where(count.eq(231))
    return result.mask(zero.gt(0) & count.eq(231), -1)


def match_momentum_controls(events, controls, k=5):
    """Same-day size/vol/momentum distances; no outcome data accepted."""
    from scipy.spatial import cKDTree

    controls = controls.loc[np.isfinite(controls.momentum)].sort_values("permno").reset_index(drop=True)
    if len(controls) < k:
        return {}
    coords = np.column_stack([np.log(controls.market_cap), np.log(controls.vol63), controls.momentum])
    scale = np.std(coords, axis=0)
    scale = np.where(scale > 1e-12, scale, 1.)
    limits = np.array([np.log(2), np.log(1.5), .10])
    radius = np.linalg.norm(limits / scale)
    tree = cKDTree(coords / scale)
    result = {}
    for row in events.itertuples():
        if not np.isfinite(row.momentum):
            continue
        point = np.array([np.log(row.market_cap), np.log(row.vol63), row.momentum])
        indices = tree.query_ball_point(point / scale, radius + 1e-12)
        z = controls.iloc[indices].copy()
        delta = coords[indices] - point
        keep = (np.abs(delta) <= limits + 1e-12).all(axis=1) & z.permco.ne(row.permco).to_numpy() & z.permno.ne(row.permno).to_numpy()
        z = z.loc[keep].copy()
        z["distance"] = ((delta[keep] / scale)**2).sum(axis=1)
        z = z.sort_values(["distance", "permno"]).drop_duplicates("permco").head(k)
        if len(z) == k:
            result[row.permno] = z.permno.astype(int).tolist()
    return result
