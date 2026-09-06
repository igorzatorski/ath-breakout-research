"""Convert CRSP CIZ observations into strategy-ready market histories."""

from dataclasses import asdict, dataclass
from dataclasses import field

import pandas as pd

from ath_breakout.data.crsp_adjustments import add_crsp_comparable_values
from ath_breakout.data.preparation import prepare_ohlcv_data
from ath_breakout.data.processing import process_market_data


@dataclass(frozen=True)
class CrspProcessingReport:
    """Counts describing rows retained and rejected by the adapter."""

    input_rows: int
    output_rows: int
    invalid_price_factor_rows: int
    invalid_share_factor_rows: int
    missing_key_rows: int
    incomplete_ohlcv_rows: int
    invalid_price_rows: int
    invalid_volume_rows: int
    inconsistent_ohlc_rows: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CrspFeatureState:
    """Minimal cross-partition state needed by rolling strategy features."""

    close_tails: dict[int, list[float]] = field(default_factory=dict)
    prior_highs: dict[int, float] = field(default_factory=dict)


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


def normalize_crsp_strategy_rows(
    raw_data: pd.DataFrame,
) -> tuple[pd.DataFrame, CrspProcessingReport]:
    """Return comparable, tradable CRSP rows before rolling features."""
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

    price_factor = pd.to_numeric(
        raw_data["price_adjustment_factor"], errors="coerce"
    )
    share_factor = pd.to_numeric(
        raw_data["share_adjustment_factor"], errors="coerce"
    )
    price_rows = raw_data[["open", "high", "low", "close"]].notna().any(axis=1)
    share_rows = raw_data[["volume", "shares_outstanding"]].notna().any(axis=1)
    invalid_price_factor = price_rows & (price_factor.isna() | price_factor.le(0))
    invalid_share_factor = share_rows & (share_factor.isna() | share_factor.le(0))
    invalid_factor = invalid_price_factor | invalid_share_factor
    data = add_crsp_comparable_values(raw_data.loc[~invalid_factor].copy())
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

    usable["nominal_close"] = usable["close"]
    usable["nominal_volume"] = usable["volume"]

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
    report = CrspProcessingReport(
        input_rows=len(raw_data),
        output_rows=len(usable),
        invalid_price_factor_rows=int(invalid_price_factor.sum()),
        invalid_share_factor_rows=int(invalid_share_factor.sum()),
        missing_key_rows=int(missing_key.sum()),
        incomplete_ohlcv_rows=int((incomplete & ~missing_key).sum()),
        invalid_price_rows=int((invalid_price & ~missing_key & ~incomplete).sum()),
        invalid_volume_rows=int((invalid_volume & ~missing_key & ~incomplete).sum()),
        inconsistent_ohlc_rows=int((inconsistent & ~missing_key & ~incomplete).sum()),
    )
    return usable, report


def prepare_crsp_strategy_data(
    raw_data: pd.DataFrame,
    ath_seed: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, CrspProcessingReport]:
    """Return strategy-ready CRSP rows while preserving CRSP return fields."""
    usable, report = normalize_crsp_strategy_rows(raw_data)
    processed = process_market_data(usable)
    seeds = _seed_map(ath_seed)
    if seeds:
        seeded_ath = processed["permno"].map(seeds)
        processed["prior_ath"] = pd.concat(
            [processed["prior_ath"], seeded_ath], axis=1
        ).max(axis=1, skipna=True)
        processed["breakout"] = processed["split_adj_close"] > processed["prior_ath"]

    processed["data_source"] = "CRSP CIZ quarterly"
    return processed, report


def initialize_crsp_feature_state(
    ath_seed: pd.DataFrame | None = None,
) -> CrspFeatureState:
    """Create feature state initialized with highs before the requested period."""
    return CrspFeatureState(prior_highs=_seed_map(ath_seed))


def add_stateful_crsp_features(
    canonical_data: pd.DataFrame,
    state: CrspFeatureState,
) -> pd.DataFrame:
    """Add exact rolling features and update state for the next partition."""
    feature_tables = []
    for permno, security in canonical_data.groupby("permno", sort=False):
        permno = int(permno)
        security = security.sort_values("date").copy()
        closes = pd.Series(
            state.close_tails.get(permno, []) + security["close"].tolist(),
            dtype=float,
        )
        offset = len(closes) - len(security)
        for window in (50, 100, 150, 200):
            security[f"sma_{window}"] = (
                closes.rolling(window=window, min_periods=window)
                .mean()
                .iloc[offset:]
                .to_numpy()
            )
        for source, target in zip(
            ("open", "high", "low", "close"),
            ("split_adj_open", "split_adj_high", "split_adj_low", "split_adj_close"),
        ):
            security[target] = security[source]

        previous_partition_high = state.prior_highs.get(permno)
        within_partition = security["high"].shift(1).cummax()
        if previous_partition_high is not None:
            within_partition = pd.concat(
                [within_partition, pd.Series(previous_partition_high, index=security.index)],
                axis=1,
            ).max(axis=1, skipna=True)
        security["prior_ath"] = within_partition
        security["breakout"] = security["close"] > security["prior_ath"]
        security["data_source"] = "CRSP CIZ quarterly"

        state.close_tails[permno] = closes.iloc[-199:].tolist()
        current_high = float(security["high"].max())
        state.prior_highs[permno] = max(
            current_high,
            previous_partition_high
            if previous_partition_high is not None
            else current_high,
        )
        feature_tables.append(security)
    if not feature_tables:
        return canonical_data.copy()
    return pd.concat(feature_tables, ignore_index=True).sort_values(
        ["permno", "date"]
    ).reset_index(drop=True)


def restore_crsp_feature_state(
    processed_data: pd.DataFrame,
    state: CrspFeatureState,
) -> None:
    """Advance state from an already-built partition during a resumed run."""
    for permno, security in processed_data.groupby("permno", sort=False):
        permno = int(permno)
        security = security.sort_values("date")
        accumulated_closes = (
            state.close_tails.get(permno, [])
            + security["close"].astype(float).tolist()
        )
        state.close_tails[permno] = accumulated_closes[-199:]
        high = float(security["high"].max())
        prior = state.prior_highs.get(permno)
        state.prior_highs[permno] = max(high, prior if prior is not None else high)
