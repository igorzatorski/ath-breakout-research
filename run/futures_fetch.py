"""Download public, commit-pinned research CSVs without executing upstream code."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "164328bd76d2937d3dd61491377704c488283bc2"
BASE = f"https://raw.githubusercontent.com/pst-group/pysystemtrade/{COMMIT}/"
OUT = ROOT / "data/raw/futures/pysystemtrade" / COMMIT
MAPPING = {
    "ES": "SP500",
    "NQ": "NASDAQ",
    "RTY": "RUSSELL_mini",
    "ZT": "US2",
    "ZN": "US10",
    "ZB": "US20",
    "6E": "EUR",
    "6J": "JPY",
    "6B": "GBP",
    "6A": "AUD",
    "6C": "CAD",
    "CL": "CRUDE_W",
    "NG": "GAS_US",
    "GC": "GOLD",
    "SI": "SILVER",
    "HG": "COPPER",
    "ZC": "CORN",
    "ZW": "WHEAT",
    "ZS": "SOYBEAN",
    "LE": "LIVECOW",
}


def fetch(relative):
    target = OUT / relative
    if not target.exists():
        request = Request(
            BASE + relative, headers={"User-Agent": "futures-research-audit"}
        )
        try:
            with urlopen(request, timeout=45) as response:
                content = response.read()
        except HTTPError as exc:
            if exc.code == 404 and "/roll_calendars_csv/" in relative:
                return dict(path=relative, status="not_published", url=BASE + relative)
            raise RuntimeError(f"Failed to fetch {relative}: HTTP {exc.code}") from exc
        if not content or content.startswith(b"version https://git-lfs"):
            raise ValueError(f"Missing content or LFS pointer: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    data = target.read_bytes()
    return dict(
        path=relative,
        bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        url=BASE + relative,
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = ["LICENSE", "docs/data.md", "sysobjects/adjusted_prices.py"]
    paths += [
        f"data/futures/csvconfig/{name}.csv"
        for name in ["instrumentconfig", "spreadcosts", "rollconfig"]
    ]
    paths += [
        f"data/futures/{folder}/{code}.csv"
        for code in MAPPING.values()
        for folder in [
            "adjusted_prices_csv",
            "multiple_prices_csv",
            "roll_calendars_csv",
        ]
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, paths))
    manifest = dict(
        repository="pst-group/pysystemtrade",
        commit=COMMIT,
        mapping=MAPPING,
        files=records,
        note="Public shipped research snapshot, not a live vendor feed; raw data not redistributed",
    )
    (OUT / "download_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(
        f"Preserved {sum('bytes' in r for r in records)} files ({sum(r.get('bytes', 0) for r in records) / 1e6:.1f} MB) at {OUT}"
    )
    print(
        "Unavailable optional calendars:",
        [r["path"] for r in records if r.get("status")],
    )


if __name__ == "__main__":
    main()
