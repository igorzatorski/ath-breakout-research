"""Read-only preflight for the new ATH research workspace; no downloads/repairs."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.data.validation.validate_data_layer import validate  # noqa: E402


def main():
    config = json.loads((ROOT / "research/ath/baseline.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/state/crsp_daily_history_manifest.json").read_text())
    errors = validate(ROOT)
    if not manifest["start_date"] <= config["start_date"] <= config["end_date"] <= manifest["end_date"]:
        errors.append("Planned dates exceed local CRSP coverage")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print("PASS: local Data Layer manifests, partitions and source fingerprints")
    print(f"CRSP coverage: {manifest['start_date']} to {manifest['end_date']}")
    print(f"Study: {config['study_id']} ({config['status']})")
    print("NEXT: implement the unfiltered ATH event table; the existing screen is not this baseline.")
    print("This preflight does not validate research assumptions, economic returns or sample selection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
