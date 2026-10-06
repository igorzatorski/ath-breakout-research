"""Update the separate Yahoo current-universe dataset."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run._bootstrap import run_module  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(run_module('scripts.data.maintenance.run_data_pipeline'))
