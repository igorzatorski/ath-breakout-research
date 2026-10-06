"""Run every public command with the project's interpreter and working directory."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_module(module, arguments=None):
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        print('Project .venv is missing. Run run/venv.py first.', file=sys.stderr)
        return 1
    environment = os.environ.copy()
    environment['VIRTUAL_ENV'] = str(ROOT / '.venv')
    environment['PATH'] = str(python.parent) + os.pathsep + environment.get('PATH', '')
    environment['PYTHONPATH'] = os.pathsep.join([str(ROOT), str(ROOT / 'src')])
    environment.pop('PYTHONHOME', None)
    options = sys.argv[1:] if arguments is None else arguments
    return subprocess.run([str(python), '-m', module, *options], cwd=ROOT, env=environment).returncode
