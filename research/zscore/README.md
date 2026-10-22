# Index mean-reversion research

Exploratory SPY / QQQ research, separate from the ATH strategy. These historical
results are not independent out-of-sample validation or a live trading system.

## Start here

- [Initial methodology](PLAN.md) and [SPY results](RESULTS.md)
- [Threshold -2 results](RESULTS_MINUS2.md)
- [Nasdaq comparison](NASDAQ_COMPARISON.md)
- [Extended signal study](EXTENDED_READOUT.md), [plan](EXTENDED_PLAN.md),
  [full results](EXTENDED_RESULTS.md)
- [Exit and sizing study](EXITS_READOUT.md), [plan](EXITS_PLAN.md),
  [full results](EXITS_RESULTS.md)

## Reproduce

Run from the repository root with the project's Python environment:

```powershell
.venv/Scripts/python.exe scripts/research/study_zscore.py --threshold -1
.venv/Scripts/python.exe scripts/research/study_zscore.py --threshold -2
.venv/Scripts/python.exe scripts/research/study_zscore.py --ticker QQQ --threshold -1
.venv/Scripts/python.exe scripts/research/study_zscore.py --ticker QQQ --threshold -2
.venv/Scripts/python.exe scripts/research/study_zscore.py --start 1999-06-03 --threshold -1
.venv/Scripts/python.exe scripts/research/study_zscore.py --start 1999-06-03 --threshold -2
.venv/Scripts/python.exe -m scripts.research.study_mean_reversion
.venv/Scripts/python.exe -m scripts.research.study_exits
.venv/Scripts/python.exe -m pytest tests/test_zscore_study.py tests/test_mean_reversion_study.py tests/test_exit_study.py -q -p no:cacheprovider --basetemp=outputs/zscore/pytest_tmp
```

Required local source snapshots are `data/raw/yfinance/SPY.parquet` and
`data/raw/yfinance/QQQ_zscore.parquet`, with daily `date`, `open`, `high`, `low`,
`close`, and `adj_close` columns. Both end on 2026-10-05. They are excluded
from Git, as are generated event ledgers and equity curves under `outputs/`.
The committed reports preserve results; rerunning requires these local data
snapshots. Refetched vendor history can differ due to revisions.

Snapshot SHA256:

- SPY: `d53d88560bb710b5a27dc0052a401166132682148ee78550ec3262018fb5872f`
- QQQ: `e26a87ef2c83022653893fe297a46b6f6a91c9f2a19bf4f50bc5ce470f5a8e66`

QQQ source: public Yahoo Finance daily history fetched 2026-10-22, beginning
1999-03-10. SPY uses the existing local Yahoo snapshot beginning 1993-01-29.
Each study writes source fingerprints and settings into its output manifest.
The exit/sizing study uses the extended study's manifest to fix signal dates,
so run the extended study first.
