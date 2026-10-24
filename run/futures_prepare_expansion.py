"""Prepare a pre-performance 50-market registry and honest source readiness table."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from run.futures_fetch import COMMIT, MAPPING, OUT as RAW

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/trend_following_futures/expansion_preparation"
RESEARCH = ROOT / "research/trend_following_futures"

# Selected for economic breadth and source feasibility, without reading their returns.
CANDIDATES = {
    "equity_indices": [
        ("SP500", "S&P 500", "US"),
        ("NASDAQ", "Nasdaq-100", "US"),
        ("RUSSELL_mini", "Russell 2000", "US"),
        ("DAX", "DAX", "Germany"),
        ("EUROSTX", "Euro Stoxx 50", "Euro area"),
        ("FTSE100", "FTSE 100", "UK"),
        ("NIKKEI", "Nikkei 225", "Japan"),
        ("SPI200", "ASX SPI 200", "Australia"),
        ("CAC", "CAC 40", "France"),
        ("SMI", "Swiss Market Index", "Switzerland"),
    ],
    "government_bonds": [
        ("US2", "US 2-year Treasury note", "US"),
        ("US10", "US 10-year Treasury note", "US"),
        ("US20", "US Treasury bond", "US"),
        ("US5", "US 5-year Treasury note", "US"),
        ("US30", "US Ultra Treasury bond", "US"),
        ("BUND", "German Bund", "Germany"),
        ("BOBL", "German Bobl", "Germany"),
        ("SHATZ", "German Schatz", "Germany"),
        ("GILT", "UK Long Gilt", "UK"),
        ("JGB", "Japanese government bond", "Japan"),
    ],
    "currencies": [
        ("EUR", "Euro vs USD", "G10 FX"),
        ("JPY", "Yen vs USD", "G10 FX"),
        ("GBP", "Pound vs USD", "G10 FX"),
        ("AUD", "Australian dollar vs USD", "G10 FX"),
        ("CAD", "Canadian dollar vs USD", "G10 FX"),
        ("CHF", "Swiss franc vs USD", "G10 FX"),
        ("NZD", "New Zealand dollar vs USD", "G10 FX"),
        ("MXP", "Mexican peso vs USD", "EM FX"),
        ("NOK", "Norwegian krone vs USD", "G10 FX"),
        ("SEK", "Swedish krona vs USD", "G10 FX"),
    ],
    "commodities": [
        ("CRUDE_W", "WTI crude oil", "Energy"),
        ("GAS_US", "Henry Hub natural gas", "Energy"),
        ("GOLD", "Gold", "Precious metals"),
        ("SILVER", "Silver", "Precious metals"),
        ("COPPER", "Copper", "Industrial metals"),
        ("CORN", "Corn", "Grains"),
        ("WHEAT", "Chicago wheat", "Grains"),
        ("SOYBEAN", "Soybeans", "Oilseeds"),
        ("LIVECOW", "Live cattle", "Livestock"),
        ("BRENT_W", "Brent crude oil", "Energy"),
        ("HEATOIL", "Heating oil", "Energy"),
        ("GASOILINE", "RBOB gasoline", "Energy"),
        ("GASOIL", "Low sulphur gasoil", "Energy"),
        ("ALUMINIUM_LME", "LME aluminium", "Industrial metals"),
        ("NICKEL_LME", "LME nickel", "Industrial metals"),
        ("PLAT", "Platinum", "Precious metals"),
        ("PALLAD", "Palladium", "Precious metals"),
        ("COFFEE", "Coffee", "Soft commodities"),
        ("SUGAR11", "Sugar No. 11", "Soft commodities"),
        ("COTTON2", "Cotton No. 2", "Soft commodities"),
    ],
}


def main():
    inventory_path = OUT / "source_file_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    if inventory["commit"] != COMMIT:
        raise ValueError("Source inventory version mismatch")
    meta_path = RAW / "data/futures/csvconfig/instrumentconfig.csv"
    meta = pd.read_csv(meta_path).set_index("Instrument")
    spread = pd.read_csv(RAW / "data/futures/csvconfig/spreadcosts.csv").set_index(
        "Instrument"
    )
    known = {
        folder: {entry["name"]: entry for entry in entries}
        for folder, entries in inventory["folders"].items()
    }
    prior = pd.read_csv(
        ROOT / "outputs/trend_following_futures/baseline_v001/staleness.csv"
    ).set_index("root")
    reverse = {v: k for k, v in MAPPING.items()}
    rows = []
    for asset_class, items in CANDIDATES.items():
        for code, name, region in items:
            if code not in meta.index:
                raise ValueError(f"No source metadata for {code}")
            m = meta.loc[code]
            original_root = reverse.get(code, "")
            prior_status = (
                (
                    "v001_prototype_eligible"
                    if prior.loc[original_root, "eligible"]
                    else "v001_gap_repair_required"
                )
                if original_root
                else "not_audited"
            )
            adjusted = code + ".csv" in known["adjusted_prices_csv"]
            multiple = code + ".csv" in known["multiple_prices_csv"]
            calendar = code + ".csv" in known["roll_calendars_csv"]
            flags = []
            if m.Currency != "USD":
                flags.append("USD conversion of P&L, notional and fees required")
            if float(m.PerBlock) <= 0:
                flags.append("commission estimate missing or zero; verify")
            if code not in spread.index or float(spread.loc[code, "SpreadCost"]) <= 0:
                flags.append("spread estimate missing or zero; verify")
            if not calendar:
                flags.append("published roll calendar missing")
            if prior_status == "v001_gap_repair_required":
                flags.append("priced-series gaps unresolved")
            if code == "DAX":
                flags.append(
                    "provider point value is micro-sized; historical unit mapping required"
                )
            if code == "SILVER":
                flags.append("source 1000 oz unit differs from standard SI 5000 oz")
            if code == "NICKEL_LME":
                flags.append(
                    "exchange suspensions/cancelled trades and venue history require audit"
                )
            rows.append(
                dict(
                    market_id=code,
                    market=name,
                    asset_class=asset_class,
                    region_or_subgroup=region,
                    pnl_currency=str(m.Currency),
                    original_v001_root=original_root,
                    source_metadata_present=True,
                    adjusted_file_listed=adjusted,
                    multiple_file_listed=multiple,
                    roll_calendar_listed=calendar,
                    source_point_value=float(m.Pointsize),
                    source_commission=float(m.PerBlock),
                    prior_audit_status=prior_status,
                    eligible_for_v002_backtest=False,
                    historical_coverage_verified=False,
                    preparation_flags="; ".join(flags),
                    source_commit=COMMIT,
                )
            )
    table = pd.DataFrame(rows)
    if len(table) != 50 or table.market_id.nunique() != 50:
        raise ValueError("Exactly 50 distinct candidates required")
    if set(MAPPING.values()) - set(table.market_id):
        raise ValueError("Original 20 candidates must be retained in the audit list")
    assert Counter(table.asset_class) == dict(
        equity_indices=10, government_bonds=10, currencies=10, commodities=20
    )
    payload = dict(
        name="Futures trend following: 50-market candidate universe",
        status="prepared_not_backtested",
        source_commit=COMMIT,
        selection_basis="economic breadth and source feasibility, before v002 performance",
        global_pit_universe=False,
        all_market_eligibility_pending=True,
        markets=rows,
    )
    (RESEARCH / "UNIVERSE_50.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    table.to_csv(OUT / "candidate_readiness.csv", index=False)
    by_class = table.groupby("asset_class").agg(
        candidates=("market_id", "size"),
        adjusted_listed=("adjusted_file_listed", "sum"),
        multiple_listed=("multiple_file_listed", "sum"),
        calendar_listed=("roll_calendar_listed", "sum"),
    )
    manifest = dict(
        source_commit=COMMIT,
        configuration_count=50,
        performance_runs=0,
        source_inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        metadata_sha256=hashlib.sha256(meta_path.read_bytes()).hexdigest(),
        builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        universe_sha256=hashlib.sha256(
            (RESEARCH / "UNIVERSE_50.json").read_bytes()
        ).hexdigest(),
        warning="File listing confirms availability only; no coverage/roll/calendar/FX readiness claim",
    )
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    report = [
        "# Fifty-market candidate universe: preparation",
        "",
        "Status: prepared, not backtested. The candidate list preserves all original 20 and adds 30 markets.",
        "Selection uses economic breadth and source metadata/file availability; no v002 returns were inspected.",
        "",
        "## Candidate markets",
        "",
        table[
            [
                "market_id",
                "market",
                "asset_class",
                "pnl_currency",
                "prior_audit_status",
                "preparation_flags",
            ]
        ].to_markdown(index=False),
        "",
        "## Verified preparation",
        "",
        by_class.to_markdown(),
        "",
        f"Foreign-currency P&L markets: {int(table.pnl_currency.ne('USD').sum())}. Required non-USD currencies: {', '.join(sorted(set(table.pnl_currency) - {'USD'}))}.",
        "A listed CSV does not establish complete usable history, venue/session calendars, liquidity or correct historical contract units.",
        "Historical source descriptions and units are preserved as provider metadata, not represented as current exchange specifications.",
        "",
        "## Readiness gates",
        "",
        "Resolve original EUR/JPY/CORN priced-series gaps using actual same-maturity data or a newly audited roll chain.",
        "Add and test timestamp-aligned FX conversion for foreign contract P&L, fees, collateral and notional limits.",
        "Audit per-market sessions, raw multiple-price continuity, source roll IDs, current/historical units, and missing or zero cost estimates.",
        "Use the declared eligibility rules for the primary comparison window; exclude/investigate failures without choosing by profitability.",
        "Keep v001 artifacts unchanged. No 50-market portfolio has been simulated by this preparation step.",
        "",
        "See RESEARCH_PROTOCOL_V002.md and EXPERIMENTS_V002.csv for the staged questions and decision rules.",
        "",
    ]
    (RESEARCH / "UNIVERSE_50.md").write_text("\n".join(report), encoding="utf-8")
    print(by_class.to_string())
    print(
        "Foreign P&L currencies:",
        table.loc[table.pnl_currency.ne("USD"), "pnl_currency"]
        .value_counts()
        .to_dict(),
    )
    print(
        "Zero/missing commission candidates:",
        table.loc[table.source_commission.le(0), "market_id"].tolist(),
    )
    print("All 50 prepared; no performance run.")


if __name__ == "__main__":
    main()
