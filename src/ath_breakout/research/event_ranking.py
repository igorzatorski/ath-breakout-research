"""Same-date composite scores and date-balanced resampling diagnostics."""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

MODELS = ['M', 'MV', 'MVC']


def percentile(values, dates):
    group = values.groupby(dates)
    return (group.rank(method='average')-.5)/group.transform('size')


def rank_events(frame):
    z = frame.copy()
    valid = np.isfinite(z[['momentum_6_1', 'volume_ratio_63', 'contraction_42']]).all(axis=1)
    z['ranking_features'] = valid
    pool = z.loc[valid]
    for name, raw in [('M', pool.momentum_6_1), ('V', pool.volume_ratio_63.clip(upper=2)), ('C', -pool.contraction_42)]:
        z.loc[valid, f'component_{name}'] = percentile(raw, pool.date)
    z['candidate_count'] = z.date.map(pool.groupby('date').size()).fillna(0).astype(int)
    z['score_M'] = z.component_M
    z['score_MV'] = (z.component_M+z.component_V)/2
    z['score_MVC'] = (z.component_M+z.component_V+z.component_C)/3
    for model in MODELS:
        z[f'rank_{model}'] = percentile(z.loc[valid, f'score_{model}'], z.loc[valid, 'date'])
        z[f'quintile_{model}'] = np.ceil(5*z[f'rank_{model}']).clip(1, 5)
    z['candidate_date_supported'] = valid & z.candidate_count.ge(5)
    return z


def common_dates(annual, top_only=False):
    supported = annual.loc[annual.candidate_date_supported]
    dates = pd.Index(supported.date.unique())
    for model in MODELS:
        observed = supported.groupby('date')[f'quintile_{model}'].agg(set)
        required = {5.} if top_only else {1., 2., 3., 4., 5.}
        dates = dates.intersection(observed.index[observed.map(lambda values: required.issubset(values))])
    return dates.sort_values()


def groups(frame, top_only=False):
    names, masks = ['reference'], [np.ones(len(frame), bool)]
    for model in MODELS:
        for q in ([5] if top_only else range(1, 6)):
            names.append(f'{model}_Q{q}')
            masks.append(frame[f'quintile_{model}'].eq(q).to_numpy())
    return names, np.column_stack(masks)


def contrast_matrix(names, top_only=False):
    rows, coefficients = [], []
    index = {name: i for i, name in enumerate(names)}

    def add(kind, label, terms):
        vector = np.zeros(len(names))
        for name, weight in terms:
            vector[index[name]] += weight
        rows.append(dict(kind=kind, label=label))
        coefficients.append(vector)
    for model in MODELS:
        add('top_vs_reference', f'{model}_top_minus_reference', [(f'{model}_Q5', 1), ('reference', -1)])
        if not top_only:
            add('spread', f'{model}_Q5_minus_Q1', [(f'{model}_Q5', 1), (f'{model}_Q1', -1)])
    for newer, older in [('MV', 'M'), ('MVC', 'M'), ('MVC', 'MV')]:
        add('incremental_top', f'{newer}_top_minus_{older}_top', [(f'{newer}_Q5', 1), (f'{older}_Q5', -1)])
        if not top_only:
            add('incremental_spread', f'{newer}_spread_minus_{older}_spread', [(f'{newer}_Q5', 1),
                (f'{newer}_Q1', -1), (f'{older}_Q5', -1), (f'{older}_Q1', 1)])
    if not top_only:
        for model in MODELS:
            for q in range(1, 5):
                add('adjacent', f'{model}_Q{q+1}_minus_Q{q}', [(f'{model}_Q{q+1}', 1), (f'{model}_Q{q}', -1)])
    return pd.DataFrame(rows), np.asarray(coefficients)


def balanced_draws(frame, membership, sessions, block, draws=2000, seed=20261017):
    dates = pd.DatetimeIndex(sorted(frame.date.unique()))
    date_id = dates.get_indexer(frame.date)
    calendar = pd.DatetimeIndex(sessions)
    positions = calendar.get_indexer(dates)
    company, labels = pd.factorize(frame.permco, sort=True)
    if (positions < 0).any() or (company < 0).any() or not 1 <= block <= len(calendar):
        raise ValueError('Supported companies, dates and block required')
    event, group = np.nonzero(membership)
    n, ng, nc = len(dates), membership.shape[1], len(labels)
    sm = csr_matrix((frame.excess_spy.to_numpy()[event], (group*n+date_id[event], company[event])), shape=(ng*n, nc))
    cm = csr_matrix((np.ones(len(event)), (group*n+date_id[event], company[event])), shape=(ng*n, nc))
    den = (cm@np.ones(nc)).reshape(ng, n)
    if (den <= 0).any():
        raise ValueError('Every evaluation date must support every group')
    points = ((sm@np.ones(nc)).reshape(ng, n)/den).mean(axis=1)
    rng = np.random.default_rng(seed)
    lengths = np.minimum(block, len(calendar)-np.arange(0, len(calendar), block))
    samples = []
    for _ in range(draws):
        starts = rng.integers(0, len(calendar), len(lengths))
        ends = starts+lengths
        delta = np.zeros(len(calendar)+1)
        np.add.at(delta, starts, 1)
        np.add.at(delta, np.minimum(ends, len(calendar)), -1)
        wrap = ends > len(calendar)
        delta[0] += wrap.sum()
        np.add.at(delta, ends[wrap]-len(calendar), -1)
        tw = np.cumsum(delta[:-1])[positions]
        cw = rng.exponential(size=nc)
        mean = (sm@cw).reshape(ng, n)/(cm@cw).reshape(ng, n)
        samples.append(mean@tw/tw.sum() if tw.sum() else np.full(ng, np.nan))
    return points, np.asarray(samples)


def intervals(points, samples, definitions, coefficients):
    estimates = coefficients@points
    values = samples@coefficients.T
    radii, support = {}, {}
    families = {'incremental3': definitions.kind.eq('incremental_top').to_numpy(), 'all': np.ones(len(definitions), bool)}
    for name, selected in families.items():
        complete = np.isfinite(values[:, selected]).all(axis=1)
        support[name] = int(complete.sum())
        radii[name] = np.quantile(np.abs(values[complete][:, selected]-estimates[selected]).max(axis=1), .95) if complete.mean() >= .95 else np.nan
    rows = []
    for j, definition in enumerate(definitions.to_dict('records')):
        valid = values[:, j][np.isfinite(values[:, j])]
        bounds = np.quantile(valid, [.025, .975]) if len(valid) >= .95*len(samples) else [np.nan]*2
        row = dict(**definition, estimate=estimates[j], lower95=bounds[0], upper95=bounds[1], valid_draws=len(valid))
        for name, selected in families.items():
            radius = radii[name] if selected[j] else np.nan
            row[f'{name}_lower'] = estimates[j]-radius
            row[f'{name}_upper'] = estimates[j]+radius
            row[f'{name}_complete_draws'] = support[name]
        rows.append(row)
    return pd.DataFrame(rows)
