"""Read-only isolated CRSP SIC history export and official FF12 mapping."""
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
import zipfile

import pandas as pd
import wrds

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.data.maintenance.update_data_layer import resolve_username  # noqa: E402
from ath_breakout.data.wrds_credentials import load_wrds_password  # noqa: E402

OUT = ROOT/'outputs/research/ath/shared_inputs/industry_history_v001'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT/'sic_history.parquet'
    if not target.exists():
        username = resolve_username()
        password = load_wrds_password(username)
        if not password:
            raise RuntimeError('Saved WRDS credential unavailable')
        print('Connecting to WRDS once; approve Duo if prompted', flush=True)
        connection = wrds.Connection(autoconnect=False, wrds_username=username, wrds_password=password,
            wrds_connect_args={'connect_timeout': 30, 'sslmode': 'require', 'options': '-c statement_timeout=120000'})
        connection._Connection__make_sa_engine_conn(raise_err=True)
        ids = pd.read_parquet(ROOT/'data/processed/crsp/universe_permnos.parquet').permno.astype(int).tolist()
        query = """SELECT DISTINCT permno, secinfostartdt::text AS effective_from,
            secinfoenddt::text AS effective_to, siccd
            FROM crsp_q_stock.stksecurityinfohist
            WHERE permno = ANY(%(ids)s) AND secinfostartdt <= '2026-06-30'
              AND (secinfoenddt >= '1993-01-01' OR secinfoenddt IS NULL)
            ORDER BY permno, effective_from, effective_to, siccd"""
        try:
            frame = connection.raw_sql(query, params={'ids': ids})
        finally:
            connection.close()
        frame.to_parquet(target, index=False)
        (OUT/'sic_query.json').write_text(json.dumps(dict(query=query, securities_requested=len(ids),
            rows=len(frame), retrieved_at=pd.Timestamp.now(tz='UTC').isoformat(),
            source='WRDS crsp_q_stock.stksecurityinfohist',
            limitation='Effective-dated current-vintage history; original publication/revision timestamps unavailable'), indent=2))
        print(f'Saved {len(frame)} history records', flush=True)
    else:
        print('Existing isolated SIC export retained', flush=True)
    definition = OUT/'Siccodes12.txt'
    if not definition.exists():
        url = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Siccodes12.zip'
        data = urllib.request.urlopen(url, timeout=30).read()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            name = next(n for n in archive.namelist() if n.lower().endswith('.txt'))
            definition.write_bytes(archive.read(name))
        (OUT/'mapping_source.json').write_text(json.dumps(dict(url=url,
            retrieved_at=pd.Timestamp.now(tz='UTC').isoformat(), sha256=hashlib.sha256(definition.read_bytes()).hexdigest(),
            limitation='Frozen current FF12 SIC grouping, not historical GICS or replication of FF portfolio construction'), indent=2))
    print('Isolated classification inputs ready', flush=True)


if __name__ == '__main__':
    main()
