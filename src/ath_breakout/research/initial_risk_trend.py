"""Fixed original-entry floor and alternative SMA exit legs on the ATH28 ledger."""
import numpy as np

from ath_breakout.research.sma50_portfolio import Portfolio


RULES = {'sma50': (50, False), 'floor5_sma50': (50, True),
    'sma200': (200, False), 'floor5_sma200': (200, True)}


class RiskTrendPortfolio(Portfolio):
    def __init__(self, policy, cost_bps, rule, **kwargs):
        super().__init__(policy, cost_bps, **kwargs)
        if rule not in RULES:
            raise ValueError('Unknown fixed exit rule')
        self.rule = rule
        self.window, self.use_floor = RULES[rule]
        self.entry_prices, self.pending_reasons = {}, {}
        self.exit_decisions = []
        self.missing_trend_days = 0
        self.active_rows, self.active_index = None, None
        self.active_trend = None

    def trade(self, date, sid, delta, price, kind, decision_date, candidate=None, terminal=False):
        if kind == 'SMA50_EXIT':
            kind = self.pending_reasons[sid]
        super().trade(date, sid, delta, price, kind, decision_date, candidate, terminal)
        if kind == 'ENTRY':
            self.entry_prices[sid] = price
            if self.use_floor:
                j = self.active_index[sid]
                trend = self.active_trend[j]
                self.active_rows['sma'][j] = max(trend, .95*price) if np.isfinite(trend) else .95*price
        if sid not in self.positions:
            self.entry_prices.pop(sid, None)
            self.pending_reasons.pop(sid, None)

    def session(self, date, previous_date, rows, index, candidates):
        trend = rows['sma'] if self.window == 50 else rows['sma200']
        effective = trend.copy()
        if self.use_floor:
            for sid in self.positions:
                j, floor = index[sid], .95*self.entry_prices[sid]
                effective[j] = max(effective[j], floor) if np.isfinite(effective[j]) else floor
        self.active_rows = dict(rows, sma=effective)
        self.active_index = index
        self.active_trend = trend
        super().session(date, previous_date, self.active_rows, index, candidates)
        for sid, p in self.positions.items():
            j = index[sid]
            if not np.isfinite(trend[j]):
                self.missing_trend_days += 1
            if p.pending_since == date:
                current = rows['close'][j]
                floor = .95*self.entry_prices[sid] if self.use_floor else np.nan
                floor_hit = self.use_floor and current < floor
                trend_hit = np.isfinite(trend[j]) and current < trend[j]
                assert floor_hit or trend_hit, 'Pending exit must match an actual current threshold'
                reason = 'BOTH_EXIT' if floor_hit and trend_hit else 'INITIAL_5_EXIT' if floor_hit else f'SMA{self.window}_EXIT'
                self.pending_reasons[sid] = reason
                self.exit_decisions.append(dict(date=date, permno=sid, entry_date=p.entry_date,
                    entry_price=self.entry_prices[sid], close=current, floor=floor,
                    sma=trend[j], window=self.window, reason=reason))
        self.active_rows, self.active_index = None, None
        self.active_trend = None
