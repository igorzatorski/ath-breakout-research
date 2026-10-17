"""Fixed2x2 opening cap and early gain stages on the same ledger."""
from open_gap_limit import eligible
from stepped_sma import SteppedPortfolio

RULES = {'base': (False, False), 'steps': (True, False),
         'gap': (False, True), 'combined': (True, True)}


class FactorialPortfolio(SteppedPortfolio):
    def __init__(self, policy, cost_bps, rule, **kwargs):
        stages, capped = RULES[rule]
        super().__init__(policy, cost_bps, 'step25_50' if stages else 'sma150', **kwargs)
        self.rule = rule
        self.limit = .5 if capped else None
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
                atr20_prior=atr, gap_atr=(opening-close)/atr, eligible=accepted, limit=self.limit))
            if accepted:
                selected.append(candidate)
        super().session(date, previous_date, rows, index, selected)
