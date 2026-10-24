"""Inspect priced vs other-maturity observations without changing the baseline."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from run.futures_audit import load_csv
from run.futures_fetch import OUT as RAW, COMMIT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/trend_following_futures/gap_diagnostic"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    cases = [
        ("6E", "EUR", "2018-10-22", "2018-10-25"),
        ("6J", "JPY", "2018-10-22", "2018-10-25"),
        ("ZC", "CORN", "2019-12-23", "2020-01-03"),
    ]
    spy_dates = pd.DatetimeIndex(
        pd.read_parquet(ROOT / "data/raw/yfinance/SPY.parquet").date
    )
    sources = []
    for root, code, start, end in cases:
        path = RAW / f"data/futures/multiple_prices_csv/{code}.csv"
        sources.append(
            dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        )
        frame = load_csv(path).loc[start:end]
        for date, day in frame.groupby(frame.index.normalize()):
            if date not in spy_dates:
                continue
            rows.append(
                dict(
                    root=root,
                    date=str(date.date()),
                    priced_contract=int(day.PRICE_CONTRACT.dropna().iloc[-1]),
                    priced_observations=int(day.PRICE.notna().sum()),
                    forward_contract=int(day.FORWARD_CONTRACT.dropna().iloc[-1]),
                    forward_observations=int(day.FORWARD.notna().sum()),
                    distinct_forward_marks=int(day.FORWARD.nunique()),
                    carry_observations=int(day.CARRY.notna().sum()),
                )
            )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "gap_evidence.csv", index=False)
    manifest = dict(
        source_commit=COMMIT,
        source_files=sources,
        baseline_changed=False,
        performance_recomputed=False,
        scope="Three selected problematic intervals; not a complete exchange-calendar classification",
        finding="Missing priced-maturity observations coexist with other-maturity observations; exact upstream cause unverified",
    )
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
