"""Read-only source audit and daily preparation for a futures research prototype."""

from pathlib import Path

import numpy as np
import pandas as pd

from run.futures_fetch import OUT as RAW, MAPPING

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/trend_following_futures/source_audit"


def load_csv(path):
    frame = pd.read_csv(path)
    index = pd.to_datetime(frame.pop(frame.columns[0]), format="mixed")
    frame.index = index
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError(f"Unordered or duplicate source timestamps: {path}")
    return frame


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = pd.read_csv(
        RAW / "data/futures/csvconfig/instrumentconfig.csv"
    ).set_index("Instrument")
    spreads = pd.read_csv(RAW / "data/futures/csvconfig/spreadcosts.csv").set_index(
        "Instrument"
    )
    coverage = []
    prepared = []
    for root, code in MAPPING.items():
        adjusted = (
            load_csv(RAW / f"data/futures/adjusted_prices_csv/{code}.csv")
            .iloc[:, 0]
            .rename("adjusted")
        )
        multiple = load_csv(RAW / f"data/futures/multiple_prices_csv/{code}.csv")
        joint = multiple.join(adjusted, how="inner")
        valid = joint.loc[
            np.isfinite(joint.PRICE)
            & np.isfinite(joint.adjusted)
            & joint.PRICE_CONTRACT.notna()
        ].copy()
        # A source roll changes the priced contract; forward must identify the new leg.
        roll = valid.PRICE_CONTRACT.ne(valid.PRICE_CONTRACT.shift())
        roll.iloc[0] = False
        previous_price = valid.PRICE.shift()
        previous_forward = valid.FORWARD.shift()
        previous_forward_id = valid.FORWARD_CONTRACT.shift()
        expected_diff = valid.PRICE - previous_price.where(~roll, previous_forward)
        observed_diff = valid.adjusted.diff()
        comparable = expected_diff.notna() & observed_diff.notna()
        errors = (observed_diff - expected_diff).abs()
        mismatches = comparable & (errors > (1e-6 + valid.PRICE.abs() * 1e-8))
        bad_roll_ids = roll & valid.PRICE_CONTRACT.ne(previous_forward_id)
        # Preserve raw intraday data. Only derive one last valid row per source date.
        valid["date"] = valid.index.normalize()
        valid["roll_events"] = roll.astype(int)
        daily = valid.groupby("date").tail(1).set_index("date")
        daily["roll_events"] = valid.groupby("date").roll_events.sum()
        daily["root"] = root
        daily["source_code"] = code
        daily["point_value"] = float(metadata.loc[code, "Pointsize"])
        daily["commission_per_unit"] = float(metadata.loc[code, "PerBlock"])
        daily["spread_price_cost"] = float(spreads.loc[code, "SpreadCost"])
        daily = daily[
            [
                "root",
                "source_code",
                "adjusted",
                "PRICE",
                "PRICE_CONTRACT",
                "FORWARD",
                "FORWARD_CONTRACT",
                "roll_events",
                "point_value",
                "commission_per_unit",
                "spread_price_cost",
            ]
        ]
        prepared.append(daily.reset_index())
        coverage.append(
            dict(
                root=root,
                source_code=code,
                first_date=str(daily.index[0].date()),
                last_date=str(daily.index[-1].date()),
                source_rows=len(joint),
                valid_rows=len(valid),
                daily_rows=len(daily),
                adjusted_missing=int(joint.adjusted.isna().sum()),
                priced_missing=int(joint.PRICE.isna().sum()),
                roll_events=int(roll.sum()),
                comparable_changes=int(comparable.sum()),
                adjustment_mismatches=int(mismatches.sum()),
                unexplained_roll_contracts=int(bad_roll_ids.sum()),
                max_change_error=float(errors.loc[comparable].max()),
                point_value=float(metadata.loc[code, "Pointsize"]),
                currency=metadata.loc[code, "Currency"],
                source_description=metadata.loc[code, "Description"],
                calendar_published=(
                    RAW / f"data/futures/roll_calendars_csv/{code}.csv"
                ).exists(),
            )
        )
        if mismatches.any() or bad_roll_ids.any():
            valid.loc[mismatches | bad_roll_ids].to_csv(
                OUT / f"{root}_adjustment_exceptions.csv"
            )
    pd.concat(prepared, ignore_index=True).to_parquet(
        OUT / "daily_markets.parquet", index=False
    )
    table = pd.DataFrame(coverage)
    table.to_csv(OUT / "coverage.csv", index=False)
    print(
        table[
            [
                "root",
                "source_code",
                "first_date",
                "last_date",
                "daily_rows",
                "roll_events",
                "adjustment_mismatches",
                "unexplained_roll_contracts",
                "point_value",
            ]
        ].to_string(index=False)
    )
    print(
        "Common raw coverage starts:",
        max(table.first_date),
        "ends:",
        min(table.last_date),
    )
    print(
        "Important: market-level research data; exact expiry/margin/executable-chain audit remains incomplete."
    )


if __name__ == "__main__":
    main()
