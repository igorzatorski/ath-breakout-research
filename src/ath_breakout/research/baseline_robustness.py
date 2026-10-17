"""Annual-event concentration and explicitly approximate dependence diagnostics."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


def nonoverlap_ids(events, sessions, separation=252):
    """Greedily select by historical company, before inspecting any outcomes."""
    if not isinstance(separation, int) or separation < 1:
        raise ValueError("Separation must be a positive integer")
    if events.event_id.duplicated().any() or events.permco.isna().any():
        raise ValueError("Unique events and observed company identities required")
    cal = pd.DatetimeIndex(sessions)
    if cal.has_duplicates or not cal.is_monotonic_increasing:
        raise ValueError("Calendar must be unique and sorted")
    z = events.sort_values(["date", "permco", "permno", "event_id"])
    positions = cal.get_indexer(z.date)
    if (positions < 0).any():
        raise ValueError("Signal outside calendar")
    last, kept = {}, []
    for row, pos in zip(z.itertuples(), positions):
        if pos - last.get(row.permco, -np.inf) >= separation:
            kept.append(row.event_id)
            last[row.permco] = pos
    return kept


def contributions(frame, metric, identity):
    """Additive contribution to the event mean; no observations removed."""
    z = frame.loc[np.isfinite(frame[metric])]
    g = z.groupby(identity)[metric].agg(events="size", excess_sum="sum", mean="mean")
    g["contribution"] = g.excess_sum / len(z)
    g["event_share"] = g.events / len(z)
    g["positive_sum"] = z.loc[z[metric] > 0].groupby(identity)[metric].sum()
    g["negative_sum"] = z.loc[z[metric] < 0].groupby(identity)[metric].sum()
    return g.fillna(0).sort_values("contribution", ascending=False).reset_index()


def ratio_estimates(values, retained, weights):
    """Baseline, retained and difference using identical event weights."""
    sums = np.array([np.dot(weights, values), np.dot(weights * retained, values)])
    counts = np.array([weights.sum(), np.dot(weights, retained)])
    means = np.divide(sums, counts, out=np.full(2, np.nan), where=counts > 0)
    return np.array([means[0], means[1], means[1] - means[0]])


def crossed_intervals(frame, metric, sessions, block=252, draws=2000, seed=20261016):
    """Date blocks and crossed event-company/date blocks, not a calibrated alpha test."""
    z = frame.loc[np.isfinite(frame[metric])].copy()
    cal = pd.DatetimeIndex(sessions)
    n = len(cal)
    if not 1 <= block <= n or z.empty:
        raise ValueError("Nonempty sample and supported block length required")
    dates = cal.get_indexer(z.date)
    if (dates < 0).any():
        raise ValueError("Event outside calendar")
    companies, labels = pd.factorize(z.permco, sort=True)
    nc = len(labels)
    values = z[metric].to_numpy(float)
    retained = z.nonoverlap.to_numpy(float)
    mats = [csr_matrix((v, (dates, companies)), shape=(n, nc)) for v in
            [values, np.ones(len(z)), values * retained, retained]]
    daily = np.column_stack([np.asarray(m.sum(axis=1)).ravel() for m in mats])
    rng = np.random.default_rng(seed)
    estimates = {"date_blocks": [], "company_x_date_blocks": []}
    # Exactly n circular dates: the final sampled block is truncated.
    lengths = np.minimum(block, n - np.arange(0, n, block))
    for _ in range(draws):
        starts = rng.integers(0, n, len(lengths))
        ends = starts + lengths
        delta = np.zeros(n + 1)
        np.add.at(delta, starts, 1)
        np.add.at(delta, np.minimum(ends, n), -1)
        wrap = ends > n
        delta[0] += wrap.sum()
        np.add.at(delta, ends[wrap] - n, -1)
        time_weights = np.cumsum(delta[:-1])
        company_weights = rng.multinomial(nc, np.full(nc, 1 / nc))
        totals_date = time_weights @ daily
        totals_cross = np.array([time_weights @ (m @ company_weights) for m in mats])
        for name, t in [("date_blocks", totals_date),
                        ("company_x_date_blocks", totals_cross)]:
            if t[1] > 0 and t[3] > 0:
                b, r = t[0] / t[1], t[2] / t[3]
                estimates[name].append([b, r, r - b])
    point = ratio_estimates(values, retained, np.ones(len(z)))
    rows = []
    for method, results in estimates.items():
        if len(results) < draws * .95:
            raise ValueError("Too many bootstrap replicates lack retained observations")
        bounds = np.quantile(results, [.025, .975], axis=0)
        for i, variant in enumerate(["baseline", "nonoverlap", "change"]):
            rows.append(dict(method=method, block=block, variant=variant,
                             estimate=point[i], lower95=bounds[0, i],
                             upper95=bounds[1, i], valid_draws=len(results)))
    return rows
