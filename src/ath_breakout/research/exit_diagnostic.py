"""Fixed-unit, fixed-horizon paths for descriptive SMA50 exit diagnosis."""
import numpy as np


def price_components(opening, close, entry, exit_price):
    """Additive price movements for unchanged units, excluding exit-day close."""
    if len(opening) != len(close) or len(close) < 2:
        raise ValueError('Need entry through exit sessions')
    if not np.isfinite(opening).all() or not np.isfinite(close[:-1]).all():
        return None
    gaps = opening[1:]-close[:-1]
    intraday = close[:-1]-opening[:-1]
    assert np.isclose(gaps.sum()+intraday.sum(),exit_price-entry)
    return dict(all_holding_gap_return=gaps.sum()/entry,
        all_holding_intraday_return=intraday.sum()/entry,
        worst_overnight_gap=np.min(opening[1:]/close[:-1]-1))


def unit_path(opening, close, dividend, terminal, total_return, previous_close, entry, exit_index, cost=.001):
    """Return paired terminal wealth; missing pre-terminal closes invalidate path."""
    cash, alive = 0., True
    end_wealth = np.nan
    exit_wealth = np.nan
    post_exit = []
    for i in range(len(close)):
        if not alive:
            continue
        div = 0. if i == 0 else dividend[i]
        if not np.isfinite(div) or div < 0:
            return None
        cash += div
        if i == exit_index:
            if not np.isfinite(opening[i]) or opening[i] <= 0:
                return None
            exit_wealth = opening[i]*(1-cost)+cash
        if terminal[i]:
            previous, ret = previous_close[i], total_return[i]
            if not np.isfinite(previous) or previous <= 0 or not np.isfinite(ret) or ret < -1:
                return None
            payoff = previous*(1+ret)-dividend[i]
            if payoff < -1e-6:
                return None
            cash += max(0., payoff)
            end_wealth, alive = cash, False
        else:
            if not np.isfinite(close[i]) or close[i] <= 0:
                return None
            end_wealth = close[i]*(1-cost)+cash
            if i >= exit_index:
                post_exit.append(close[i])
    if not np.isfinite(exit_wealth):
        return None
    denominator = entry*(1+cost)
    return dict(hold_return=end_wealth/denominator-1, sale_return=exit_wealth/denominator-1,
        hold_minus_sale=(end_wealth-exit_wealth)/denominator,
        max_post_exit_price_return=max(post_exit)/opening[exit_index]-1 if post_exit else np.nan,
        terminal_before_endpoint=not alive)
