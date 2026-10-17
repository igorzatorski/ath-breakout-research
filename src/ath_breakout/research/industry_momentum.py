"""Effective-dated CRSP SIC, frozen FF12 groups and within-industry ranks."""
import re

import numpy as np
import pandas as pd

THRESHOLDS = [.5, .7, .8]
MIN_PEERS = 20


def sic_mapping(text):
    mapping = np.full(10000, 12, dtype=int)
    names = {}
    group = None
    for line in text.splitlines():
        header = re.match(r'^\s*(\d{1,2})\s+([A-Za-z]+)\s+', line)
        interval = re.match(r'^\s*(\d{4})-(\d{4})\s*$', line)
        if header:
            group = int(header[1])
            names[group] = header[2]
        elif interval:
            if group is None:
                raise ValueError('SIC interval before industry header')
            mapping[int(interval[1]):int(interval[2])+1] = group
    if set(names) != set(range(1, 13)):
        raise ValueError('Expected official twelve-industry mapping')
    mapping[:100] = 0
    mapping[9999] = 0
    return mapping, names


def prepare_history(frame):
    h = frame.copy()
    h['permno'] = h.permno.astype('int64')
    h['effective_from'] = pd.to_datetime(h.effective_from)
    h['effective_to'] = pd.to_datetime(h.effective_to)
    h = h.sort_values(['permno', 'effective_from', 'effective_to'])
    if h[['effective_from', 'effective_to']].isna().any().any() or h.effective_from.gt(h.effective_to).any():
        raise ValueError('Invalid effective intervals')
    previous_end = h.groupby('permno').effective_to.shift()
    if h.effective_from.le(previous_end).any():
        raise ValueError('Overlapping classification intervals')
    return h


def attach_industry(pool, history, mapping):
    q = pool.copy()
    q['permno'] = q.permno.astype('int64')
    q['_order'] = np.arange(len(q))
    z = pd.merge_asof(q.sort_values('date'), history.sort_values('effective_from'),
        left_on='date', right_on='effective_from', by='permno', direction='backward')
    in_interval = z.effective_from.notna() & z.date.le(z.effective_to)
    code = pd.to_numeric(z.siccd, errors='coerce')
    valid = in_interval & code.between(100, 9998) & code.eq(np.floor(code))
    z['industry'] = 0
    z.loc[valid, 'industry'] = mapping[code.loc[valid].astype(int)]
    z['classification_status'] = np.where(valid, 'classified', np.where(in_interval, 'invalid_sic', 'no_interval'))
    return z.sort_values('_order').drop(columns='_order').reset_index(drop=True)


def industry_ranks(frame):
    z = frame.copy()
    valid = z.industry.gt(0) & np.isfinite(z.momentum)
    g = z.loc[valid].groupby(['date', 'industry']).momentum
    z['industry_peers'] = np.nan
    z['industry_percentile'] = np.nan
    z.loc[valid, 'industry_peers'] = g.transform('size')
    z.loc[valid, 'industry_percentile'] = (g.rank(method='average')-.5)/z.loc[valid, 'industry_peers']
    z['industry_supported'] = valid & z.industry_peers.ge(MIN_PEERS)
    z['feature_status'] = np.where(~valid, z.classification_status,
        np.where(z.industry_supported, 'supported', 'insufficient_peers'))
    return z


def mask(frame, minimum):
    return np.ones(len(frame), dtype=bool) if minimum < 0 else frame.industry_percentile.gt(minimum).to_numpy()
