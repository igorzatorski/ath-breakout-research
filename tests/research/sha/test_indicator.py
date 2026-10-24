import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.sha import SHAConfig, smoothed_heikin_ashi


def sample():
    return pd.DataFrame(
        [[10, 14, 8, 12], [12, 16, 10, 14], [14, 18, 12, 16]],
        columns=["open", "high", "low", "close"],
        index=pd.date_range("2024-01-01", periods=3),
    )


def test_manual_two_stage_calculation():
    # span=3 means alpha=1/2 at both smoothing stages.
    result = smoothed_heikin_ashi(sample(), SHAConfig(3, 3, 1))
    np.testing.assert_allclose(result.sha_open, [11, 11, 11.25])
    np.testing.assert_allclose(result.sha_close, [11, 11.5, 12.5])
    np.testing.assert_allclose(result.sha_high, [14, 14.5, 15.5])
    np.testing.assert_allclose(result.sha_low, [8, 8.5, 9.5])
    assert result.direction.tolist() == [0, 1, 1]
    assert pd.isna(result.signal.iloc[0])
    assert result.signal.iloc[1:].tolist() == [1, 1]


def test_no_smoothing_reduces_to_standard_ha():
    result = smoothed_heikin_ashi(sample(), SHAConfig(1, 1, 0))
    np.testing.assert_allclose(result.sha_open, [11, 11, 12])
    np.testing.assert_allclose(result.sha_close, [11, 13, 15])


def test_future_append_and_mutation_do_not_change_past():
    prices = pd.concat(
        [
            sample()
            .add(i)
            .set_axis(pd.date_range("2024-01-01", periods=120)[i * 3 : i * 3 + 3])
            for i in range(40)
        ]
    )
    original = prices.copy(deep=True)
    full = smoothed_heikin_ashi(prices)
    pd.testing.assert_frame_equal(
        smoothed_heikin_ashi(prices.iloc[:70]), full.iloc[:70]
    )
    prices.iloc[70:] *= 10
    pd.testing.assert_frame_equal(
        smoothed_heikin_ashi(prices).iloc[:70], full.iloc[:70]
    )
    pd.testing.assert_frame_equal(original.iloc[:70], prices.iloc[:70])


def test_constant_prices_neutral_and_input_unchanged():
    prices = sample() * 0 + 10
    original = prices.copy(deep=True)
    result = smoothed_heikin_ashi(prices, SHAConfig(warmup_bars=0))
    assert result.signal.eq(0).all()
    assert result.display_color.eq("lime").all()
    pd.testing.assert_frame_equal(prices, original)


def test_reference_preset_and_red_display_rule():
    config = SHAConfig.tradingview_reference()
    assert (config.pre_span, config.post_span) == (10, 10)
    falling = sample().iloc[::-1].set_axis(sample().index)
    result = smoothed_heikin_ashi(falling, SHAConfig(1, 1, 0))
    assert result.display_color.tolist() == ["lime", "red", "red"]


@pytest.mark.parametrize(
    "kind", ["missing", "infinite", "range", "zero", "duplicate", "reverse"]
)
def test_invalid_input_rejected(kind):
    prices = sample().astype(float)
    if kind == "missing":
        prices.iloc[0, 0] = np.nan
    elif kind == "infinite":
        prices.iloc[0, 0] = np.inf
    elif kind == "range":
        prices.iloc[0, 1] = 1
    elif kind == "zero":
        prices.iloc[0, 2] = 0
    elif kind == "duplicate":
        prices.index = [prices.index[0]] * 3
    else:
        prices = prices.iloc[::-1]
    with pytest.raises(ValueError):
        smoothed_heikin_ashi(prices)


@pytest.mark.parametrize(
    "kwargs",
    [{"pre_span": 0}, {"post_span": 1.5}, {"pre_span": True}, {"warmup_bars": -1}],
)
def test_invalid_settings_rejected(kwargs):
    with pytest.raises(ValueError):
        SHAConfig(**kwargs)
