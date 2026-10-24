"""Preview SHA on a local daily CSV/parquet snapshot; no downloads or trades."""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ath_breakout.research.sha import SHAConfig, smoothed_heikin_ashi


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--preset", choices=["tradingview", "fast"], default="tradingview"
    )
    parser.add_argument("--pre-span", type=int)
    parser.add_argument("--post-span", type=int)
    parser.add_argument("--layout", choices=["overlay", "panels"], default="overlay")
    parser.add_argument("--warmup-bars", type=int, default=50)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/smoothed_heikin_ashi/preview")
    )
    args = parser.parse_args()
    preset = (
        SHAConfig.tradingview_reference()
        if args.preset == "tradingview"
        else SHAConfig()
    )
    config = SHAConfig(
        args.pre_span if args.pre_span is not None else preset.pre_span,
        args.post_span if args.post_span is not None else preset.post_span,
        args.warmup_bars,
    )
    source = args.source.resolve()
    raw = (
        pd.read_parquet(source) if source.suffix == ".parquet" else pd.read_csv(source)
    )
    raw.columns = raw.columns.str.lower()
    if "date" in raw:
        raw = raw.set_index(pd.to_datetime(raw.pop("date")))
    result = smoothed_heikin_ashi(raw, config)
    args.output.mkdir(parents=True, exist_ok=True)
    raw.join(result).to_csv(args.output / "indicator.csv", index_label="date")
    overlay = args.layout == "overlay"
    fig = (
        go.Figure()
        if overlay
        else make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            subplot_titles=(
                "Real OHLC prices",
                "Synthetic SHA values — never execution prices",
            ),
        )
    )
    for row, frame, prefix in [(1, raw, ""), (2, result, "sha_")]:
        trace = go.Candlestick(
            x=frame.index,
            open=frame[prefix + "open"],
            high=frame[prefix + "high"],
            low=frame[prefix + "low"],
            close=frame[prefix + "close"],
            name="Real OHLC" if row == 1 else "SHA",
            increasing_line_color="#9ca3af" if row == 1 else "#00ff00",
            decreasing_line_color="#64748b" if row == 1 else "#ff0000",
            increasing_fillcolor="rgba(156,163,175,0.25)"
            if row == 1
            else "rgba(0,255,0,0.4)",
            decreasing_fillcolor="rgba(100,116,139,0.25)"
            if row == 1
            else "rgba(255,0,0,0.4)",
        )
        if overlay:
            fig.add_trace(trace)
        else:
            fig.add_trace(trace, row=row, col=1)
    fig.update_layout(
        title=f"{source.stem}: EMA({config.pre_span}) → HA → EMA({config.post_span}) | Indicator preview, no backtest",
        template="plotly_dark",
        height=850,
        showlegend=True,
    )
    fig.update_xaxes(rangeslider_visible=False, title_text="Date")
    # Start with one year visible; calculations still use the entire snapshot.
    fig.update_xaxes(range=[raw.index[max(0, len(raw) - 252)], raw.index[-1]])
    fig.update_yaxes(title_text="Source price units")
    fig.write_html(args.output / "preview.html", include_plotlyjs=True)
    manifest = {
        "source": str(source),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "config": vars(config),
        "preset": args.preset,
        "layout": args.layout,
        "rows": len(raw),
        "start": str(raw.index[0]),
        "end": str(raw.index[-1]),
        "ready_rows": int(result.ready.sum()),
        "status": "Indicator only; PyneSys parity unverified; no performance evaluation",
        "input_contract": "Completed daily OHLC; source units and adjustment convention preserved",
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(
        f"Saved indicator.csv, preview.html and manifest.json to {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
