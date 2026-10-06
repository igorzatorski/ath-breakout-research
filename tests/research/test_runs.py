"""Verify preservation, provenance and failed-run isolation."""
import json

import pytest

from ath_breakout.research.runs import recorded_run


def test_runs_never_overwrite_and_record_actual_artifacts(tmp_path):
    outputs = []
    for value in ('first', 'second'):
        with recorded_run(tmp_path / 'outputs', 'test', {'setting': value}, root=tmp_path) as output:
            (output / 'result.csv').write_text(value)
            outputs.append(output)
    assert outputs[0] != outputs[1]
    assert (outputs[0] / 'result.csv').read_text() == 'first'
    manifest = json.loads((outputs[0] / 'manifest.json').read_text())
    assert manifest['status'] == 'complete'
    assert len(manifest['artifacts']['result.csv']) == 64
    assert manifest['configuration'] == {'setting': 'first'}


def test_failed_run_retains_failure_state_and_propagates_error(tmp_path):
    with pytest.raises(ValueError, match='invalid input'):
        with recorded_run(tmp_path / 'outputs', 'test', {}, root=tmp_path) as output:
            raise ValueError('invalid input')
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['status'] == 'failed'
    assert manifest['error_type'] == 'ValueError'


def test_credentials_are_not_included_in_run_metadata(tmp_path):
    state = tmp_path / 'data/state'
    state.mkdir(parents=True)
    (state / 'wrds_settings.json').write_text('{"username":"private-user"}')
    with recorded_run(tmp_path / 'outputs', 'test', {}, root=tmp_path) as output:
        (output / 'result.csv').write_text('ok')
    assert 'private-user' not in (output / 'manifest.json').read_text()
