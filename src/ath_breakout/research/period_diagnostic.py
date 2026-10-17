"""Exact descriptive decompositions of period mean changes, not causal effects."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

PERIODS = ["early", "middle", "recent"]


def period_labels(dates):
    years = pd.to_datetime(dates).dt.year
    return pd.Series(np.select([years <= 2009, years <= 2017], ["early", "middle"],
                               default="recent"), index=dates.index)


def additive_groups(frame, group, metric):
    """Each group's additive contribution to its period's total event mean."""
    z = frame.loc[np.isfinite(frame[metric])]
    result = z.groupby(["period", group], observed=True)[metric].agg(
        events="size", value_sum="sum", mean="mean").reset_index()
    totals = z.groupby("period", observed=True).size()
    result["weight"] = result.period.map(totals).astype(float)
    result["weight"] = result.events / result.weight
    result["contribution"] = result.weight * result["mean"]
    return result


def mix_within_decomposition(frame, group, metric, old="early", new="recent"):
    """Symmetric Kitagawa on shared support, plus explicit one-sided cells."""
    stats = additive_groups(frame, group, metric)
    a = stats.loc[stats.period.eq(old)].set_index(group)
    b = stats.loc[stats.period.eq(new)].set_index(group)
    labels = a.index.union(b.index)
    result = pd.DataFrame(index=labels)
    result["old_events"] = a.events.reindex(labels, fill_value=0)
    result["new_events"] = b.events.reindex(labels, fill_value=0)
    result["old_weight"] = a.weight.reindex(labels, fill_value=0)
    result["new_weight"] = b.weight.reindex(labels, fill_value=0)
    result["old_mean"] = a["mean"].reindex(labels)
    result["new_mean"] = b["mean"].reindex(labels)
    shared = result.old_events.gt(0) & result.new_events.gt(0)
    result["shared"] = shared
    result["mix"] = 0.
    result["within"] = 0.
    result["one_sided_support"] = 0.
    result.loc[shared, "mix"] = ((result.new_weight-result.old_weight) *
                                  (result.new_mean+result.old_mean)/2)[shared]
    result.loc[shared, "within"] = ((result.new_mean-result.old_mean) *
                                     (result.new_weight+result.old_weight)/2)[shared]
    result.loc[~shared, "one_sided_support"] = (
        result.new_weight * result.new_mean.fillna(0)
        - result.old_weight * result.old_mean.fillna(0))[~shared]
    result["total_change"] = result["mix"]+result["within"]+result.one_sided_support
    expected = frame.loc[frame.period.eq(new), metric].mean() - frame.loc[frame.period.eq(old), metric].mean()
    if not np.isclose(result.total_change.sum(), expected, atol=1e-12):
        raise ValueError("Decomposition does not reconcile")
    return result.reset_index()


def period_change_intervals(frame, sessions, block=252, draws=2000, seed=20261016):
    """Joint crossed weights for stock/SPY/excess and historical-period changes."""
    metrics = ["stock_return", "spy_return", "excess_spy"]
    if frame.empty or not np.isfinite(frame[metrics]).all().all():
        raise ValueError("Complete event returns required")
    cal = pd.DatetimeIndex(sessions)
    n = len(cal)
    dates = cal.get_indexer(frame.date)
    if (dates < 0).any() or not 1 <= block <= n:
        raise ValueError("Unsupported calendar")
    companies, names = pd.factorize(frame.permco, sort=True)
    nc = len(names)
    period = pd.Categorical(frame.period, categories=PERIODS).codes.astype(np.int64)
    if (period < 0).any():
        raise ValueError("Unknown period")
    matrices = [csr_matrix((frame[metric], (period*n+dates, companies)), shape=(3*n, nc))
                for metric in metrics]
    counts = csr_matrix((np.ones(len(frame)), (period*n+dates, companies)), shape=(3*n, nc))
    points = frame.groupby("period", observed=True)[metrics].mean().reindex(PERIODS).to_numpy()
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
        denominator = (counts @ cw).reshape(3, n) @ tw
        sums = np.column_stack([(m @ cw).reshape(3, n) @ tw for m in matrices])
        samples.append(np.divide(sums, denominator[:, None], out=np.full((3, 3), np.nan),
                                 where=denominator[:, None] > 0))
    samples = np.asarray(samples)
    rows = []
    for j, metric in enumerate(metrics):
        for i, period_name in enumerate(PERIODS):
            values = samples[:, i, j]
            valid = values[np.isfinite(values)]
            if len(valid) < .95*draws:
                raise ValueError("Insufficient period bootstrap support")
            lo, hi = np.quantile(valid, [.025, .975])
            rows.append(dict(metric=metric, contrast=period_name, estimate=points[i, j],
                             lower95=lo, upper95=hi, block=block, valid_draws=len(valid)))
        values = samples[:, 2, j]-samples[:, 0, j]
        valid = values[np.isfinite(values)]
        lo, hi = np.quantile(valid, [.025, .975])
        rows.append(dict(metric=metric, contrast="recent_minus_early", estimate=points[2, j]-points[0, j],
                         lower95=lo, upper95=hi, block=block, valid_draws=len(valid)))
    return rows
