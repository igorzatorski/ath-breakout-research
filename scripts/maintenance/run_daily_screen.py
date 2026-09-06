"""Refresh Yahoo daily data, then screen only a completed current session."""

import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    subprocess.run([sys.executable, str(root / "scripts" / "run_screener.py"), "--latest"],
                   cwd=root, check=True)


if __name__ == "__main__":
    main()
