import pandas as pd

from ath_breakout.data.adapters.csv import load_ohlcv_csv


def test_loads_and_sorts_multiple_securities() -> None:
    data = load_ohlcv_csv("tests/fixtures/multi_security_ohlcv.csv")

    assert isinstance(data, pd.DataFrame)
    assert data["security_id"].tolist() == ["AAPL", "AAPL", "MSFT", "MSFT"]
    assert data["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-02",
        "2024-01-03",
        "2024-01-02",
        "2024-01-03",
    ]
    assert data.index.tolist() == [0, 1, 2, 3]
