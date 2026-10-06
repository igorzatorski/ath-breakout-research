"""Create or synchronize .venv; commands use it automatically without activation."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify the existing environment without installing')
    args = parser.parse_args(arguments)
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not args.check:
        uv = shutil.which('uv')
        if not uv:
            print('Install uv first: python -m pip install uv')
            return 1
        subprocess.run([uv, 'sync', '--all-extras', '--locked'], cwd=ROOT, check=True)
    if not python.is_file():
        print('Project .venv is missing. Run this script without --check.')
        return 1
    probe = (
        "import sys,pandas,pyarrow,plotly,yfinance,sklearn,wrds,keyring,pytest,ruff,rich; "
        "print('Environment ready: '+sys.executable); "
        "print('scikit-learn: '+sklearn.__version__)"
    )
    subprocess.run([str(python), '-c', probe], cwd=ROOT, check=True)
    print('No terminal activation is needed. Open a file in run/ and click Run Python File.')
    print('Next: run/check_data.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
