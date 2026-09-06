import json
import pandas as pd
import pytest
from scripts import run_period_screener as screen

@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(screen, "ensure_ready", lambda: None)
    state = tmp_path / "data/state"
    state.mkdir(parents=True)
    (state / "crsp_daily_history_manifest.json").write_text(json.dumps({"start_date": "2024-01-01", "end_date": "2024-07-08"}))
    monkeypatch.setattr(screen, "load_security_data", lambda path: pd.DataFrame())
    candidate = {"signal_date": pd.Timestamp("2024-07-03"), "security_id": "1", "ticker": "TEST", "close": 50., "setup_score": 70., "breakout_quality_score": 80.}
    history = pd.DataFrame({"nominal_open": [100.], "split_adj_open": [50.]}, index=pd.to_datetime(["2024-07-05"]))
    monkeypatch.setattr(screen, "load_crsp_point_in_time_inputs", lambda *a, **k: ({"1": history}, pd.DataFrame([candidate]), None))
    return tmp_path, history

def test_next_exchange_session_and_nominal_open(environment):
    root, _ = environment
    screen.main(["2024-07-03", "2024-07-03"])
    result = pd.read_csv(root / "outputs/screening/periods/2024-07-03_2024-07-03/breakouts.csv")
    assert result.loc[0, "entry_date"] == "2024-07-05"
    assert result.loc[0, "entry_price"] == 100.

def test_missing_next_session_does_not_use_later_price(environment):
    root, history = environment
    history.index = pd.to_datetime(["2024-07-08"])
    screen.main(["2024-07-03", "2024-07-03"])
    result = pd.read_csv(root / "outputs/screening/periods/2024-07-03_2024-07-03/breakouts.csv")
    assert len(result) == 1
    assert pd.isna(result.loc[0, "entry_price"])
    assert result.loc[0, "entry_status"] == "unavailable"

def test_outside_coverage_refuses_misleading_empty_result(environment):
    with pytest.raises(SystemExit, match="outside CRSP coverage"):
        screen.main(["2024-07-09", "2024-07-10"])
