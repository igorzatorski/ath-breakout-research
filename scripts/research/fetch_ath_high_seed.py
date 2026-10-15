"""Read-only WRDS repair export; never overwrite the legacy Data Layer seed."""
import json
from pathlib import Path
import sys

import pandas as pd
import wrds

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.data.maintenance.update_data_layer import resolve_username  # noqa: E402
from ath_breakout.data.wrds_credentials import load_wrds_password  # noqa: E402

OUTPUT = ROOT / "outputs/research/ath/shared_inputs/high_seed_before_1993.parquet"


def main():
    if OUTPUT.exists():
        print("Existing isolated seed retained; no query or overwrite")
        return
    username = resolve_username()
    password = load_wrds_password(username)
    if not password:
        raise RuntimeError("Saved WRDS credential unavailable")
    connection = wrds.Connection(autoconnect=False, wrds_username=username,
                                 wrds_password=password,
                                 wrds_connect_args={"connect_timeout": 15, "sslmode": "require"})
    connection._Connection__make_sa_engine_conn(raise_err=True)
    permnos = pd.read_parquet(ROOT / "data/processed/crsp/universe_permnos.parquet").permno.astype(int).tolist()
    print("Read-only WRDS high-history seed query started", flush=True)
    query = """
        SELECT permno,
          MAX(dlyhigh / NULLIF(dlycumfacpr, 0)) FILTER
            (WHERE dlyhigh > 0 AND dlycumfacpr > 0) AS prior_comparable_high,
          MAX(dlyclose / NULLIF(dlycumfacpr, 0)) FILTER
            (WHERE dlyclose > 0 AND dlycumfacpr > 0) AS prior_comparable_close,
          MIN(dlycaldt) AS first_observation_date,
          MAX(dlycaldt) AS last_observation_date,
          COUNT(*) AS observation_count,
          COUNT(*) FILTER (WHERE dlydelflg != 'Y' AND
            (dlyhigh IS NULL OR dlyhigh <= 0 OR dlycumfacpr IS NULL OR dlycumfacpr <= 0)) AS missing_high_rows
        FROM crsp_q_stock.dsf_v2
        WHERE permno = ANY(%(permnos)s) AND dlycaldt < '1993-01-01'
        GROUP BY permno ORDER BY permno
    """
    try:
        frame = connection.raw_sql(query, params={"permnos": permnos},
                                   date_cols=["first_observation_date", "last_observation_date"])
    finally:
        connection.close()
    assert not frame.permno.duplicated().any()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUTPUT, index=False)
    OUTPUT.with_suffix(".json").write_text(json.dumps({"query": query, "permnos_requested": len(permnos),
        "rows": len(frame), "source": "WRDS crsp_q_stock.dsf_v2", "scope": "pre-1993 high/close bounds and missing-high audit"}, indent=2))
    print(f"Saved isolated repaired seed: {len(frame)} securities", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Seed repair failed: {type(exc).__module__}.{type(exc).__name__}", flush=True)
        raise SystemExit(1)
