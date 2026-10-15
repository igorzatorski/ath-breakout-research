"""Vectorized event returns and contemporaneous size/volatility matching."""
import numpy as np


def match_controls(events, controls, k=5):
    """Return fixed same-day control IDs; never inspect future prices/returns."""
    from scipy.spatial import cKDTree

    if len(controls) < k or events.empty:
        return {}
    controls = controls.sort_values("permno").reset_index(drop=True)
    coordinates = np.column_stack([np.log(controls.market_cap), np.log(controls.vol63)])
    scale = np.std(coordinates, axis=0)
    scale = np.where(scale > 1e-12, scale, 1.)
    tree = cKDTree(coordinates / scale)
    result = {}
    radius = np.sqrt((np.log(2)/scale[0])**2 + (np.log(1.5)/scale[1])**2)
    for row in events.itertuples():
        point = np.log([row.market_cap, row.vol63])
        indices = tree.query_ball_point(point/scale, radius + 1e-12)
        z = controls.iloc[indices].copy()
        z = z.loc[z.permco.ne(row.permco) & z.permno.ne(row.permno)
                  & np.log(z.market_cap/row.market_cap).abs().le(np.log(2)+1e-12)
                  & np.log(z.vol63/row.vol63).abs().le(np.log(1.5)+1e-12)]
        if len(z) < k:
            continue
        z["distance"] = (((np.column_stack([np.log(z.market_cap), np.log(z.vol63)]) - point)/scale)**2).sum(axis=1)
        z = z.sort_values(["distance", "permno"]).drop_duplicates("permco").head(k)
        if len(z) == k:
            result[row.permno] = z.permno.astype(int).tolist()
    return result


def forward_arrays(opens, closes, returns, terminals, entry_rows, columns, horizon, available_end):
    """Return wealth for arbitrary panel entries; terminal rows truncate the path."""
    rows, cols = closes.shape
    e = np.asarray(entry_rows, int)
    c = np.asarray(columns, int)
    end = e + horizon - 1
    in_bounds = (e >= 0) & (end < rows) & (end <= available_end)
    safe_e = np.clip(e, 0, rows-1)
    safe_end = np.clip(end, 0, rows-1)
    indices = np.arange(rows)[:, None]
    next_terminal = np.minimum.accumulate(np.where(terminals, indices, rows)[::-1], axis=0)[::-1]
    later = next_terminal[np.minimum(safe_e+1, rows-1), c]
    finish = np.minimum(safe_end, later)
    invalid = (~np.isfinite(returns) | (returns < -1)
               | ((~np.isfinite(closes) | (closes <= 0)) & ~terminals))
    factor = 1+returns
    logs = np.zeros_like(factor)
    np.log(factor, out=logs, where=np.isfinite(factor) & (factor > 0))
    prefix_log = np.vstack([np.zeros(cols), np.cumsum(logs, axis=0)])
    prefix_bad = np.vstack([np.zeros(cols, dtype=int), np.cumsum(invalid, axis=0)])
    prefix_zero = np.vstack([np.zeros(cols, dtype=int), np.cumsum(factor == 0, axis=0)])
    bad = prefix_bad[finish+1, c] - prefix_bad[safe_e+1, c]
    zero = prefix_zero[finish+1, c] - prefix_zero[safe_e+1, c]
    entry_valid = (np.isfinite(opens[safe_e,c]) & (opens[safe_e,c] > 0)
                   & np.isfinite(closes[safe_e,c]) & (closes[safe_e,c] > 0) & ~terminals[safe_e,c])
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        wealth = closes[safe_e,c]/opens[safe_e,c] * np.exp(prefix_log[finish+1,c]-prefix_log[safe_e+1,c])
    wealth[zero > 0] = 0
    valid = in_bounds & entry_valid & (bad == 0) & np.isfinite(wealth)
    result = np.where(valid, wealth-1, np.nan)
    status = np.where(~in_bounds, "censored", np.where(~entry_valid, "missing_entry", np.where((bad != 0) | ~np.isfinite(wealth), "invalid_path", "ok")))
    return result, status, valid & (later <= safe_end)


def moving_block_interval(frame, column, block=126, draws=2000):
    """Event-weighted mean via daily sum/count blocks; no independent-event SE."""
    z = frame.loc[frame[column].notna()].copy()
    if z.empty:
        return np.nan, np.nan
    from ath_breakout.data.market_calendar import valid_nyse_sessions
    sessions = valid_nyse_sessions(frame.date.min(), frame.date.max())
    aggregates = z.groupby("date")[column].agg(["sum", "count"]).reindex(sessions, fill_value=0)
    n = len(aggregates)
    block = min(block, n)
    values = aggregates.to_numpy(float)
    extended = np.concatenate([values, values[:block-1]], axis=0)
    prefix = np.vstack([np.zeros(2), np.cumsum(extended, axis=0)])
    block_sums = prefix[np.arange(n)+block] - prefix[np.arange(n)]
    rng = np.random.default_rng(20261015)
    estimates = []
    for _ in range(draws):
        sample = block_sums[rng.integers(0, n, size=int(np.ceil(n/block)))].sum(axis=0)
        if sample[1]:
            estimates.append(sample[0]/sample[1])
    return tuple(np.quantile(estimates, [.025, .975]))
