"""Standalone Plotly scientific figure from saved aggregate return diagnostics."""
import json
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def main():
    out = Path(sys.argv[1])
    bins = pd.read_csv(out/'distribution.csv')
    tails = pd.read_csv(out/'tails.csv')
    losses = pd.read_csv(out/'winner_prior_losses.csv')
    paths = pd.read_csv(out/'path_quantiles.csv')
    summary = pd.read_csv(out/'summary.csv')
    fig = make_subplots(rows=2, cols=2, vertical_spacing=.20, horizontal_spacing=.10,
        subplot_titles=['Annual return distribution (all tails retained)', 'Reached during year versus final annual gain',
                        'Closing-wealth paths: cross-sectional mean, median and 10–90% band',
                        'Final ≥100% winners: prior loss before first doubling'])
    names = [('momentum_top20', 'ATH + 6-1 momentum top20'), ('all_ath', 'All qualified ATH events')]
    counts = []
    for index, (sample, _) in enumerate(names):
        visible = index == 0
        before = len(fig.data)
        meta = dict(visible=visible, showlegend=False)
        b = bins.loc[bins['sample'].eq(sample) & bins.weighting.eq('all') & bins.period.eq('all')]
        for metric in ['stock_return', 'spy_return']:
            check = b.loc[b.metric.eq(metric)]
            assert len(check) == 9 and abs(check.fraction.sum()-1) < 1e-12
        for metric, label, color in [('stock_return', 'ATH stock', '#1565c0'), ('spy_return', 'Same-window SPY', '#78909c')]:
            v = b.loc[b.metric.eq(metric)]
            fig.add_trace(go.Bar(x=v['bin'], y=v.fraction*100, name=label, marker_color=color, customdata=v.events,
                hovertemplate=label+'<br>%{x}<br>%{y:.2f}% of events<br>N=%{customdata}<extra></extra>', **meta), row=1, col=1)
        t = tails.loc[tails['sample'].eq(sample) & tails.weighting.eq('all') & tails.period.eq('all')]
        assert t.final_events.le(t.ever_events).all()
        for metric, label, color in [('ever_fraction', 'Reached at a close', '#00a087'), ('final_fraction', 'Finished at or above', '#1565c0')]:
            fig.add_trace(go.Bar(x=['+'+str(int(v*100))+'%' for v in t.level], y=t[metric]*100, name=label,
                marker_color=color, hovertemplate=label+' %{x}<br>%{y:.2f}% of events<extra></extra>', **meta), row=1, col=2)
        p = paths.loc[paths['sample'].eq(sample)]
        ref = summary.loc[summary['sample'].eq(sample) & summary.weighting.eq('all') & summary.period.eq('all')].iloc[0]
        assert len(p) == 252 and abs(p.iloc[-1]['mean']-ref.stock) < 1e-12
        assert abs(p.iloc[-1]['median']-ref['median']) < 1e-12
        fig.add_trace(go.Scatter(x=p.session, y=p.q10*100, mode='lines', line=dict(width=0), name='10th percentile', **meta), row=2, col=1)
        fig.add_trace(go.Scatter(x=p.session, y=p.q90*100, mode='lines', line=dict(width=0), fill='tonexty',
            fillcolor='rgba(21,101,192,0.13)', name='10–90% range', **meta), row=2, col=1)
        fig.add_trace(go.Scatter(x=p.session, y=p['mean']*100, mode='lines', line=dict(color='#e07a18', width=2.5),
            name='Mean', hovertemplate='Mean at session %{x}: %{y:.2f}%<extra></extra>', **meta), row=2, col=1)
        fig.add_trace(go.Scatter(x=p.session, y=p['median']*100, mode='lines', line=dict(color='#1565c0', width=2.5),
            name='Median', hovertemplate='Median at session %{x}: %{y:.2f}%<extra></extra>', **meta), row=2, col=1)
        l = losses.loc[losses['sample'].eq(sample) & losses.weighting.eq('all') & losses.period.eq('all') & losses.level.eq(1.)]
        fig.add_trace(go.Bar(x=['−'+str(int(v*100))+'%' for v in l.loss], y=l.crossed_fraction*100,
            customdata=l[['crossed_events', 'winners']].to_numpy(), marker_color='#b35a45', name='Closing loss before doubling',
            hovertemplate='%{x} from entry before first +100%<br>%{y:.2f}% of final ≥100% winners<br>%{customdata[0]} / %{customdata[1]}<extra></extra>', **meta), row=2, col=2)
        counts.append(len(fig.data)-before)
    buttons = []
    for i, (sample, name) in enumerate(names):
        n = int(summary.loc[summary['sample'].eq(sample) & summary.weighting.eq('all') & summary.period.eq('all'), 'events'].iloc[0])
        visible = [False]*len(fig.data)
        start = sum(counts[:i])
        visible[start:start+counts[i]] = [True]*counts[i]
        buttons.append(dict(label=name, method='update', args=[dict(visible=visible),
            dict(title=dict(text=f'Annual returns after ATH | {name} | N={n:,}'))]))
    n = int(summary.loc[summary['sample'].eq('momentum_top20') & summary.weighting.eq('all') & summary.period.eq('all'), 'events'].iloc[0])
    fig.update_layout(title=dict(text=f'Annual returns after ATH | ATH + 6-1 momentum top20 | N={n:,}', x=.04),
        template='plotly_white', height=980, width=1400, margin=dict(l=75, r=45, t=145, b=115), barmode='group',
        font=dict(size=13), updatemenus=[dict(buttons=buttons, x=0, y=1.16, xanchor='left')])
    fig.update_xaxes(tickangle=-30, row=1, col=1)
    fig.update_yaxes(title_text='Events (%)', rangemode='tozero', row=1, col=1)
    fig.update_yaxes(title_text='Events (%)', rangemode='tozero', row=1, col=2)
    fig.update_xaxes(title_text='Holding session (entry close = 1)', row=2, col=1)
    fig.update_yaxes(title_text='Total return from entry (%)', row=2, col=1)
    fig.update_xaxes(title_text='Closing wealth below entry before first +100%', row=2, col=2)
    fig.update_yaxes(title_text='Final ≥100% winners (%)', range=[0, 100], row=2, col=2)
    fig.add_annotation(text='Blue: ATH stock / final gain / median path. Grey: SPY. Green: reached during year. Orange: mean path.',
        x=0, y=-.15, xref='paper', yref='paper', showarrow=False, xanchor='left', font=dict(size=12))
    fig.add_annotation(text='252-session gross event returns; initial investment 1; distributions and terminal cash. Closing observations only. No stop-loss or portfolio backtest.',
        x=0, y=-.20, xref='paper', yref='paper', showarrow=False, xanchor='left', font=dict(size=12))
    fig.write_html(out/'return_distribution.html', include_plotlyjs=True, full_html=True)
    (out/'return_distribution.plotly.json').write_text(fig.to_json(), encoding='utf-8')
    (out/'figure_checks.json').write_text(json.dumps(dict(panels=4, populations=2, traces=len(fig.data),
        default_population='momentum_top20', rows_per_distribution=9, aggregate_checks='passed', source='saved aggregate CSVs',
        renderer='Plotly standalone scientific figure', code_path='scripts/research/plot_ath_return_paths.py'), indent=2))
    print(out/'return_distribution.html')


if __name__ == '__main__':
    main()
