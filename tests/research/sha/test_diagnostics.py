import numpy as np
import pandas as pd
import pytest

from ath_breakout.research.sha.diagnostics import (
    annual_comparison,
    drawdown_episode,
    trade_statistics,
)


def test_drawdown_is_multiple_losses_and_uses_last_peak():
    equity = pd.Series(
        [100.0, 100.0, 95.0, 90.25, 85.7375, 101.0],
        index=pd.date_range("2020-01-01", periods=6),
    )
    result = drawdown_episode(equity)
    assert result["max_drawdown"] == pytest.approx(0.95**3 - 1)
    assert result["peak_date"] == "2020-01-02"
    assert result["trough_date"] == "2020-01-05"
    assert result["recovery_date"] == "2020-01-06"


def test_trade_means_win_condition_and_profit_factor_exclude_open():
    metrics = pd.DataFrame(
        [dict(pre_span=10, post_span=10), dict(pre_span=1, post_span=1)]
    )
    trades = pd.DataFrame(
        dict(
            pre_span=[10] * 4,
            post_span=[10] * 4,
            status=["closed", "closed", "closed", "open"],
            net_return=[0.1, -0.05, 0, 100],
            holding_sessions=[2, 4, 6, 100],
            holding_calendar_days=[2, 6, 8, 150],
            initial_outlay=[100, 200, 300, 1],
            value=[110, 190, 300, 101],
        )
    )
    result = trade_statistics(metrics, trades)
    assert result.loc[0, "mean_holding_sessions"] == 4
    assert result.loc[0, "mean_trade_return"] == pytest.approx(0.05 / 3)
    assert result.loc[0, "profit_factor_dollars"] == 1
    assert result.loc[0, "zero_return_trades"] == 1
    assert result.loc[0, "maximum_losing_streak"] == 1
    assert result.loc[1, "maximum_losing_streak"] == 0
    assert np.isnan(result.loc[1, "mean_holding_sessions"])


def test_annual_returns_compound_instead_of_sum():
    equity = pd.Series([100, 110, 121], index=pd.date_range("2020-01-01", periods=3))
    result = annual_comparison(equity, equity)
    assert result.loc[2020, "strategy"] == pytest.approx(0.21)
    assert result.loc[2020, "excess_return"] == 0
