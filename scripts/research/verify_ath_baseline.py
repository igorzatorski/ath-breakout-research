"""Independent aggregation and sampled raw annual-return checks of ATH baseline."""
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ath_breakout.data.market_calendar import valid_nyse_sessions  # noqa: E402
from audit_ath_baseline import sha256  # noqa: E402


def main(out):
    manifest = json.loads((out / "manifest.json").read_text())
    for name, digest in manifest["artifacts"].items():
        assert sha256(out / name) == digest
    z = pd.read_parquet(out / "events.parquet")
    summary = pd.read_csv(out / "summary.csv")
    samples = {
        "annual_spy": ("excess_spy", z.loc[z.excess_spy.notna()]),
        "momentum_common": ("new_excess", z.loc[z.excess_spy.notna() & z.new_excess.notna() & z.excess_control.notna()]),
        "capm_common": ("momentum_gap", z.loc[z.stock_car.notna() & z.old_car.notna() & z.momentum_car.notna()]),
    }
    assert [len(v[1]) for v in samples.values()] == [71961, 43824, 39561]
    checks = 0
    for sample, (metric, f) in samples.items():
        for variant in ["baseline", "nonoverlap"]:
            v = f if variant == "baseline" else f.loc[f.nonoverlap]
            row = summary.loc[summary["sample"].eq(sample) & summary.period.eq("all") & summary.variant.eq(variant)].iloc[0]
            assert len(v) == row.events
            assert math.isclose(math.fsum(v[metric]) / len(v), row["mean"], abs_tol=1e-12)
            checks += 1
        for identity in ["permno", "permco"]:
            saved = pd.read_csv(out / f"contributors_{sample}_{identity}.csv").set_index(identity)
            groups = {}
            for key, value in zip(f[identity], f[metric]):
                groups.setdefault(key, []).append(value)
            for key, values in groups.items():
                assert len(values) == saved.loc[key, "events"]
                assert math.isclose(math.fsum(values) / len(f), saved.loc[key, "contribution"], abs_tol=1e-12)
                checks += 1
    # Infer the past-only rule with a separately implemented group loop.
    cal = valid_nyse_sessions("1994-01-01", "2026-06-30")
    selection = pd.read_parquet(out / "selection.parquet")
    for _, f in selection.groupby("permco"):
        last = -100000
        for row in f.sort_values(["date", "permno", "event_id"]).itertuples():
            pos = int(cal.searchsorted(row.date))
            expected = pos - last >= 252
            assert expected == row.nonoverlap
            if expected:
                last = pos
            checks += 1
    # Largest positive/negative annual observations plus a reproducible random sample.
    f = samples["annual_spy"][1]
    selected = pd.concat([f.nlargest(10, "excess_spy"), f.nsmallest(10, "excess_spy"),
                          f.sample(30, random_state=20261016)]).drop_duplicates("event_id")
    cache = {}
    for year in range(int(selected.entry_date.dt.year.min()), int(selected.exit_date.dt.year.max()) + 1):
        path = ROOT / f"data/raw/crsp/daily_by_year/daily_{year}.parquet"
        cache[year] = pd.read_parquet(path, columns=["permno", "date", "open", "close", "total_return", "delisting_flag"],
                                      filters=[("permno", "in", selected.permno.tolist())])
    raw = pd.concat(cache.values()).set_index(["permno", "date"]).sort_index()
    max_error = 0.
    for row in selected.itertuples():
        schedule = valid_nyse_sessions(row.entry_date, row.exit_date)
        assert len(schedule) == 252
        prices = raw.loc[row.permno].reindex(schedule)
        wealth = float(prices.iloc[0]["close"] / prices.iloc[0]["open"])
        assert prices.iloc[0].delisting_flag != "Y"
        for day in prices.iloc[1:].itertuples():
            assert np.isfinite(day.total_return) and day.total_return >= -1
            wealth *= 1 + day.total_return
            if day.delisting_flag == "Y":
                break
        error = abs(wealth - 1 - row.stock_return)
        max_error = max(max_error, error)
        assert error < 1e-9, (row.event_id, error)
    # Calendar-stratified feature profiles prevent aggregate history mixes being hidden.
    u = pd.read_parquet(out / "uncertain_candidates.parquet")
    rows = []
    for label, frame in [("qualified", z), ("uncertain_candidates", u)]:
        for year, f in frame.groupby(frame.date.dt.year):
            row = dict(group=label, year=int(year), events=len(f), securities=f.permno.nunique())
            for metric in ["market_cap", "adv21", "vol63"]:
                row[metric + "_median"] = f[metric].median()
                row[metric + "_observed"] = int(f[metric].notna().sum())
            rows.append(row)
    pd.DataFrame(rows).to_csv(out / "history_features_by_year.csv", index=False)
    results = dict(status="passed", aggregation_and_selection_checks=checks,
                   raw_return_checks=len(selected), maximum_raw_return_error=max_error,
                   source_manifest_sha256=sha256(out / "manifest.json"),
                   verification_code_sha256=sha256(Path(__file__)),
                   history_features_sha256=sha256(out / "history_features_by_year.csv"),
                   scope="Arithmetic, saved hash consistency, selection and sampled annual stock returns; not provider truth or bootstrap coverage calibration")
    (out / "independent_verification.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
