"""Check online/offline routing and refresh-before-date-prompt ordering."""
from scripts.data.maintenance import crsp_refresh
from scripts.backtesting import run_backtest


def test_default_checks_online_and_preserves_arguments(monkeypatch):
    calls = []
    monkeypatch.setattr(crsp_refresh, "refresh", lambda username: calls.append(username))
    assert crsp_refresh.refresh_before_run(["--wrds-username", "test", "--start", "2020-01-01"]) == ["--start", "2020-01-01"]
    assert calls == ["test"]


def test_explicit_skip_does_not_connect(monkeypatch):
    monkeypatch.setattr(crsp_refresh, "refresh", lambda username: (_ for _ in ()).throw(AssertionError("Unexpected network call")))
    assert crsp_refresh.refresh_before_run(["--skip-crsp-check", "--latest"]) == ["--latest"]
    assert crsp_refresh.refresh_before_run(["--help"]) == ["--help"]


def test_backtest_reads_updated_default_end_after_refresh(tmp_path, monkeypatch):
    monkeypatch.setattr(run_backtest, "PROJECT_ROOT", tmp_path)
    state = tmp_path / "data/state"
    state.mkdir(parents=True)
    def refresh(arguments):
        (state / "crsp_daily_history_manifest.json").write_text('{"end_date":"2026-09-30"}')
        return []
    monkeypatch.setattr(run_backtest, "refresh_before_run", refresh)
    prompts = []
    monkeypatch.setattr(run_backtest, "request_date", lambda prompt, default: prompts.append(default) or default)
    monkeypatch.setattr(run_backtest, "run_crsp_backtest", lambda arguments: arguments)
    result = run_backtest.main([])
    assert result[-1] == "2026-09-30"
