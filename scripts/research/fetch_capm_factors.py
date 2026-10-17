"""Cache the official daily Kenneth French factors without WRDS access."""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile

import pandas as pd

from extend_ath_annual import sha256

ROOT = Path(__file__).resolve().parents[2]
URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
TARGET = ROOT / "outputs/research/ath/shared_inputs/capm_factors_20261016"


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    archive = TARGET / "official_daily_factors.zip"
    if not archive.exists():
        request = urllib.request.Request(URL, headers={"User-Agent": "ATHAcademicResearch/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            assert len(z.namelist()) == 1
        archive.write_bytes(payload)
        (TARGET / "download.json").write_text(json.dumps({"url": URL, "retrieved_utc": datetime.now(timezone.utc).isoformat(), "sha256": sha256(archive)}, indent=2))
    metadata = json.loads((TARGET / "download.json").read_text())
    assert sha256(archive) == metadata["sha256"]
    with zipfile.ZipFile(archive) as z:
        txt = z.read(z.namelist()[0]).decode("utf-8-sig")
    lines = [s for s in txt.splitlines() if re.match(r"^\d{8},", s)]
    d = pd.read_csv(io.StringIO("date,mkt_rf,smb,hml,rf\n"+"\n".join(lines)))
    d.date = pd.to_datetime(d.date.astype(str), format="%Y%m%d")
    for col in ["mkt_rf", "smb", "hml", "rf"]:
        assert d[col].gt(-99).all(), "Missing-factor sentinel"
        d[col] /= 100
    assert not d.date.duplicated().any()
    d.to_parquet(TARGET / "factors.parquet", index=False)
    print({"rows": len(d), "first": str(d.date.min().date()), "last": str(d.date.max().date()), "archive_sha256": sha256(archive)})


if __name__ == "__main__":
    main()
