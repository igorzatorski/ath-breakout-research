import sys
import types
import pandas as pd
import pytest
from scripts.maintenance import update_data_layer as update

@pytest.fixture
def connection(monkeypatch):
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
