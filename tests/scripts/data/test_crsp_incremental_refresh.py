"""Incremental queries must not download observations already present."""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from scripts.data.acquisition import download_wrds_crsp_daily_history as daily


def test_queries_only_missing_dates_and_new_securities():
    previous = {"status": "complete", "permnos": [1, 2], "start_date": "1993-01-01", "end_date": "2026-06-30"}
    assert daily.incremental_queries(previous, [1, 2], pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-31")) == []
    queries = daily.incremental_queries(previous, [1, 2, 3], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-09-30"))
    assert queries == [([3], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-09-30")),
                       ([1, 2], pd.Timestamp("2026-07-01"), pd.Timestamp("2026-09-30"))]
    assert daily.incremental_queries({"status": "running", "previous_snapshot": previous}, [1, 2, 3], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-09-30")) == queries


def frame(permno, date, close):
    record = {name: None for name in daily.CRSP_DAILY_COLUMNS}
    record.update(permno=permno, date=pd.Timestamp(date), close=close)
    return pd.DataFrame([record])


def test_merge_preserves_existing_prices_and_orders_keys(tmp_path, monkeypatch):
    path = tmp_path / "daily.parquet"
    pq.write_table(pa.Table.from_pandas(frame(2, "2026-06-30", 20), schema=daily.parquet_schema(), preserve_index=False), path)
    monkeypatch.setattr(daily, "stream_crsp_daily", lambda *args, **kwargs: iter([frame(1, "2026-07-01", 10)]))
    rows, chunks = daily.extend_year_partition(None, [([1], pd.Timestamp("2026-07-01"), pd.Timestamp("2026-07-01"))], path, 100)
    data = pd.read_parquet(path)
    assert (rows, chunks) == (2, 1)
    assert data.permno.tolist() == [1, 2]
    assert data.close.tolist() == [10, 20]


def test_duplicate_incremental_data_do_not_replace_original(tmp_path, monkeypatch):
    path = tmp_path / "daily.parquet"
    original = frame(1, "2026-06-30", 20)
    pq.write_table(pa.Table.from_pandas(original, schema=daily.parquet_schema(), preserve_index=False), path)
    before = path.read_bytes()
    monkeypatch.setattr(daily, "stream_crsp_daily", lambda *args, **kwargs: iter([original]))
    with pytest.raises(ValueError, match="duplicate"):
        daily.extend_year_partition(None, [([1], pd.Timestamp("2026-06-30"), pd.Timestamp("2026-06-30"))], path, 100)
    assert path.read_bytes() == before
