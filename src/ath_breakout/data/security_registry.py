"""Track every security observed in current and past universe snapshots."""

from datetime import date
from pathlib import Path

import pandas as pd

from ath_breakout.data.universe import validate_universe


REGISTRY_COLUMNS = [
    "security_id",
    "ticker",
    "in_current_universe",
    "first_seen_in_universe",
    "last_seen_in_universe",
]


def update_security_registry(
    current_universe: pd.DataFrame,
    registry_file: str | Path,
    today: date | None = None,
) -> pd.DataFrame:
    """Add new securities and retain securities absent from today's universe."""
    validate_universe(current_universe)

    if len(current_universe) == 0:
        raise ValueError("Current universe must contain at least one security")

    current_date = today or date.today()
    registry_path = Path(registry_file)

    if registry_path.exists():
        registry = pd.read_csv(registry_path)
    else:
        registry = pd.DataFrame(columns=REGISTRY_COLUMNS)

    current_ids = set(current_universe["security_id"])

    if len(registry) > 0:
        registry["in_current_universe"] = registry["security_id"].isin(
            current_ids
        )

    for _, security in current_universe.iterrows():
        security_id = security["security_id"]
        existing_security = registry["security_id"] == security_id

        if existing_security.any():
            registry.loc[existing_security, "ticker"] = security["ticker"]
            registry.loc[existing_security, "in_current_universe"] = True
            registry.loc[existing_security, "last_seen_in_universe"] = current_date
        else:
            new_security = pd.DataFrame(
                [
                    {
                        "security_id": security_id,
                        "ticker": security["ticker"],
                        "in_current_universe": True,
                        "first_seen_in_universe": current_date,
                        "last_seen_in_universe": current_date,
                    }
                ]
            )
            registry = pd.concat([registry, new_security], ignore_index=True)

    registry = registry[REGISTRY_COLUMNS]
    registry = registry.sort_values("security_id").reset_index(drop=True)

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = registry_path.with_suffix(".tmp.csv")
    registry.to_csv(temporary_path, index=False)
    temporary_path.replace(registry_path)
    return registry
