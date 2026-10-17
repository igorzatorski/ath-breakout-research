"""Export source-backed Plotly crash charts and matched benchmark episodes."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

WINDOWS = {'2008_2009': ('2008-01-02', '2009-06-30'),
           '2020': ('2020-01-02', '2020-12-31'), '2022': ('2022-01-03', '2022-12-30')}
LABELS = {'base': 'SMA150 baseline', 'steps': 'Early SMA stages',
          'gap': 'Opening cap 0.5 ATR', 'combined': 'Stages + opening cap', 'SPY': 'SPY'}
COLORS = {'base': '#8c6bb1', 'steps': '#2563eb', 'gap': '#c77c15', 'combined': '#008476', 'SPY': '#242424'}


def main(run):
    run = Path(run)
    out = run / 'crash_charts'
    out.mkdir(exist_ok=True)
    curves = {f'{rule}__{policy}_10bps': pd.read_csv(run / f'{rule}__{policy}_10bps/equity.csv', parse_dates=['date'])
              for rule in ['base', 'steps', 'gap', 'combined'] for policy in ['drift', 'monthly_equal']}
    source = curves['base__drift_10bps']
    records, rows = [], []
    chart_files = []
    for episode, (start, end) in WINDOWS.items():
        segment = source.loc[source.date.between(start, end)]
        first = segment.index[0]
        reference_initial = 100000. if first == 0 else source.spy_nav.iloc[first-1]
        reference = np.r_[reference_initial, segment.spy_nav.to_numpy()]
        reference_dd = reference / np.maximum.accumulate(reference)-1
        trough = int(np.argmin(reference_dd))
        peak = int(np.argmax(reference[:trough+1]))
        trough_date = segment.date.iloc[trough-1]
        peak_date = segment.date.iloc[peak-1] if peak else segment.date.iloc[0]
        reference_loss = reference[trough]/reference[peak]-1
        for name, equity in curves.items():
            f = equity.loc[equity.date.between(start, end)]
            initial = 100000. if first == 0 else equity.nav.iloc[first-1]
            curve = np.r_[initial, f.nav.to_numpy()]
            peak_nav = curve[peak]
            trough_nav = curve[trough]
            cash = f.cash/f.nav
            peak_cash = 1. if first == 0 and peak == 0 else (
                equity.cash.iloc[first-1]/equity.nav.iloc[first-1] if peak == 0 else cash.iloc[peak-1])
            records.append(dict(episode=episode, run=name, start=str(f.date.iloc[0].date()), end=str(f.date.iloc[-1].date()),
                window_return=curve[-1]/curve[0]-1,
                local_max_drawdown=(curve/np.maximum.accumulate(curve)-1).min(),
                global_max_drawdown_in_window=f.drawdown.min(), average_cash=cash.mean(), min_cash=cash.min(), max_cash=cash.max(),
                spy_peak_date=str(peak_date.date()), peak_is_initial_capital=peak == 0,
                spy_trough_date=str(trough_date.date()), spy_peak_to_trough=reference_loss,
                strategy_matched_peak_to_trough=trough_nav/peak_nav-1,
                cash_at_spy_peak=peak_cash, cash_at_spy_trough=float(cash.iloc[trough-1])))
        for policy in ['drift', 'monthly_equal']:
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.07,
                subplot_titles=('Portfolio value: first window close = 100',
                    'Drawdown from running peak since 2008 (%)', 'End-of-day cash / portfolio NAV (%)'))
            for rule in ['base', 'steps', 'gap', 'combined', 'SPY']:
                f = curves[f'{rule if rule != "SPY" else "base"}__{policy}_10bps']
                f = f.loc[f.date.between(start, end)]
                nav = f.spy_nav if rule == 'SPY' else f.nav
                if rule == 'SPY':
                    all_eq = curves[f'base__{policy}_10bps']
                    dd = all_eq.spy_nav / np.maximum.accumulate(np.r_[100000., all_eq.spy_nav])[1:] - 1
                    dd = dd.loc[f.index]
                else:
                    dd = f.drawdown
                series = [nav/nav.iloc[0]*100, dd*100]
                if rule != 'SPY':
                    series.append(f.cash/f.nav*100)
                for panel, values in enumerate(series, 1):
                    fig.add_trace(go.Scatter(x=f.date, y=values, name=LABELS[rule], legendgroup=rule,
                        showlegend=panel == 1, mode='lines', line=dict(color=COLORS[rule],
                            width=2.6 if rule in ['combined', 'SPY'] else 1.7,
                            dash='dash' if rule == 'base' else 'solid'),
                        hovertemplate='%{x|%Y-%m-%d}<br>%{y:.2f}<extra>'+LABELS[rule]+'</extra>'), row=panel, col=1)
                    rows.extend(dict(episode=episode, policy=policy, series=rule, panel=panel,
                        date=str(date.date()), value=float(value)) for date, value in zip(f.date, values))
            fig.add_vline(x=trough_date.timestamp()*1000, line_width=1, line_dash='dot', line_color='#777777')
            fig.update_layout(title=dict(text=f'ATH research: {episode.replace("_", "–")} | {policy.replace("_", " ")}', x=.04),
                template='plotly_white', height=1050, width=1300, hovermode='x unified',
                margin=dict(l=80, r=40, t=120, b=100),
                legend=dict(orientation='h', y=1.11, x=0), font=dict(family='Arial', size=13))
            fig.update_yaxes(title_text='Indexed value', row=1, col=1)
            fig.update_yaxes(title_text='Drawdown (%)', range=[-60, 1], row=2, col=1)
            fig.update_yaxes(title_text='Cash (%)', range=[0, 100], row=3, col=1)
            fig.update_xaxes(range=[f.date.iloc[0], f.date.iloc[-1]], nticks=7)
            fig.add_annotation(xref='paper', yref='paper', x=0, y=-.10, showarrow=False, align='left',
                text='US equities; 10 bps/side; zero cash yield. Dotted line: SPY local trough. '
                     '2020/2022 inherit existing positions.<br>Value is rebased at first close; drawdown retains full 2008 history. '
                     'Cash is an outcome of stock exits and new entries, not a market overlay.', font=dict(size=11))
            path = out / f'crash_{episode}_{policy}.html'
            fig.write_html(path, include_plotlyjs=True, config=dict(responsive=True, displaylogo=False,
                toImageButtonOptions=dict(format='png', filename=f'ath_crash_{episode}_{policy}', width=1300, height=1050, scale=2)))
            chart_files.append(path.name)
    pd.DataFrame(records).to_csv(run / 'crash_metrics.csv', index=False)
    pd.DataFrame(rows).to_csv(out / 'reviewed_chart_rows.csv', index=False)
    (out / 'sources.json').write_text(json.dumps(dict(source_files=[str(Path(n)/'equity.csv') for n in curves],
        windows=WINDOWS, definitions=dict(value='first close in each window = 100',
        drawdown='running peak seeded by initial capital since 2008', cash='end-of-day cash / NAV',
        trough='minimum local SPY drawdown including prior-close capital'), charts=chart_files), indent=2))
    print(pd.DataFrame(records).loc[lambda x:x.run.eq('steps__drift_10bps'),
        ['episode', 'spy_peak_to_trough', 'strategy_matched_peak_to_trough', 'cash_at_spy_peak', 'cash_at_spy_trough']].to_string(index=False))
    print('CHARTS:', out, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
