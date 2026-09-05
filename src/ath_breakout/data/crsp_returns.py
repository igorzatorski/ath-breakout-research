"""Validate CRSP daily return and distribution components."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CrspReturnValidation:
    no_distribution_rows: int
    ordinary_distribution_rows: int
    nonordinary_distribution_rows: int
    return_identity_rows: int


def validate_crsp_return_components(data: pd.DataFrame) -> CrspReturnValidation:
    """Validate documented relationships without reconstructing CRSP returns."""
    required = {
        "total_return",
        "return_ex_distributions",
        "income_return",
        "ordinary_dividend",
        "nonordinary_dividend",
        "period_price_factor",
        "distribution_return_flag",
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing CRSP return columns: {', '.join(missing)}")

    ordinary = pd.to_numeric(data["ordinary_dividend"], errors="coerce").fillna(0.0)
    nonordinary = pd.to_numeric(
        data["nonordinary_dividend"], errors="coerce"
    ).fillna(0.0)
    period_factor = pd.to_numeric(
        data["period_price_factor"], errors="coerce"
    ).fillna(0.0)
    total_return = pd.to_numeric(data["total_return"], errors="coerce")
    price_return = pd.to_numeric(
        data["return_ex_distributions"], errors="coerce"
    )
    income_return = pd.to_numeric(data["income_return"], errors="coerce")

    no_distribution = (
        ordinary.eq(0.0) & nonordinary.eq(0.0) & period_factor.eq(0.0)
    )
    comparable_returns = no_distribution & total_return.notna() & price_return.notna()
    if not np.allclose(
        total_return[comparable_returns],
        price_return[comparable_returns],
        rtol=0.0,
        atol=1e-10,
    ):
        raise ValueError("CRSP total and price returns differ without a distribution")

    ordinary_event = ordinary.gt(0.0)
    ordinary_with_returns = ordinary_event & total_return.notna() & price_return.notna()
    if ordinary_with_returns.any() and np.isclose(
        total_return[ordinary_with_returns],
        price_return[ordinary_with_returns],
        rtol=0.0,
        atol=1e-10,
    ).any():
        raise ValueError("Ordinary dividend did not affect CRSP total return")

    identity_rows = (
        total_return.notna() & price_return.notna() & income_return.notna()
    )
    reconstructed = price_return[identity_rows] + income_return[identity_rows]
    if not np.allclose(
        total_return[identity_rows], reconstructed, rtol=0.0, atol=1e-9
    ):
        raise ValueError("CRSP return component identity does not hold")

    distribution_event = ordinary_event | nonordinary.gt(0.0) | period_factor.ne(0.0)
    if data.loc[distribution_event, "distribution_return_flag"].isna().any():
        raise ValueError("CRSP distribution event is missing its impact flag")

    return CrspReturnValidation(
        no_distribution_rows=int(no_distribution.sum()),
        ordinary_distribution_rows=int(ordinary_event.sum()),
        nonordinary_distribution_rows=int(nonordinary.gt(0.0).sum()),
        return_identity_rows=int(identity_rows.sum()),
    )
