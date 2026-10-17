"""Independent checks of saved momentum matches and return aggregation."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from extend_ath_annual import sha256  # noqa: E402


def main():
    out = Path(sys.argv[1])
    manifest = json.loads((out / "manifest.json").read_text())
    for name, expected in manifest["artifacts"].items():
        assert sha256(out / name) == expected
    r = pd.read_parquet(out / "event_returns.parquet")
    assert not r.event_id.duplicated().any()
    assert np.allclose(r.new_excess, r.stock_return-r.new_control_return, equal_nan=True)
    assert np.allclose(r.change, (r.control_return-r.new_control_return).where(r.stock_return.notna()), equal_nan=True)
    common = r.loc[r.new_excess.notna() & r.excess_control.notna() & r.excess_spy.notna()]
    assert len(common) == manifest["common_events"]
    checks = 0
    for year in [1994, 2000, 2009, 2020, 2025]:
        m = pd.read_parquet(out / f"by_year/matches_{year}.parquet")
        if m.empty:
            continue
        assert not m.duplicated(["event_id", "control_permco"]).any()
        assert m.groupby("event_id").size().eq(5).all()
        assert m.control_permco.ne(m.event_permco).all()
        assert m.momentum_gap.abs().le(.1+1e-12).all()
        assert m.size_ratio.between(.5-1e-12, 2+1e-12).all()
        assert m.vol_ratio.between(1/1.5-1e-12, 1.5+1e-12).all()
        q = pd.read_parquet(out / f"by_year/control_returns_{year}.parquet")
        expected = q.groupby("event_id").value.agg(["mean", "count"])
        z = r.set_index("event_id").reindex(expected.index)
        assert np.allclose(z.new_control_return, expected["mean"].where(expected["count"].eq(5)), equal_nan=True)
        sample = m.iloc[np.linspace(0, len(m)-1, min(8, len(m)), dtype=int)]
        selected = set(sample.permno)
        raw = pd.concat([pd.read_parquet(ROOT / f"data/raw/crsp/daily_by_year/daily_{y}.parquet", columns=["date", "permno", "total_return"]) for y in [year-1, year]])
        raw = raw.loc[raw.permno.isin(selected)].set_index(["date", "permno"])
        cal = valid_nyse_sessions(f"{year-1}-01-01", f"{year}-12-31")
        for row in sample.itertuples():
            t = cal.get_loc(row.date)
            window = cal[t-251:t-20]
            values = raw.total_return.reindex(pd.MultiIndex.from_product([window, [row.permno]])).to_numpy()
            assert len(values) == 231 and np.isfinite(values).all() and (values >= -1).all()
            assert np.isclose(np.prod(1+values)-1, row.control_momentum, atol=1e-10, rtol=1e-10)
            checks += 1
    print(f"Verified artifact hashes, matching constraints, paired arithmetic, basket aggregation; {checks} independent production momentum products.")


if __name__ == "__main__":
    main()
