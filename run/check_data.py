"""Check local Data Layer readiness without downloads."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run._bootstrap import run_module  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(run_module('scripts.research.check_readiness'))
