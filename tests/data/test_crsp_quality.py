import json

import pandas as pd

from ath_breakout.data.adapters.crsp import CRSP_DAILY_COLUMNS
from ath_breakout.data.crsp_quality import audit_crsp_history


def daily_rows() -> pd.DataFrame:
    rows = []
    for permno, day in [(10001, "2025-01-02"), (10001, "2025-01-03")]:
        row = {column: None for column in CRSP_DAILY_COLUMNS}
        row.update({
            "security_id": str(permno), "permno": permno, "permco": 1,
            "ticker": "TEST", "date": pd.Timestamp(day), "open": 10.0,
            "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100.0,
            "total_return": 0.01, "source": "CRSP CIZ quarterly",
        })
        rows.append(row)
    return pd.DataFrame(rows)


def write_fixture(tmp_path, daily: pd.DataFrame, expected_rows: int = 2):
    partition = tmp_path / "daily_2025.parquet"
    daily.to_parquet(partition, index=False)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "status": "complete", "daily_rows": expected_rows,
        "unique_permnos": 1, "delisting_rows": 1, "ath_seed_rows": 1,
        "partitions": [{"year": 2025, "path": str(partition), "rows": expected_rows}],
    }), encoding="utf-8")
    delistings = tmp_path / "delistings.parquet"
    pd.DataFrame({
        "permno": [10001], "delisting_date": pd.to_datetime(["2025-01-04"]),
        "delisting_return": [-0.5],
    }).to_parquet(delistings, index=False)
    seed = tmp_path / "seed.parquet"
    pd.DataFrame({
        "permno": [10001], "prior_comparable_high": [12.0]
    }).to_parquet(seed, index=False)
    return manifest, delistings, seed


def test_crsp_audit_passes_valid_partition(tmp_path) -> None:
    paths = write_fixture(tmp_path, daily_rows())
    summary, report = audit_crsp_history(*paths, batch_size=1)
    assert summary["status"] == "pass"
    assert summary["daily_rows"] == 2
    assert report.loc[0, "status"] == "pass"


def test_crsp_audit_detects_duplicate_key_and_manifest_mismatch(tmp_path) -> None:
    data = daily_rows()
    data.loc[1, "date"] = data.loc[0, "date"]
    paths = write_fixture(tmp_path, data, expected_rows=3)
    summary, report = audit_crsp_history(*paths, batch_size=1)
    assert summary["status"] == "error"
    assert report.loc[0, "duplicate_keys"] == 1
    assert "row count" in report.loc[0, "errors"]


def test_crsp_audit_counts_legitimate_missing_market_fields(tmp_path) -> None:
    data = daily_rows()
    data.loc[0, ["open", "high", "low", "volume"]] = None
    data.loc[0, "total_return"] = None
    data.loc[0, "return_missing_flag"] = "M"
    paths = write_fixture(tmp_path, data)
    summary, report = audit_crsp_history(*paths)
    assert summary["status"] == "pass"
    assert summary["missing_volume_rows"] == 1
    assert summary["missing_total_return_rows"] == 1
    assert summary["unflagged_missing_total_return_rows"] == 0
    assert report.loc[0, "null_open"] == 1


def test_crsp_audit_reports_ohlc_inconsistency_as_warning(tmp_path) -> None:
    data = daily_rows()
    data.loc[0, "high"] = 9.5
    paths = write_fixture(tmp_path, data)
    summary, report = audit_crsp_history(*paths)
    assert summary["status"] == "warning"
    assert report.loc[0, "status"] == "warning"
    assert report.loc[0, "ohlc_high_violations"] == 1
