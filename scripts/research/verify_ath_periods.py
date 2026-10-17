"""Independent period, influence, tail and composition reconciliation."""
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from diagnose_ath_periods import SOURCE  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402


def main(out):
    manifest = json.loads((out / "manifest.json").read_text())
    for name, digest in manifest["artifacts"].items():
        assert sha256(out / name) == digest
    z = pd.read_parquet(out / "events.parquet")
    original = pd.read_parquet(SOURCE / "events.parquet").set_index("event_id").loc[z.event_id]
    for col in ["stock_return", "spy_return", "excess_spy", "new_excess", "stock_car", "momentum_gap"]:
        assert np.allclose(z[col], original[col], equal_nan=True, atol=1e-12)
    assert np.array_equal(z.nonoverlap, original.nonoverlap)
    assert np.array_equal(z.quintile_6_1, original.quintile_6_1, equal_nan=True)
    expected = np.where(z.date < pd.Timestamp("2010-01-01"), "early",
                        np.where(z.date < pd.Timestamp("2018-01-01"), "middle", "recent"))
    assert np.array_equal(expected, z.period)
    base = z.loc[z.common_momentum & z.excess_spy.notna()]
    main = base.loc[base.quintile_6_1.eq(5)]
    assert len(main) == 23712 and len(base) == 65650
    checks = 0
    for row in pd.read_csv(out / "period_summary.csv").itertuples():
        f = base if row.variant == "baseline" else base.loc[base[f"quintile_{row.variant.split('_top')[0]}"].eq(5)]
        if row.overlap == "nonoverlap":
            f = f.loc[f.nonoverlap]
        f = f.loc[f.period.eq(row.period)]
        assert len(f) == row.events
        for column, field in [("stock_return", "stock"), ("spy_return", "spy"), ("excess_spy", "excess")]:
            assert math.isclose(math.fsum(f[column])/len(f), getattr(row, field), abs_tol=1e-12)
            checks += 1
    for filename, key in [("year_contributions.csv", "year"),
                           ("company_contributions.csv", "permco"),
                           ("tail_contributions.csv", "excess_bucket")]:
        table = pd.read_csv(out / filename)
        for row in table.itertuples():
            period = main.loc[main.period.eq(row.period)]
            f = period.loc[period[key].astype(str).eq(str(getattr(row, key)))]
            assert len(f) == row.events
            assert math.isclose(math.fsum(f.excess_spy)/len(period), row.contribution, abs_tol=1e-12)
            checks += 1
    # Explicit two-period identity, avoiding the production decomposition helper.
    for grouping in ["size_bucket", "vol_bucket", "size_vol_cell", "excess_bucket"]:
        a = main.loc[main.period.eq("early")]
        b = main.loc[main.period.eq("recent")]
        table = pd.read_csv(out / f"mix_within_{grouping}.csv")
        reconstructed = []
        for row in table.itertuples():
            key = getattr(row, grouping)
            av = a.loc[a[grouping].astype(str).eq(str(key)), "excess_spy"].tolist()
            bv = b.loc[b[grouping].astype(str).eq(str(key)), "excess_spy"].tolist()
            wa, wb = len(av)/len(a), len(bv)/len(b)
            ma, mb = (math.fsum(av)/len(av) if av else None), (math.fsum(bv)/len(bv) if bv else None)
            actual = (math.fsum(bv)/len(b))-(math.fsum(av)/len(a))
            assert math.isclose(actual, row.total_change, abs_tol=1e-12)
            if av and bv:
                assert math.isclose((wb-wa)*(ma+mb)/2, row.mix, abs_tol=1e-12)
                assert math.isclose((mb-ma)*(wa+wb)/2, row.within, abs_tol=1e-12)
            reconstructed.append(actual)
            checks += 1
        assert math.isclose(math.fsum(reconstructed), b.excess_spy.mean()-a.excess_spy.mean(), abs_tol=1e-12)
    for row in pd.read_csv(out / "leave_one_year_out.csv").itertuples():
        f = main.loc[main.period.eq(row.period) & main.year.ne(row.omitted_year)]
        assert len(f) == row.events and math.isclose(f.excess_spy.mean(), row.mean, abs_tol=1e-12)
        checks += 1
    # Check every main-event size percentile against the full saved PIT cross section.
    size_checks = 0
    for year in range(1994, 2027):
        events = main.loc[main.year.eq(year) & main.size_percentile.notna()]
        if events.empty:
            continue
        pool = pd.read_parquet(out / f"by_year/size_pool_{year}.parquet")
        days = dict(tuple(pool.groupby("date")))
        for date, f in events.groupby("date"):
            values = np.sort(days[date].market_cap.to_numpy())
            for row in f.itertuples():
                expected = (np.searchsorted(values, row.market_cap, "left")+
                            np.searchsorted(values, row.market_cap, "right"))/(2*len(values))
                assert math.isclose(expected, row.size_percentile, abs_tol=1e-12)
                assert row.size_population == len(values)
                size_checks += 1
    comp = pd.read_csv(out / "stock_spy_decomposition.csv")
    assert np.allclose(comp.stock_component+comp.benchmark_component, comp.excess_change, atol=1e-12)
    for row in pd.read_csv(out / "matched_capm_context.csv").itertuples():
        f = main.loc[main.period.eq(row.period)]
        if row.sample == "capm_common":
            f = f.loc[f.stock_car.notna() & f.old_car.notna() & f.momentum_car.notna()]
            for col, field in [("stock_car", "stock_car"), ("momentum_car", "control_car"),
                               ("momentum_gap", "car_gap")]:
                assert math.isclose(f[col].mean(), getattr(row, field), abs_tol=1e-12)
            assert math.isclose(row.stock_car-row.control_car, row.car_gap, abs_tol=1e-12)
        else:
            f = f.loc[f.new_excess.notna()]
            assert np.isnan(row.stock_car) and np.isnan(row.control_car) and np.isnan(row.car_gap)
        assert len(f) == row.events
        assert math.isclose(f.stock_return.mean(), row.stock, abs_tol=1e-12)
        assert math.isclose(f.spy_return.mean(), row.spy, abs_tol=1e-12)
        assert math.isclose(f.new_excess.mean(), row.excess_controls12, abs_tol=1e-12)
        checks += 1
    result = dict(status="passed", numerical_checks=checks, main_event_size_percentiles_checked=size_checks,
                  main_events=len(main), source_returns_filters_and_nonoverlap_preserved=True,
                  manifest_sha256=sha256(out / "manifest.json"), verifier_sha256=sha256(Path(__file__)),
                  scope="Saved hashes, frozen source identity, period/group means, all main size ranks, attribution identities; not causal proof or bootstrap calibration")
    (out / "independent_verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
