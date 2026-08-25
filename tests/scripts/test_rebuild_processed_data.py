import pandas as pd

from ath_breakout.data.storage import load_security_data, save_security_data
from scripts.maintenance import rebuild_processed_data


def test_main_rebuilds_processed_file_from_local_raw_data(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    raw_directory = tmp_path / "raw"
    processed_directory = tmp_path / "processed"
    raw_data = pd.DataFrame(
        {
            "security_id": ["AAPL", "AAPL"],
            "ticker": ["AAPL", "AAPL"],
            "date": pd.to_datetime(["2026-08-20", "2026-08-21"]),
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1_000_000, 1_100_000],
        }
    )
    save_security_data(raw_data, raw_directory / "AAPL.parquet")
    monkeypatch.setattr(
        rebuild_processed_data,
        "RAW_DIRECTORY",
        raw_directory,
    )
    monkeypatch.setattr(
        rebuild_processed_data,
        "PROCESSED_DIRECTORY",
        processed_directory,
    )

    rebuild_processed_data.main()

    result = load_security_data(processed_directory / "AAPL.parquet")
    output = capsys.readouterr().out
    assert "prior_ath" in result.columns
    assert "breakout" in result.columns
    assert "Finished: 1 successful, 0 failed" in output


def test_rebuild_progress_columns_do_not_move(capsys) -> None:
    rebuild_processed_data.print_rebuild_progress(99, 2575, 99, 0)
    rebuild_processed_data.print_rebuild_progress(100, 2575, 100, 0)
    rebuild_processed_data.print_rebuild_progress(1000, 2575, 999, 1)

    lines = capsys.readouterr().out.splitlines()
    separator_positions = [
        [index for index, character in enumerate(line) if character == "|"]
        for line in lines
    ]
    assert separator_positions[0] == separator_positions[1]
    assert separator_positions[1] == separator_positions[2]
