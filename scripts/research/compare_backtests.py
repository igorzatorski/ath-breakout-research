"""Compare completed saved backtests and flag incompatible assumptions."""
import argparse
import html
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ath_breakout.research.runs import file_hash, recorded_run


def compare_runs(directories):
    rows, curves, manifests = [], [], []
    for directory in directories:
        directory = Path(directory)
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('status') != 'complete' or manifest.get('kind') != 'portfolio_backtest':
            raise ValueError(f'Not a completed portfolio backtest: {directory}')
        for name in ('summary.csv', 'equity_curve.csv'):
            if manifest.get('artifacts', {}).get(name) != file_hash(directory / name):
                raise ValueError(f'Artifact fingerprint mismatch: {directory / name}')
        summary = pd.read_csv(directory / 'summary.csv')
        if len(summary) != 1:
            raise ValueError(f'Expected one summary row: {directory}')
        row = summary.iloc[0].to_dict()
        row['run_id'] = manifest['run_id']
        row['run_directory'] = str(directory.resolve())
        rows.append(row)
        curves.append(pd.read_csv(directory / 'equity_curve.csv'))
        manifests.append(manifest)
    table = pd.DataFrame(rows)
    warnings = []
    for key in ('start_date', 'end_date', 'benchmark_name', 'accounting_version', 'return_mode', 'diagnostic_subset'):
        values = [str(row.get(key)) for row in rows]
        if len(set(values)) > 1:
            warnings.append(f'Different {key}: direct performance ranking may be misleading.')
    if any(set(curve['date']) != set(curves[0]['date']) for curve in curves[1:]):
        warnings.append('Different observation calendars: curves are shown over their own dates.')
    if any(manifest['fingerprints']['data'] != manifests[0]['fingerprints']['data'] for manifest in manifests[1:]):
        warnings.append('Different input fingerprints: data snapshots differ.')
    if any(manifest['fingerprints']['code_sha256'] != manifests[0]['fingerprints']['code_sha256'] for manifest in manifests[1:]):
        warnings.append('Different code fingerprints: implementation versions differ.')
    if any(row.get('diagnostic_subset') is not None and not pd.isna(row.get('diagnostic_subset')) for row in rows):
        warnings.append('Diagnostic PERMNO subsets are not representative strategy performance.')
    figure = make_subplots(rows=2, cols=1, subplot_titles=['Growth of 100 vs SPY', 'Drawdown vs SPY'])
    for row, curve in zip(rows, curves):
        label = row['run_id']
        growth = curve['equity'] / float(row['initial_capital']) * 100
        figure.add_trace(go.Scatter(x=curve['date'], y=growth, name=label), row=1, col=1)
        figure.add_trace(go.Scatter(x=curve['date'], y=curve['drawdown'], name=label, showlegend=False), row=2, col=1)
    # Include each distinct benchmark curve when periods or inputs differ.
    seen = set()
    for index, curve in enumerate(curves):
        initial = float(rows[index]['initial_capital'])
        key = tuple(zip(curve['date'], (curve['benchmark_equity'] / initial).fillna(-1)))
        if key in seen:
            continue
        seen.add(key)
        label = 'SPY' if len(curves) == 1 else f'SPY ({index + 1})'
        figure.add_trace(go.Scatter(x=curve['date'], y=curve['benchmark_equity'] / initial * 100, name=label, line={'dash': 'dash'}), row=1, col=1)
        figure.add_trace(go.Scatter(x=curve['date'], y=curve['benchmark_drawdown'], name=label, line={'dash': 'dash'}, showlegend=False), row=2, col=1)
    figure.update_yaxes(tickformat='.0%', row=2, col=1)
    figure.update_layout(height=850, title='Saved backtest comparison', template='plotly_white')
    return table, figure, warnings


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', type=Path, help='two or more saved backtest directories')
    args = parser.parse_args(arguments)
    directories = args.runs
    if not directories:
        print('Paste saved run directories separated by | (see outputs/backtests/).')
        directories = [Path(value.strip().strip('"')) for value in input('Runs: ').split('|') if value.strip()]
    if len(directories) < 2:
        raise SystemExit('Select at least two completed backtests.')
    table, figure, warnings = compare_runs(directories)
    with recorded_run('outputs/comparisons/backtests', 'backtest_comparison', {'runs': [str(path.resolve()) for path in directories]}) as output:
        table.to_csv(output / 'comparison.csv', index=False)
        (output / 'warnings.json').write_text(json.dumps(warnings, indent=2), encoding='utf-8')
        warnings_html = ''.join('<li>' + html.escape(warning) + '</li>' for warning in warnings)
        report = (
            '<!doctype html><html><head><meta charset="utf-8"><title>Backtest comparison</title>'
            '<style>body{font-family:Arial;margin:24px}td,th{padding:6px;border:1px solid #ddd}'
            'table{border-collapse:collapse}.warning{color:#9a3500}.metrics{overflow-x:auto}</style>'
            '</head><body><h1>Saved backtest comparison</h1><ul class="warning">' + warnings_html
            + '</ul>' + figure.to_html(full_html=False, include_plotlyjs=True)
            + '<h2>All saved metrics</h2><div class="metrics">'
            + table.set_index('run_id').T.to_html(escape=True) + '</div></body></html>'
        )
        (output / 'comparison.html').write_text(report, encoding='utf-8')
    columns = [key for key in ('run_id', 'cagr', 'annualized_volatility', 'maximum_drawdown', 'benchmark_cagr', 'annualized_alpha_hac', 'sharpe_ratio_zero_rate') if key in table]
    print(table[columns].to_markdown(index=False))
    for warning in warnings:
        print('WARNING: ' + warning)
    print(f'Comparison saved: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
