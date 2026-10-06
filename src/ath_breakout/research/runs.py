"""Record isolated runs, input fingerprints, configuration and completion state."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(root=PROJECT_ROOT):
    """Fingerprint source manifests and code; never read credentials or price stores."""
    inputs = [
        'data/state/crsp_daily_history_manifest.json',
        'data/state/crsp_universe_history_manifest.json',
        'data/state/crsp_strategy_history_manifest.json',
        'data/state/crsp_quality_summary.json',
        'data/state/yfinance_manifest.csv',
        'data/state/benchmark_manifest.csv',
        'data/processed/features/SPY.parquet',
    ]
    data = {name: file_hash(root / name) for name in inputs if (root / name).is_file()}
    digest = hashlib.sha256()
    for directory in ('src', 'scripts', 'run'):
        for path in sorted((root / directory).rglob('*.py')):
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    try:
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {'data': data, 'code_sha256': digest.hexdigest(), 'git_commit': commit,
            'lock_sha256': file_hash(root / 'uv.lock') if (root / 'uv.lock').is_file() else None}


@contextmanager
def recorded_run(output_root, kind, configuration, root=PROJECT_ROOT):
    """Create a unique run directory; incomplete or failed runs stay identifiable."""
    started = datetime.now(timezone.utc)
    run_id = started.strftime('%Y%m%dT%H%M%S%fZ') + '_' + uuid4().hex[:8]
    output = Path(output_root) / run_id
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        'schema_version': 1, 'run_id': run_id, 'kind': kind, 'status': 'running',
        'started_at_utc': started.isoformat(), 'configuration': configuration,
        'fingerprints': None,
    }

    def save():
        temporary = output / 'manifest.json.tmp'
        temporary.write_text(json.dumps(manifest, indent=2, default=str), encoding='utf-8')
        temporary.replace(output / 'manifest.json')

    save()
    try:
        manifest['fingerprints'] = fingerprints(root)
        save()
        yield output
        manifest['artifacts'] = {
            path.relative_to(output).as_posix(): file_hash(path)
            for path in sorted(output.rglob('*'))
            if path.is_file() and path.name != 'manifest.json'
        }
        manifest['status'] = 'complete'
    except BaseException as error:
        manifest['status'] = 'failed'
        manifest['error_type'] = type(error).__name__
        raise
    finally:
        manifest['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        save()
