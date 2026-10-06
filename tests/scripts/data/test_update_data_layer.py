import sys
import types
import pandas as pd
import pytest
from scripts.data.maintenance import update_data_layer as update

@pytest.fixture
def connection(monkeypatch, tmp_path):
    monkeypatch.setattr(update, "ROOT", tmp_path)
    monkeypatch.setattr(update, "refresh_benchmark", lambda end: None)
    class Connection:
        closed = False
        def raw_sql(self, sql):
            return pd.DataFrame({"last_date": ["2026-06-30"]})
        def close(self):
            self.closed = True
    instance = Connection()
    monkeypatch.setitem(sys.modules, "wrds", types.SimpleNamespace(Connection=lambda **kwargs: instance))
    monkeypatch.setattr(update, "load_wrds_password", lambda username: None)
    return instance


def test_current_valid_data_skip_all_downloads(monkeypatch, connection):
    state = update.ROOT / "data/state"
    state.mkdir(parents=True)
    (state / "crsp_daily_history_manifest.json").write_text('{"status":"complete","end_date":"2026-06-30"}')
    monkeypatch.setattr(update, "validate", lambda root: [])
    commands = []
    monkeypatch.setattr(update.subprocess, "run", lambda args, **kwargs: commands.append(args))
    assert update.refresh("test") == 0
    assert commands == []
    assert connection.closed


def test_incomplete_local_data_are_resumed(monkeypatch, connection):
    state = update.ROOT / "data/state"
    state.mkdir(parents=True)
    (state / "crsp_daily_history_manifest.json").write_text('{"status":"incomplete","end_date":"2026-06-30"}')
    commands = []
    monkeypatch.setattr(update.subprocess, "run", lambda args, **kwargs: commands.append(args))
    assert update.refresh("test") == 0
    assert any("download_wrds_crsp_daily_history.py" in str(command) for command in commands)


def test_derived_repair_does_not_redownload_raw(monkeypatch, connection):
    state = update.ROOT / "data/state"
    state.mkdir(parents=True)
    universe = update.ROOT / "data/processed/crsp/universe_memberships.parquet"
    universe.parent.mkdir(parents=True)
    universe.touch()
    (state / "crsp_daily_history_manifest.json").write_text('{"status":"complete","end_date":"2026-06-30"}')
    monkeypatch.setattr(update, "validate", lambda root: ["Processed ATH seed fingerprint is stale or missing"])
    commands = []
    monkeypatch.setattr(update.subprocess, "run", lambda args, **kwargs: commands.append(args))
    update.refresh("test")
    assert len(commands) == 3
    assert not any("download_wrds" in str(command) for command in commands)

def test_discovers_available_date_before_building(monkeypatch, connection):
    monkeypatch.setattr(sys, "argv", ["update", "--username", "test"])
    commands = []
    monkeypatch.setattr(update.subprocess, "run", lambda args, **kwargs: commands.append(args))
    assert update.main() == 0
    assert connection.closed
    assert commands[0][-1] == "2026-06-30"
    assert commands[1][-1] == "2026-06-30"
    assert commands[-1][-1].endswith("validate_data_layer.py")

def test_future_request_does_not_modify_local_data(monkeypatch, connection):
    monkeypatch.setattr(sys, "argv", ["update", "--username", "test", "--end-date", "2026-09-01"])
    commands = []
    monkeypatch.setattr(update.subprocess, "run", lambda *args, **kwargs: commands.append(args))
    with pytest.raises(SystemExit, match="coverage"):
        update.main()
    assert commands == []
    assert connection.closed
