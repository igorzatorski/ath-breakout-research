"""Cash/share ledger for fresh ATH entries and next-open SMA50 exits."""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Holding:
    permno: int
    permco: int
    ticker: str
    entry_date: object
    signal_date: object
    quantity: float = 0.
    last: float = 0.
    bought: float = 0.
    sold: float = 0.
    dividends: float = 0.
    pending_since: object = None


class Portfolio:
    def __init__(self, policy, cost_bps, initial=100000., maximum=20, weight=.05):
        if policy not in ['drift', 'monthly_equal'] or not 0 <= cost_bps < 100 or not 0 < weight*maximum <= 1:
            raise ValueError('Invalid portfolio configuration')
        self.policy, self.rate, self.initial = policy, cost_bps/10000, initial
        self.maximum, self.weight = maximum, weight
        self.cash, self.fees = initial, 0.
        self.positions, self.transactions, self.closed, self.skips, self.equity, self.holdings = {}, [], [], [], [], []
        self.rebalance_pending = False
        self.rebalance_decision = None
        self.stale_marks, self.return_checks, self.max_return_error = 0, 0, 0.
        self.rebalance_count, self.deferred_exits = 0, 0

    def nav(self):
        return self.cash+sum(p.quantity*p.last for p in self.positions.values())

    def trade(self, date, sid, delta, price, kind, decision_date, candidate=None, terminal=False):
        if not np.isfinite(price) or price < 0 or (price == 0 and not terminal):
            raise ValueError('Nonexecutable transaction price')
        if sid not in self.positions:
            if delta <= 0 or candidate is None:
                raise ValueError('New holding needs a signal')
            self.positions[sid] = Holding(sid, int(candidate['permco']), str(candidate['ticker']), date,
                candidate['date'], last=price)
        p = self.positions[sid]
        p.last = price
        before = self.nav()
        quantity_before = p.quantity
        notional, fee = delta*price, abs(delta*price)*(0 if terminal else self.rate)
        change = -notional-fee
        self.cash += change
        p.quantity += delta
        self.fees += fee
        if delta > 0:
            p.bought += notional+fee
        else:
            p.sold += -notional-fee
        if p.quantity < -1e-8 or self.cash < -max(1e-6, before*1e-10):
            raise ValueError('Short position or unfinanced purchase')
        if abs(self.cash) < 1e-7:
            self.cash = 0.
        self.transactions.append(dict(date=date, decision_date=decision_date, permno=sid, permco=p.permco,
            ticker=p.ticker, kind=kind, quantity=delta, quantity_before=quantity_before,
            quantity_after=p.quantity, price=price, notional=notional, fee=fee,
            cash_delta=change, cash_after=self.cash, nav_before=before, nav_after=self.nav()))
        if not np.isclose(self.nav(), before-fee, atol=max(1e-6, before*1e-10)):
            raise AssertionError('Trade failed wealth conservation')
        if delta < 0 and abs(p.quantity) <= max(np.finfo(float).tiny, abs(quantity_before)*1e-12):
            self.closed.append(dict(permno=sid, permco=p.permco, ticker=p.ticker,
                entry_date=p.entry_date, exit_date=date, reason=kind, bought=p.bought, sold=p.sold,
                dividends=p.dividends, pnl=p.sold+p.dividends-p.bought,
                cashflow_profit_ratio=(p.sold+p.dividends)/p.bought-1))
            del self.positions[sid]

    def session(self, date, previous_date, rows, index, candidates):
        def value(sid, field):
            return rows[field][index[sid]]

        overnight = {sid: (p.quantity, p.last) for sid, p in self.positions.items()}
        # Ex-date entitlement belongs only to shares held before this opening.
        for sid, p in list(self.positions.items()):
            if value(sid, 'observed'):
                dividend = value(sid, 'dividend')
                if not np.isfinite(dividend) or dividend < 0:
                    raise ValueError(f'Missing distribution for held PERMNO {sid} at {date}')
                amount = p.quantity*dividend
                if amount:
                    self.cash += amount
                    p.dividends += amount
                    self.transactions.append(dict(date=date, decision_date=date, permno=sid, permco=p.permco,
                        ticker=p.ticker, kind='DIVIDEND', quantity=0., quantity_before=p.quantity,
                        quantity_after=p.quantity, price=0., notional=0., fee=0., cash_delta=amount,
                        cash_after=self.cash, nav_before=np.nan, nav_after=np.nan))
            price = value(sid, 'open')
            if np.isfinite(price) and price > 0:
                p.last = price
            company = value(sid, 'company')
            if np.isfinite(company):
                p.permco = int(company)
        if len({p.permco for p in self.positions.values()}) != len(self.positions):
            raise ValueError('Corporate change created duplicate held company')
        for sid, p in list(self.positions.items()):
            if p.pending_since is not None:
                opening = value(sid, 'open')
                if np.isfinite(opening) and opening > 0:
                    self.trade(date, sid, -p.quantity, opening, 'SMA50_EXIT', p.pending_since)
                else:
                    self.deferred_exits += 1
                    self.skips.append(dict(date=date, permno=sid, reason='deferred_exit_no_open'))
        if self.policy == 'monthly_equal' and previous_date is not None and date.month != previous_date.month:
            self.rebalance_pending = True
            self.rebalance_decision = previous_date
        selected, companies = [], {p.permco for p in self.positions.values()}
        slots = self.maximum-len(self.positions)
        for candidate in candidates:
            if previous_date is None or pd.Timestamp(candidate['date']) != pd.Timestamp(previous_date):
                raise ValueError('Entry candidate must come from immediately previous session')
            sid, company = int(candidate['permno']), int(candidate['permco'])
            if company in companies or sid in self.positions:
                reason = 'already_held_company'
            elif len(selected) >= slots:
                reason = 'capacity'
            elif not np.isfinite(value(sid, 'open')) or value(sid, 'open') <= 0:
                reason = 'missing_entry_open'
            else:
                selected.append(candidate)
                companies.add(company)
                continue
            self.skips.append(dict(date=date, signal_date=candidate['date'], permno=sid, reason=reason))
        can_rebalance = all(np.isfinite(value(sid, 'open')) and value(sid, 'open') > 0 for sid in self.positions)
        if self.rebalance_pending and can_rebalance:
            nav = self.nav()
            target_ids = list(self.positions)+[int(c['permno']) for c in selected]
            values = np.array([self.positions[sid].quantity*value(sid, 'open') if sid in self.positions else 0. for sid in target_ids])
            lo, hi = 0., self.weight*nav
            for _ in range(70):
                target = (lo+hi)/2
                if target/self.weight+self.rate*np.abs(target-values).sum() > nav:
                    hi = target
                else:
                    lo = target
            target = (lo+hi)/2
            metadata = {int(c['permno']): c for c in selected}
            orders = [(sid, target-current) for sid, current in zip(target_ids, values)]
            for sid, dollars in sorted(orders, key=lambda item: item[1]):
                if abs(dollars) <= max(1e-8, nav*1e-12):
                    continue
                fresh = sid not in self.positions
                self.trade(date, sid, dollars/value(sid, 'open'), value(sid, 'open'),
                    'ENTRY' if fresh else 'REBAL_BUY' if dollars > 0 else 'REBAL_SELL',
                    metadata[sid]['date'] if fresh else self.rebalance_decision, metadata.get(sid))
            self.rebalance_pending = False
            self.rebalance_count += 1
        else:
            if self.rebalance_pending:
                self.skips.append(dict(date=date, permno=-1, reason='deferred_monthly_rebalance'))
            opening_nav = self.nav()
            target = opening_nav*self.weight
            for candidate in selected:
                sid = int(candidate['permno'])
                dollars = min(target, self.cash/(1+self.rate))
                if dollars <= max(1e-8, opening_nav*1e-12):
                    self.skips.append(dict(date=date, permno=sid, reason='no_cash'))
                    continue
                self.trade(date, sid, dollars/value(sid, 'open'), value(sid, 'open'), 'ENTRY', candidate['date'], candidate)
        # Regular cash-ledger returns must reconcile with source CIZ returns.
        for sid, (_, previous_close) in overnight.items():
            current, dividend, ret = value(sid, 'close'), value(sid, 'dividend'), value(sid, 'return')
            # A source return following a missing close need not start at our
            # explicitly carried stale mark. Only compare identical endpoints.
            source_previous = value(sid, 'previous_close')
            if not np.isfinite(source_previous) or not np.isclose(source_previous, previous_close):
                self.skips.append(dict(date=date, permno=sid, reason='return_check_unmatched_previous_mark'))
                continue
            if value(sid, 'observed') and not value(sid, 'terminal') and np.isfinite(current) and current > 0:
                if not np.isfinite(ret) or ret < -1:
                    raise ValueError(f'Missing held daily return {sid} at {date}')
                error = abs((current+dividend)/previous_close-1-ret)
                self.return_checks += 1
                self.max_return_error = max(self.max_return_error, error)
                if error > 1e-5:
                    raise ValueError(f'Unexplained CIZ price/distribution return {sid} at {date}: {error}')
        stale = 0
        for sid, p in list(self.positions.items()):
            if value(sid, 'terminal'):
                ret, dividend = value(sid, 'return'), value(sid, 'dividend')
                previous = overnight[sid][1] if sid in overnight else value(sid, 'previous_close')
                if not np.isfinite(ret) or ret < -1 or not np.isfinite(previous) or previous <= 0 or not np.isfinite(dividend):
                    raise ValueError(f'Unresolved terminal payoff {sid} at {date}')
                payoff = previous*(1+ret)-dividend
                if payoff < -1e-6:
                    raise ValueError('Negative terminal stock payoff after distributions')
                self.trade(date, sid, -p.quantity, max(0., payoff), 'CIZ_TERMINAL', date, terminal=True)
                continue
            current, sma = value(sid, 'close'), value(sid, 'sma')
            if np.isfinite(current) and current > 0:
                p.last = current
                if np.isfinite(sma) and current < sma and p.pending_since is None:
                    p.pending_since = date
            else:
                stale += 1
                self.skips.append(dict(date=date, permno=sid, reason='stale_close_mark'))
        self.stale_marks += stale
        nav = self.nav()
        if not np.isfinite(nav) or nav <= 0 or self.cash < -1e-6 or len(self.positions) > self.maximum:
            raise ValueError('Invalid end-of-day portfolio state')
        prior = self.equity[-1]['nav'] if self.equity else self.initial
        self.equity.append(dict(date=date, nav=nav, cash=self.cash, exposure=1-self.cash/nav,
            positions=len(self.positions), fees_cumulative=self.fees, daily_return=nav/prior-1, stale_marks=stale))
        for sid, p in self.positions.items():
            self.holdings.append(dict(date=date, permno=sid, permco=p.permco, quantity=p.quantity,
                price=p.last, value=p.quantity*p.last, weight=p.quantity*p.last/nav,
                pending_exit=p.pending_since is not None))

    def ending_positions(self):
        return pd.DataFrame([dict(permno=sid, permco=p.permco, ticker=p.ticker, entry_date=p.entry_date,
            quantity=p.quantity, mark=p.last, value=p.quantity*p.last, bought=p.bought, sold=p.sold,
            dividends=p.dividends, unrealized_total_pnl=p.quantity*p.last+p.sold+p.dividends-p.bought)
            for sid, p in self.positions.items()])


def performance(equity, initial):
    if equity.empty:
        return {}
    returns = equity.daily_return.to_numpy()
    curve = np.r_[initial, initial*np.cumprod(1+returns)]
    vol = np.std(returns, ddof=1)*np.sqrt(252)
    return dict(sessions=len(returns), total_return=curve[-1]/initial-1,
        cagr=(curve[-1]/initial)**(252/len(returns))-1, volatility=vol,
        sharpe_zero_rf=np.mean(returns)*252/vol if vol > 0 else np.nan,
        max_drawdown=np.min(curve/np.maximum.accumulate(curve)-1), average_exposure=equity.exposure.mean(),
        average_positions=equity.positions.mean(), final_nav=equity.nav.iloc[-1])
