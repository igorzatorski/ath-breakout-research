"""Pre-signal OLS betas and close-to-close cumulative CAPM abnormal returns."""
import numpy as np


def capm_event_arrays(returns, terminals, market_excess, risk_free, signal_rows, columns, valid_forward, chunk=2048):
    """Estimate on t-252..t-1; CAR on t+2..t+252 (entry close onwards).

    Forward validity must come from the original next-open 252-session engine.
    Terminal Y day is active; later cash has zero beta and zero nominal return.
    """
    n = len(signal_rows)
    beta, intercept, car = [np.full(n, np.nan) for _ in range(3)]
    count = np.zeros(n, dtype=int)
    for start in range(0, n, chunk):
        stop = min(start+chunk, n)
        s, c = signal_rows[start:stop], columns[start:stop]
        pre = s[:, None]+np.arange(-252, 0)[None, :]
        assert pre.min() >= 0 and (pre < s[:, None]).all()
        r = returns[pre, c[:, None]]
        x = market_excess[pre]
        y = r-risk_free[pre]
        valid = np.isfinite(x) & np.isfinite(y) & (r >= -1)
        nn = valid.sum(axis=1)
        count[start:stop] = nn
        xx, yy = np.where(valid, x, 0), np.where(valid, y, 0)
        denom_n = np.maximum(nn, 1)
        sx, sy = xx.sum(axis=1), yy.sum(axis=1)
        variance = (xx*xx).sum(axis=1)-sx*sx/denom_n
        covariance = (xx*yy).sum(axis=1)-sx*sy/denom_n
        good = (nn >= 200) & (variance > 1e-12)
        b = np.divide(covariance, variance, out=np.full(len(s), np.nan), where=good)
        a = sy/denom_n-b*sx/denom_n
        beta[start:stop], intercept[start:stop] = b, a
        post = s[:, None]+np.arange(2, 253)[None, :]
        # Calendar can extend beyond the actual data cutoff; valid_forward masks it.
        assert post.max() < len(returns)
        rr = returns[post, c[:, None]]
        terminal = terminals[post, c[:, None]]
        after = np.cumsum(terminal, axis=1)-terminal > 0
        actual = np.where(after, 0, rr)
        exposed = np.where(after, 0, 1)
        abnormal = actual-risk_free[post]-b[:, None]*market_excess[post]*exposed
        ok = good & valid_forward[start:stop] & np.isfinite(abnormal).all(axis=1)
        car[start:stop] = np.where(ok, abnormal.sum(axis=1), np.nan)
    return beta, intercept, count, car
