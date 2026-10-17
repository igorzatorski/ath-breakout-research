"""Independent saved-output aggregation and direct pre-beta/CAR checks."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from extend_ath_annual import sha256
from fetch_capm_factors import TARGET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402


def main():
    out = Path(sys.argv[1])
    manifest = json.loads((out / "manifest.json").read_text())
    for name, expected in manifest["artifacts"].items():
        assert sha256(out / name) == expected
    r = pd.read_parquet(out / "event_results.parquet").set_index("event_id")
    assert len(r) == 75884 and not r.index.duplicated().any()
    assert np.allclose(r.momentum_gap, r.stock_car-r.momentum_car, equal_nan=True)
    assert np.allclose(r.old_gap, r.stock_car-r.old_car, equal_nan=True)
    factors = pd.read_parquet(TARGET / "factors.parquet").set_index("date")
    direct = 0
    for year in range(1994, 2027):
        q = pd.read_parquet(out / f"by_year/query_results_{year}.parquet")
        for kind, gross_column in [("old", "control_return"), ("momentum", "new_control_return")]:
            controls = q.loc[q.kind.eq(kind)]
            gross = controls.groupby("event_id").stock_return.agg(["mean", "count"])
            expected = gross["mean"].where(gross["count"].eq(5))
            assert np.allclose(expected, r[gross_column].reindex(expected.index), equal_nan=True)
            car = controls.groupby("event_id").car.agg(["mean", "count"])
            expected_car = car["mean"].where(car["count"].eq(5))
            assert np.allclose(expected_car, r[f"{kind}_car"].reindex(expected_car.index), equal_nan=True)
        if year not in [1994, 2002, 2009, 2021, 2025]:
            continue
        unique = pd.read_parquet(out / f"by_year/unique_security_dates_{year}.parquet")
        valid = unique.loc[unique.car.notna()]
        samples = valid.sample(min(7, len(valid)), random_state=543)
        raw = pd.concat([pd.read_parquet(ROOT / f"data/raw/crsp/daily_by_year/daily_{y}.parquet", columns=["date", "permno", "total_return", "delisting_flag"]) for y in range(max(1993, year-2), min(year+2, 2026)+1)])
        raw = raw.loc[raw.permno.isin(samples.permno)].set_index(["date", "permno"])
        cal = valid_nyse_sessions(f"{year-2}-01-01", f"{year+2}-01-31")
        for row in samples.itertuples():
            t = cal.get_loc(row.date)
            days = cal[t-252:t]
            pre = raw.total_return.reindex(pd.MultiIndex.from_product([days, [row.permno]])).to_numpy()
            f = factors.reindex(days)
            ok = np.isfinite(pre) & (pre >= -1)
            b = np.linalg.lstsq(np.column_stack([np.ones(ok.sum()), f.mkt_rf.to_numpy()[ok]]), pre[ok]-f.rf.to_numpy()[ok], rcond=None)[0]
            assert np.isclose(b[1], row.beta, atol=1e-10) and ok.sum() == row.estimation_count
            post_days = cal[t+2:t+253]
            assert len(post_days) == 251 and post_days[-1] <= pd.Timestamp("2026-06-30")
            post = raw.reindex(pd.MultiIndex.from_product([post_days, [row.permno]]))
            after = False
            total = 0.
            for day, ret, terminal in zip(post_days, post.total_return, post.delisting_flag):
                total += (0 if after else ret)-factors.at[day, "rf"]-(0 if after else b[1]*factors.at[day, "mkt_rf"])
                after = after or terminal == "Y"
            assert np.isclose(total, row.car, atol=1e-10)
            direct += 1
    print(f"Passed all artifact hashes, all-year old/new gross and CAR baskets, paired identities, {direct} independent OLS/CAR reconstructions.")
    (out / "independent_verification.json").write_text(json.dumps({"status": "passed", "direct_reconstructions": direct, "all_year_baskets": True}, indent=2))


if __name__ == "__main__":
    main()
