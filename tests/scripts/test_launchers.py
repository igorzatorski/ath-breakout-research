"""Run real launchers outside the repository without opening another terminal."""
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('script,argument,expected', [
    ('venv', '--check', 'Environment ready:'),
    ('backtest', '--help', '--max-positions'),
    ('screen', '--help', '--as-of'),
    ('update_data', '--help', '--end-date'),
    ('compare_backtests', '--help', '--runs'),
])
def test_launcher_uses_project_environment_from_another_directory(tmp_path, script, argument, expected):
    result = subprocess.run([sys.executable, str(ROOT / 'run' / (script + '.py')), argument],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30, check=True)
    assert expected in result.stdout
