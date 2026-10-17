"""Fixed candidate neighborhood, overlap and shared-draw conditional contrasts."""
from itertools import product

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

DIMENSIONS = 'CVAB'
STATES = list(product(range(3), repeat=4))


def config_name(state):
    return ''.join(f'{name}{level}' for name, level in zip(DIMENSIONS, state))


def indicators(frame):
    age = frame.age_exact.fillna(frame.age_lower_bound)
    return {'C1': frame.contraction_42.le(.75+1e-12), 'C2': frame.contraction_63.le(.75+1e-12),
        'V1': frame.volume_ratio_63.ge(1.5-1e-12), 'V2': frame.volume_ratio_63.ge(2.-1e-12),
        'A1': age.ge(126), 'A2': age.ge(252),
        'B1': frame.breakout_strength.ge(.5-1e-12), 'B2': frame.breakout_strength.ge(1.-1e-12)}


def memberships(frame):
    individual = indicators(frame)
    columns = []
    for state in STATES:
        keep = np.ones(len(frame), bool)
        for name, level in zip(DIMENSIONS, state):
            if level:
                keep &= individual[f'{name}{level}'].to_numpy()
        columns.append(keep)
    return np.column_stack(columns)


def contrasts():
    index = {s: i for i, s in enumerate(STATES)}
    rows = []
    for i, state in enumerate(STATES[1:], 1):
        rows.append(dict(kind='baseline', parent=0, child=i, feature='', main=all(x in [0, 2] for x in state)))
    for i, state in enumerate(STATES):
        for dim, level in enumerate(state):
            if level == 0:
                for option in [1, 2]:
                    target = list(state)
                    target[dim] = option
                    rows.append(dict(kind='addition', parent=i, child=index[tuple(target)], feature=DIMENSIONS[dim],
                        main=option == 2 and all(x in [0, 2] for x in state)))
            if level == 1:
                target = list(state)
                target[dim] = 2
                rows.append(dict(kind='neighbor', parent=i, child=index[tuple(target)], feature=DIMENSIONS[dim], main=False))
    return pd.DataFrame(rows)


def bootstrap_means(frame, groups, sessions, block=252, draws=2000, seed=20261017):
    cal = pd.DatetimeIndex(sessions)
    dates = cal.get_indexer(frame.date)
    values = frame.excess_spy.to_numpy(float)
    if frame.empty or (dates < 0).any() or not np.isfinite(values).all() or not groups[:, 0].all():
        raise ValueError('Complete reference and supported dates required')
    company, names = pd.factorize(frame.permco, sort=True)
    if (company < 0).any() or not 1 <= block <= len(cal):
        raise ValueError('Supported companies and block required')
    n, nc, ng = len(cal), len(names), groups.shape[1]
    event, group = np.nonzero(groups)
    sm = csr_matrix((values[event], (group*n+dates[event], company[event])), shape=(ng*n, nc))
    cm = csr_matrix((np.ones(len(event)), (group*n+dates[event], company[event])), shape=(ng*n, nc))
    rng = np.random.default_rng(seed)
    lengths = np.minimum(block, n-np.arange(0, n, block))
    result = []
    for draw in range(draws):
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
        result.append(np.divide(num, den, out=np.full(ng, np.nan), where=den > 0))
        if (draw+1) % 500 == 0:
            print(f'  block{block}: {draw+1}/{draws} draws', flush=True)
    return np.asarray(result)


def contrast_intervals(points, samples, edges):
    parent, child = edges.parent.to_numpy(), edges.child.to_numpy()
    estimate = points[child]-points[parent]
    difference = samples[:, child]-samples[:, parent]
    families = {'main15': edges.kind.eq('baseline') & edges.main,
        'grid80': edges.kind.eq('baseline'), 'main_add32': edges.kind.eq('addition') & edges.main,
        'all404': np.ones(len(edges), bool)}
    radii, supports = {}, {}
    for name, keep in families.items():
        complete = np.isfinite(difference[:, keep]).all(axis=1)
        supports[name] = int(complete.sum())
        radii[name] = np.quantile(np.abs(difference[complete][:, keep]-estimate[keep]).max(axis=1), .95) if complete.mean() >= .95 else np.nan
    rows = []
    for i, edge in enumerate(edges.to_dict('records')):
        valid = difference[:, i][np.isfinite(difference[:, i])]
        bounds = np.quantile(valid, [.025, .975]) if len(valid) >= .95*len(samples) else [np.nan, np.nan]
        row = dict(**edge, parent_name=config_name(STATES[edge['parent']]), child_name=config_name(STATES[edge['child']]),
            estimate=estimate[i], lower95=bounds[0], upper95=bounds[1], valid_draws=len(valid))
        for name in families:
            radius = radii[name] if families[name][i] else np.nan
            row[f'{name}_lower'] = estimate[i]-radius
            row[f'{name}_upper'] = estimate[i]+radius
            row[f'{name}_complete_draws'] = supports[name]
        rows.append(row)
    return pd.DataFrame(rows)
