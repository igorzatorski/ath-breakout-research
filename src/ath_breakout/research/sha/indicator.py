"""EMA -> Heikin Ashi -> EMA; not a verified PyneSys replica."""

from dataclasses import dataclass
from numbers import Integral

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SHAConfig:
    """Lengths count observed bars, not calendar days or holding periods."""

    pre_span: int = 5
    post_span: int = 3
    warmup_bars: int = 50

    @classmethod
    def tradingview_reference(cls):
        """EMA lengths from PyneSys script; numerical chart parity unverified."""
        return cls(pre_span=10, post_span=10)

    def __post_init__(self):
        for name in ("pre_span", "post_span", "warmup_bars"):
            value = getattr(self, name)
            minimum = 0 if name == "warmup_bars" else 1
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise ValueError(f"{name} must be an integer")
            if value < minimum:
                raise ValueError(f"{name} must be >= {minimum}")


def smoothed_heikin_ashi(
    ohlc: pd.DataFrame, config: SHAConfig | None = None
) -> pd.DataFrame:
    """Return synthetic OHLC, direction (-1/0/+1), readiness and nullable signal.

    Input: one instrument, lowercase OHLC, unique increasing DatetimeIndex.
    Missing/nonfinite/nonpositive prices and invalid OHLC ranges are rejected.
    No bars are resampled or filled. Caller supplies completed daily bars and
    consistent adjustment conventions. EMA uses adjust=False, seeded at the
    first observation. Initial HA open is (smoothed open + close) / 2.
    Equal final open/close is neutral. The first warmup_bars outputs remain
    visible but signal is missing. Direction is descriptive, not a fill price
    or trading instruction. Input is never mutated.
    """
    config = config or SHAConfig()
    columns = ["open", "high", "low", "close"]
    if not isinstance(ohlc.index, pd.DatetimeIndex):
        raise ValueError("DatetimeIndex required")
    if ohlc.empty or ohlc.index.hasnans:
        raise ValueError("Nonempty input with valid timestamps required")
    if not ohlc.index.is_unique or not ohlc.index.is_monotonic_increasing:
        raise ValueError("Timestamps must be unique and increasing")
    if not ohlc.columns.is_unique or not set(columns).issubset(ohlc.columns):
        raise ValueError("Unique lowercase open/high/low/close columns required")
    prices = ohlc[columns].astype(float)
    if not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any():
        raise ValueError("Finite positive OHLC prices required")
    if (prices.high < prices.max(axis=1)).any() or (
        prices.low > prices.min(axis=1)
    ).any():
        raise ValueError("Invalid OHLC range")

    smooth = prices.ewm(span=config.pre_span, adjust=False).mean()
    ha_close = smooth.mean(axis=1).to_numpy()
    ha_open = np.empty(len(prices))
    ha_open[0] = (smooth.open.iloc[0] + smooth.close.iloc[0]) / 2
    for i in range(1, len(prices)):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2
    ha = (
        pd.DataFrame(
            {
                "open": ha_open,
                "high": np.maximum.reduce([smooth.high.to_numpy(), ha_open, ha_close]),
                "low": np.minimum.reduce([smooth.low.to_numpy(), ha_open, ha_close]),
                "close": ha_close,
            },
            index=prices.index,
        )
        .ewm(span=config.post_span, adjust=False)
        .mean()
    )
    result = ha.add_prefix("sha_")
    result["direction"] = np.sign(ha.close - ha.open).astype("int8")
    # PyneSys plotting rule: red only when open > close; ties are green.
    # Keep research direction neutral on ties, independently of display color.
    result["display_color"] = np.where(ha.open > ha.close, "red", "lime")
    result["ready"] = np.arange(len(result)) >= config.warmup_bars
    result["signal"] = result.direction.astype("Int8").where(result.ready)
    return result
