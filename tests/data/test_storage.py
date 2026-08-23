import pandas as pd

from ath_breakout.data.storage import load_security_data, save_security_data


def test_saves_and_loads_security_parquet(tmp_path) -> None:
    file_path = tmp_path / "AAPL.parquet"
    data = pd.DataFrame(
        {
            "security_id": ["AAPL"],
            "ticker": ["AAPL"],
            "date": pd.to_datetime(["2024-01-02"]),
            "close": [102.0],
        }
    )

    save_security_data(data, file_path)
    result = load_security_data(file_path)

    pd.testing.assert_frame_equal(result, data)
    assert not (tmp_path / "AAPL.tmp.parquet").exists()
