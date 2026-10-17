"""Five authorized SMA exits using the unchanged risk/trend ledger."""
from ath_breakout.research.initial_risk_trend import RiskTrendPortfolio

WINDOWS = (50, 100, 150, 200, 250)
RULES = tuple(f'sma{window}' for window in WINDOWS)


class SMAExitPortfolio(RiskTrendPortfolio):
    def __init__(self, policy, cost_bps, rule, **kwargs):
        if rule not in RULES:
            raise ValueError('Unsupported exit window')
        super().__init__(policy, cost_bps, 'sma200', **kwargs)
        self.rule = rule
        self.window = int(rule[3:])

    def session(self, date, previous_date, rows, index, candidates):
        selected = rows['sma'] if self.window == 50 else rows[self.rule]
        super().session(date, previous_date, dict(rows, sma200=selected), index, candidates)
