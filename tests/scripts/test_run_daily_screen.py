import subprocess

import pytest

from scripts.maintenance import run_daily_screen


def test_failed_update_never_launches_screener(monkeypatch):
    calls = []

    def fail(command, **kwargs):
        calls.append(command)
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(run_daily_screen.subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        run_daily_screen.main()
    assert len(calls) == 1
    assert calls[0][-2].endswith("run_screener.py")
    assert calls[0][-1] == "--latest"
