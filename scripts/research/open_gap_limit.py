"""Opening-only price-cap eligibility using strictly pre-entry information."""
import numpy as np

from ath_breakout.research.initial_risk_trend import RiskTrendPortfolio

RULES = {'unrestricted': None, 'gap05': .5, 'gap10': 1., 'gap20': 2.}


def eligible(opening, signal_close, atr, limit):
    if not np.isfinite(opening) or opening <= 0:
        return False
    if limit is None:
        return True
    if not np.isfinite(signal_close) or signal_close <= 0 or not np.isfinite(atr) or atr <= 0:
        return False
    return opening <= signal_close + limit * atr


class GapLimitPortfolio(RiskTrendPortfolio):
    def __init__(self, policy, cost_bps, rule, **kwargs):
        super().__init__(policy, cost_bps, 'sma200', **kwargs)
        self.rule, self.window = rule, 150
        self.limit = RULES[rule]
        self.entry_screens = []

    def session(self, date, previous_date, rows, index, candidates):
        selected = []
        for candidate in candidates:
            sid = int(candidate['permno'])
            opening = rows['open'][index[sid]]
            close, atr = candidate['signal_close'], candidate['atr20_prior']
            accepted = eligible(opening, close, atr, self.limit)
            self.entry_screens.append(dict(event_id=candidate['event_id'], date=date,
                signal_date=previous_date, permno=sid, open=opening, signal_close=close,
                atr20_prior=atr, gap_atr=(opening-close)/atr,
                eligible=accepted, limit=self.limit))
            if accepted:
                selected.append(candidate)
        super().session(date, previous_date, dict(rows, sma200=rows['sma150']), index, selected)
