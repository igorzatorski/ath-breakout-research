# Smoothed Heikin Ashi research

Independent Python research track within the ATH research repository.
Status: causal EMA-based indicator, local preview command and unit tests implemented.
Single SPY EMA(10,10) baseline implemented and executed; PyneSys parity unverified.
See [frozen methodology](BASELINE_10_10_PLAN.md) and [baseline results](BASELINE_10_10_RESULTS.md).
The 400-pair EMA grid is also available: [grid methodology](GRID_20_20_PLAN.md)
and [all-results readout](GRID_20_20_RESULTS.md). This is full-history exploration,
not independent validation or an adopted parameter choice.
Cross-market grids, full trade statistics and drawdown diagnostics are available:
[methodology](CROSS_MARKET_PLAN.md) and [results](CROSS_MARKET_RESULTS.md).
QQQ represents Nasdaq-100, not Nasdaq Composite; BTC uses UTC daily observations.

## Research question

Can a strategy driven by Smoothed Heikin Ashi candle direction capture trends
well enough to compensate for delayed signals, whipsaws and trading costs?

## Start here

Read [PLAN.md](PLAN.md) for the staged workflow and unresolved inputs.
The first implementation milestone is a causal indicator in Python, checked
against the intended TradingView indicator on identical input data.

## Boundaries and file ownership

- `research/smoothed_heikin_ashi/`: methodology, specifications and reports.
- Future Python research modules: `src/ath_breakout/research/sha/`.
- Future command entry points: `scripts/research/sha/`.
- Future tests: `tests/research/sha/`.
- Future generated artifacts: `outputs/smoothed_heikin_ashi/` (Git ignored).

The indicator and tests use the paths above; the preview entry point is
`run/sha_preview.py`. The existing Python environment is reused.
Do not inherit ATH entry rules, equity-universe assumptions or portfolio defaults.
Changes to this track must not change existing ATH or Z-score research behavior.

The implementation and simulation will run in Python. Pine Script is a reference
specification for indicator parity, not the execution environment.

## First working configuration

Daily input, EMA(5) on each real OHLC series, standard HA transformation,
then EMA(3) on each HA OHLC series. This is an engineering starting point,
not a validated optimal setting. The intended holding horizon is roughly
one week to several months; smoothing lengths do not fix holding duration.
Lengths count observed bars (five equity sessions differ from five crypto days).

EMA uses `adjust=False`, seeded at the first observation. Initial HA open
is the mean of first smoothed open and close; HA close is smoothed OHLC mean.
Subsequent HA open averages the previous HA open and close. HA high/low
include the smoothed high/low and current HA open/close.
Direction is the sign of final close minus open; equality is neutral.
The first 50 bars are excluded from the nullable signal, while calculated
values remain visible. Warm-up mitigates initialization effects but is not
a formal parity guarantee. The caller supplies completed daily bars.

Input requires increasing unique dates and complete, finite, positive,
internally consistent OHLC. Missing bars are not invented or filled.
Input adjustments are preserved; source choice remains part of future research.

## Run locally

```powershell
.venv/Scripts/python.exe run/sha_preview.py data/raw/yfinance/SPY.parquet
.venv/Scripts/python.exe run/sha_backtest.py
.venv/Scripts/python.exe run/sha_grid.py
.venv/Scripts/python.exe run/sha_fetch_cross_market.py
.venv/Scripts/python.exe run/sha_cross_market.py
.venv/Scripts/python.exe -m pytest tests/research/sha -q -p no:cacheprovider --basetemp=outputs/smoothed_heikin_ashi/pytest_tmp
```

The preview accepts local CSV or parquet with lowercase/case-insensitive OHLC
and a `date` column or DatetimeIndex. It writes a self-contained interactive
`preview.html`, `indicator.csv`, and source-fingerprinted `manifest.json`.
Default output is `outputs/smoothed_heikin_ashi/preview/`; reruns replace those
generated files. Use `--output` to keep separate previews and `--pre-span`,
`--post-span`, `--warmup-bars` to explicitly change settings.

The preview itself is an indicator smoke test, not a performance evaluation.
The separate baseline runner evaluates SPY with the frozen execution rules.
No source download or parameter search occurs.
The chart includes warm-up candles; use the CSV `ready` column for eligibility.

Formula reference: [TradingView HA construction](https://www.tradingview.com/support/solutions/43000619436-understanding-heikin-ashi-charts/).

## PyneSys reference preset and overlay

The [requested script](https://www.tradingview.com/script/pjl3mIvc-Smoothed-Heiken-Ashi/)
was inspected through its public Source code tab on 2026-10-24. Its input defaults
are EMA(10) before HA and EMA(10) after HA. It imports `wallneradam/TAExt/8`.
The published chart example shows a different post-smoothing selection; chart
legend settings should not be confused with source input defaults.

The current public [TAExt source](https://www.tradingview.com/script/3i8MeCJw-TAExt/)
exposes version 10, whose HA recurrence matches our EMA -> HA -> EMA structure.
The imported version 8 has not been independently retrieved or compared, and
matching-data numerical parity against TradingView remains unverified.
Only EMA is implemented here; the source's other MA types and multi-timeframe
behavior are not implemented. Daily input is retained for this project.

`SHAConfig.tradingview_reference()` provides lengths 10/10. The preview command
now defaults to that preset and overlays translucent green/red SHA candles on
gray real candles in a dark chart. Initial viewport is the last 252 observed
bars; calculation still uses full input history. Plotly rendering approximates
the reference's body/wick/border styling rather than reproducing its renderer.
`display_color` follows the source's red-if-open>close rule, including green
ties. Research `direction` and `signal` remain neutral on ties; a later strategy
must explicitly decide how to treat them.

```powershell
.venv/Scripts/python.exe run/sha_preview.py data/raw/yfinance/SPY.parquet --output outputs/smoothed_heikin_ashi/tradingview_reference
.venv/Scripts/python.exe run/sha_preview.py data/raw/yfinance/SPY.parquet --preset fast --layout panels --output outputs/smoothed_heikin_ashi/fast_preview
```

The library default `SHAConfig()` remains 5/3 for compatibility with the first
prototype; the preview explicitly selects 10/10 unless `--preset fast` is used.
Neither preset was chosen by performance optimization.
