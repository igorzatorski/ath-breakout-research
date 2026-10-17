"""Permanent gain-triggered exit stages on the existing cash/share ledger."""
import numpy as np

from ath_breakout.research.sma50_portfolio import Portfolio

RULES = {'sma150': None, 'step25_50': (.25, .50),
         'step50_100': (.50, 1.), 'step100_200': (1., 2.)}
WINDOWS = (150, 100, 50)


class SteppedPortfolio(Portfolio):
    def __init__(self, policy, cost_bps, rule, **kwargs):
        super().__init__(policy, cost_bps, **kwargs)
        if rule not in RULES:
            raise ValueError('Unknown stepped exit rule')
        self.rule = rule
        self.thresholds = RULES[rule]
        self.entry_prices, self.stages, self.pending_reasons = {}, {}, {}
        self.exit_decisions, self.transitions = [], []
        self.missing_trend_days = 0
        self.active_rows = self.active_index = self.effective = None

    def select(self, date, sid):
        j = self.active_index[sid]
        rows = self.active_rows
        close = rows['close'][j]
        prior = self.stages[sid]
        stage = prior
        if np.isfinite(close) and close > 0 and self.thresholds is not None:
            ratio = close / self.entry_prices[sid]
            stage = max(prior, sum(ratio >= 1 + threshold for threshold in self.thresholds))
        self.stages[sid] = stage
        selected = rows[f'sma{WINDOWS[stage]}'][j]
        self.effective[j] = selected
        if stage != prior:
            previous_sma = rows[f'sma{WINDOWS[prior]}'][j]
            self.transitions.append(dict(date=date, permno=sid, entry_price=self.entry_prices[sid],
                close=close, prior_stage=prior, stage=stage, previous_sma=previous_sma,
                selected_sma=selected, numerically_lower=bool(np.isfinite(selected)
                    and np.isfinite(previous_sma) and selected < previous_sma)))

    def trade(self, date, sid, delta, price, kind, decision_date, candidate=None, terminal=False):
        if kind == 'SMA50_EXIT':
            kind = self.pending_reasons[sid]
        super().trade(date, sid, delta, price, kind, decision_date, candidate, terminal)
        if kind == 'ENTRY':
            self.entry_prices[sid] = price
            self.stages[sid] = 0
            if not self.active_rows['terminal'][self.active_index[sid]]:
                self.select(date, sid)
        if sid not in self.positions:
            self.entry_prices.pop(sid, None)
            self.stages.pop(sid, None)
            self.pending_reasons.pop(sid, None)

    def session(self, date, previous_date, rows, index, candidates):
        self.active_rows, self.active_index = rows, index
        self.effective = rows['sma150'].copy()
        for sid, p in self.positions.items():
            if p.pending_since is None and not rows['terminal'][index[sid]]:
                self.select(date, sid)
        super().session(date, previous_date, dict(rows, sma=self.effective), index, candidates)
        for sid, p in self.positions.items():
            j = index[sid]
            trend = self.effective[j]
            if not np.isfinite(trend):
                self.missing_trend_days += 1
            if p.pending_since == date:
                window = WINDOWS[self.stages[sid]]
                reason = f'SMA{window}_EXIT'
                self.pending_reasons[sid] = reason
                self.exit_decisions.append(dict(date=date, permno=sid, entry_date=p.entry_date,
                    entry_price=self.entry_prices[sid], close=rows['close'][j], floor=np.nan,
                    sma=trend, window=window, stage=self.stages[sid], reason=reason))
        self.active_rows = self.active_index = self.effective = None
