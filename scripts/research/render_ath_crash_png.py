"""Publication-style static plots from the reviewed ATH40 chart rows."""
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

COLORS = {'base': '#8c6bb1', 'steps': '#2563eb', 'gap': '#c77c15', 'combined': '#008476', 'SPY': '#242424'}
LABELS = {'base': 'SMA150 baseline', 'steps': 'Early SMA stages', 'gap': 'Opening cap 0.5 ATR',
          'combined': 'Stages + opening cap', 'SPY': 'SPY'}


def main(run):
    run = Path(run)
    out = run/'crash_charts'
    data = pd.read_csv(out/'reviewed_chart_rows.csv', parse_dates=['date'])
    metrics = pd.read_csv(run/'crash_metrics.csv')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
        'grid.alpha': .18, 'axes.titleweight': 'bold', 'savefig.facecolor': 'white'})
    for (episode, policy), f in data.groupby(['episode','policy']):
        fig, axes = plt.subplots(3, 1, figsize=(13, 10.5), sharex=True)
        for panel, ax in enumerate(axes, 1):
            for rule in ['base', 'steps', 'gap', 'combined', 'SPY']:
                z = f.loc[f.panel.eq(panel)&f.series.eq(rule)]
                if len(z):
                    ax.plot(z.date, z.value, color=COLORS[rule], label=LABELS[rule],
                        lw=2.2 if rule in ['combined','SPY'] else 1.6, ls='--' if rule=='base' else '-')
            trough = pd.Timestamp(metrics.loc[metrics.episode.eq(episode),'spy_trough_date'].iloc[0])
            ax.axvline(trough, color='#999999', lw=1, ls=':')
        axes[0].set_ylabel('Value (first close = 100)')
        axes[1].set_ylabel('Drawdown since 2008 (%)')
        axes[1].set_ylim(-60, 2)
        axes[2].set_ylabel('End-of-day cash / NAV (%)')
        axes[2].set_ylim(0, 100)
        axes[2].xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
        axes[2].xaxis.set_major_formatter(mdates.ConciseDateFormatter(axes[2].xaxis.get_major_locator()))
        axes[2].set_xlim(f.date.min(), f.date.max())
        title = f'ATH portfolios during {episode.replace("_", "–")} | {policy.replace("_", " ")}'
        fig.suptitle(title, x=.08, ha='left', fontsize=17, fontweight='bold')
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper left', bbox_to_anchor=(.07,.945), ncol=3, frameon=False)
        fig.subplots_adjust(left=.10, right=.97, top=.85, bottom=.12, hspace=.18)
        fig.text(.10,.035, 'US equities · 10 bps per side · zero cash yield · dotted line = SPY local trough\n'
            'Value starts at first window close; drawdown retains the full 2008 history. '
            '2020/2022 retain existing positions.\nCash follows individual stock exits and new entries; no market/cash overlay is applied.', fontsize=10, color='#444444')
        fig.savefig(out/f'crash_{episode}_{policy}.png', dpi=150)
        fig.savefig(out/f'crash_{episode}_{policy}.pdf')
        plt.close(fig)
    # Compact, directly comparable diagnostic of the principal candidate.
    fig, axes = plt.subplots(2, 3, figsize=(16, 8.2), sharey='row')
    for column, episode in enumerate(['2008_2009','2020','2022']):
        f = data.loc[data.episode.eq(episode)&data.policy.eq('drift')]
        for row, panel in enumerate([1,3]):
            for rule in (['steps','SPY'] if panel==1 else ['steps']):
                z = f.loc[f.panel.eq(panel)&f.series.eq(rule)]
                axes[row,column].plot(z.date,z.value,color=COLORS[rule],lw=2.3,label=LABELS[rule])
            axes[row,column].xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3,maxticks=4))
            axes[row,column].xaxis.set_major_formatter(mdates.ConciseDateFormatter(axes[row,column].xaxis.get_major_locator()))
            axes[row,column].set_xlim(f.date.min(),f.date.max())
        axes[0,column].set_title(episode.replace('_','–'),fontsize=14)
    axes[0,0].set_ylabel('Value (first close = 100)')
    axes[1,0].set_ylabel('Cash / NAV (%)')
    axes[1,0].set_ylim(0,100)
    axes[0,0].legend(frameon=False,loc='lower left')
    fig.suptitle('Does the SMA exit move the portfolio into cash?',x=.065,ha='left',fontweight='bold',fontsize=19)
    fig.subplots_adjust(left=.065,right=.98,top=.88,bottom=.16,hspace=.24,wspace=.12)
    fig.text(.065,.045,'Early SMA stages +25%/+50%, drift weights · daily net values · identical entry/ranking rules\n'
        'Cash is produced by stock exits and new entries, not an explicit market allocation rule. '
        '2008 starts in cash; 2020/2022 retain earlier positions.',fontsize=11,color='#444444')
    fig.savefig(out/'crash_overview_steps_drift.png',dpi=150)
    fig.savefig(out/'crash_overview_steps_drift.pdf')
    fig.savefig(out/'crash_overview_steps_drift.svg')
    plt.close(fig)
    print('Rendered six detailed PNG/PDF charts and the crash overview')


if __name__=='__main__':
    main(sys.argv[1])
