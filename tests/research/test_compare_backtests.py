"""Ensure comparisons identify incompatible runs and changed artifacts."""
import json

import pandas as pd
import pytest

from ath_breakout.research.runs import recorded_run
from scripts.research.compare_backtests import compare_runs


def make_run(root, start='2024-01-02', capital=100):
    with recorded_run(root / 'outputs', 'portfolio_backtest', {}, root=root) as output:
        pd.DataFrame([{'start_date': start, 'end_date': '2024-01-03', 'initial_capital': capital,
                       'cagr': 0.1, 'benchmark_name': 'SPY', 'return_mode': 'crsp_total_return'}]).to_csv(output / 'summary.csv', index=False)
        pd.DataFrame({'date': [start, '2024-01-03'], 'equity': [capital, capital * 1.1],
                      'benchmark_equity': [capital, capital * 1.02], 'drawdown': [0, 0],
                      'benchmark_drawdown': [0, 0]}).to_csv(output / 'equity_curve.csv', index=False)
    return output


def test_growth_is_normalized_and_same_benchmark_is_not_duplicated(tmp_path):
    table, figure, warnings = compare_runs([make_run(tmp_path), make_run(tmp_path, capital=200)])
    assert len(table) == 2
    assert warnings == []
    assert len(figure.data) == 6  # two strategies and one normalized benchmark
    assert list(figure.data[0].y) == pytest.approx([100, 110])


def test_different_period_is_explicitly_flagged(tmp_path):
    _, _, warnings = compare_runs([make_run(tmp_path), make_run(tmp_path, start='2024-01-01')])
    assert any('start_date' in warning for warning in warnings)
    assert any('calendars' in warning for warning in warnings)


def test_failed_runs_and_modified_artifacts_are_rejected(tmp_path):
    output = make_run(tmp_path)
    (output / 'summary.csv').write_text('changed')
    with pytest.raises(ValueError, match='fingerprint mismatch'):
        compare_runs([output])
    manifest = json.loads((output / 'manifest.json').read_text())
    manifest['status'] = 'failed'
    (output / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='Not a completed'):
        compare_runs([output])
