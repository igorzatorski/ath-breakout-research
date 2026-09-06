"""Convert CRSP CIZ observations into strategy-ready market histories."""

from dataclasses import asdict, dataclass

import pandas as pd

from ath_breakout.data.crsp_adjustments import add_crsp_comparable_values
from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.processing import process_market_data


@dataclass(frozen=True)
class CrspProcessingReport:
    """Counts describing rows retained and rejected by the adapter."""

    input_rows: int
    output_rows: int
    missing_key_rows: int
    incomplete_ohlcv_rows: int
    invalid_price_rows: int
    invalid_volume_rows: int
    inconsistent_ohlc_rows: int

    def to_dict(self) -> dict:
        return asdict(self)


def _seed_map(ath_seed: pd.DataFrame | None) -> dict[int, float]:
    if ath_seed is None or len(ath_seed) == 0:
        return {}
    required = {"permno", "prior_comparable_high"}
    missing = sorted(required - set(ath_seed.columns))
    if missing:
        raise ValueError(f"Missing CRSP ATH seed columns: {', '.join(missing)}")
    if ath_seed["permno"].duplicated().any():
        raise ValueError("Duplicate PERMNO values found in CRSP ATH seed")
    valid = ath_seed.dropna(subset=["permno", "prior_comparable_high"])
    if (valid["prior_comparable_high"] <= 0).any():
        raise ValueError("CRSP ATH seed highs must be positive")
    return dict(zip(valid["permno"].astype(int), valid["prior_comparable_high"]))


def prepare_crsp_strategy_data(
    raw_data: pd.DataFrame,
    ath_seed: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, CrspProcessingReport]:
    """Return strategy-ready CRSP rows while preserving CRSP return fields."""
    required = {
        "security_id", "permno", "ticker", "date", "open", "high", "low",
        "close", "volume", "total_return", "ordinary_dividend",
        "nonordinary_dividend", "price_adjustment_factor",
        "share_adjustment_factor", "shares_outstanding", "delisting_flag",
        "source",
    }
    missing = sorted(required - set(raw_data.columns))
    if missing:
        raise ValueError(f"Missing CRSP strategy columns: {', '.join(missing)}")

    data = add_crsp_comparable_values(raw_data)
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["crsp_ticker"] = data["ticker"].astype("string")
    data["ticker"] = data.groupby("security_id")["ticker"].transform(
        lambda values: values.ffill().bfill()
    )
    data["ticker"] = data["ticker"].fillna(data["security_id"].astype(str))

    missing_key = data["security_id"].isna() | data["permno"].isna() | data["date"].isna()
    comparable = [
        "comparable_open", "comparable_high", "comparable_low",
        "comparable_close", "comparable_volume",
    ]
    incomplete = data[comparable].isna().any(axis=1)
    invalid_price = (data[
        ["comparable_open", "comparable_high", "comparable_low", "comparable_close"]
    ] <= 0).any(axis=1)
    invalid_volume = data["comparable_volume"] < 0
    inconsistent_high = data["comparable_high"] < data[
        ["comparable_open", "comparable_low", "comparable_close"]
    ].max(axis=1)
    inconsistent_low = data["comparable_low"] > data[
        ["comparable_open", "comparable_high", "comparable_close"]
    ].min(axis=1)
    inconsistent = inconsistent_high | inconsistent_low
    rejected = missing_key | incomplete | invalid_price | invalid_volume | inconsistent
    usable = data.loc[~rejected].copy()

    usable["open"] = usable["comparable_open"]
    usable["high"] = usable["comparable_high"]
    usable["low"] = usable["comparable_low"]
    usable["close"] = usable["comparable_close"]
    usable["volume"] = usable["comparable_volume"]
    usable["adj_close"] = usable["close"]
    usable["dividends"] = (
        usable["comparable_ordinary_dividend"].fillna(0.0)
        + usable["comparable_nonordinary_dividend"].fillna(0.0)
    )
    usable["stock_splits"] = 0.0
    usable["repaired"] = False
    usable["prices_split_adjusted"] = True

    usable = prepare_ohlcv_data(usable)
    processed = process_market_data(usable)
    seeds = _seed_map(ath_seed)
    if seeds:
        seeded_ath = processed["permno"].map(seeds)
        processed["prior_ath"] = pd.concat(
            [processed["prior_ath"], seeded_ath], axis=1
        ).max(axis=1, skipna=True)
        processed["breakout"] = processed["split_adj_close"] > processed["prior_ath"]

    processed["data_source"] = "CRSP CIZ quarterly"
    report = CrspProcessingReport(
        input_rows=len(data),
        output_rows=len(processed),
        missing_key_rows=int(missing_key.sum()),
        incomplete_ohlcv_rows=int((incomplete & ~missing_key).sum()),
        invalid_price_rows=int((invalid_price & ~missing_key & ~incomplete).sum()),
        invalid_volume_rows=int((invalid_volume & ~missing_key & ~incomplete).sum()),
        inconsistent_ohlc_rows=int((inconsistent & ~missing_key & ~incomplete).sum()),
    )
    return processed, report
