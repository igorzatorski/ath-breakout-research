"""Read-only structural/source audit of a completed ATH matched signal study."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(
        (ROOT / "outputs/research/ath/ath_04_signal_matched_v002").iterdir())[-1]
    manifest = json.loads((out / "manifest.json").read_text())
    for item in manifest["inputs"]:
        assert sha256(ROOT / item["path"]) == item["sha256"]
    for name, fingerprint in manifest["artifacts"].items():
        assert sha256(out / name) == fingerprint
    event_count, matched_count = 0, 0
    for path in sorted((out / "by_year").glob("events_*.parquet")):
        e = pd.read_parquet(path)
        m = pd.read_parquet(path.with_name(path.name.replace("events_", "matches_")))
        assert not e.duplicated(["permno", "date"]).any()
        assert e.adjusted_close.gt(e.prior_ath).all()
        assert (~e.history_uncertain).all()
        assert e.formation_date.lt(e.date).all()
        assert e.adv21.ge(10_000_000).all()
        assert not m.duplicated(["event_id", "permno"]).any()
        assert m.groupby("event_id").size().eq(5).all()
        assert m.groupby("event_id").control_permco.nunique().eq(5).all()
        assert m.control_permco.ne(m.event_permco).all()
        assert m.size_ratio.between(.5-1e-12, 2+1e-12).all()
        assert m.vol_ratio.between(1/1.5-1e-12, 1.5+1e-12).all()
        assert set(m.event_id).issubset(set(e.event_id))
        event_count += len(e)
        matched_count += m.event_id.nunique()
    f = pd.read_parquet(out / "forward_returns.parquet")
    assert len(f) == event_count * 4
    assert not f.duplicated(["event_id", "horizon"]).any()
    assert np.allclose(f.excess_spy, f.stock_return-f.spy_return, equal_nan=True)
    assert np.allclose(f.excess_control, f.stock_return-f.control_return, equal_nan=True)
    assert f.loc[f.valid_control_count.ne(5), "control_return"].isna().all()
    assert f.loc[f.status.ne("ok"), "stock_return"].isna().all()
    assert (f.stock_return.dropna() >= -1-1e-12).all()
    assert not np.isinf(f.stock_return.dropna()).any()
    legacy = pd.read_parquet(ROOT / "data/raw/crsp/ath_seed_before_1993.parquet").set_index("permno")
    repaired = pd.read_parquet(ROOT / "outputs/research/ath/shared_inputs/high_seed_before_1993.parquet").set_index("permno")
    joined = legacy.join(repaired[["prior_comparable_close"]], how="inner")
    assert np.allclose(joined.prior_comparable_high, joined.prior_comparable_close, rtol=1e-7, atol=1e-8)
    print(json.dumps({"status": "PASS", "events": event_count, "matched_at_signal": int(matched_count),
                      "paired_21": int((f.horizon.eq(21)&f.excess_spy.notna()&f.excess_control.notna()).sum()),
                      "legacy_live_close_alignment": len(joined), "source_and_artifact_hashes": "PASS",
                      "controls_and_event_invariants": "PASS"}, indent=2))


if __name__ == "__main__":
    main()
