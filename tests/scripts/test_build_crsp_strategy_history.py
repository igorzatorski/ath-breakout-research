import json

import pandas as pd

from scripts.maintenance.build_crsp_strategy_history import build_strategy_history
from tests.data.test_crsp_processing import crsp_rows


def test_builds_and_resumes_chronological_strategy_partitions(tmp_path) -> None:
    raw = crsp_rows(205)
    raw["date"] = list(pd.bdate_range("1993-01-04", periods=199)) + list(
        pd.bdate_range("1994-01-03", periods=6)
    )
    raw_paths = []
    partitions = []
    for year in (1993, 1994):
        part = raw[raw["date"].dt.year == year]
        path = tmp_path / f"raw_{year}.parquet"
        part.to_parquet(path, index=False)
        raw_paths.append(path)
        partitions.append({"year": year, "path": str(path), "rows": len(part)})
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text(
        json.dumps({"status": "complete", "partitions": partitions}),
        encoding="utf-8",
    )
    seed = tmp_path / "seed.parquet"
    pd.DataFrame(
        {"permno": pd.Series(dtype=int), "prior_comparable_high": pd.Series(dtype=float)}
    ).to_parquet(seed, index=False)
    output = tmp_path / "processed"
    manifest = tmp_path / "processed_manifest.json"

    first = build_strategy_history(source_manifest, seed, output, manifest)
    second = build_strategy_history(source_manifest, seed, output, manifest)

    year_two = pd.read_parquet(output / "strategy_1994.parquet")
    assert first["status"] == "complete"
    assert first["output_rows"] == 205
    assert year_two.iloc[0]["sma_200"] == 99.75
    assert second["partitions"][0]["status"] == "existing"
    assert second["partitions"][1]["status"] == "existing"

    # A changed earlier partition invalidates downstream stateful features.
    import os
    stat = raw_paths[0].stat()
    os.utime(raw_paths[0], ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    third = build_strategy_history(source_manifest, seed, output, manifest)
    assert [p["status"] for p in third["partitions"]] == ["built", "built"]
