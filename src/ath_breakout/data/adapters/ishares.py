"""Download an IWV holdings snapshot as a Russell 3000 proxy universe."""

import csv
from io import StringIO
from urllib.request import Request, urlopen

import pandas as pd

from ath_breakout.data.universe import validate_universe


IWV_HOLDINGS_URL = (
    "https://www.ishares.com/us/products/239714/"
    "ishares-russell-3000-etf/latest-holdings.csv"
)


def parse_iwv_holdings(csv_text: str) -> pd.DataFrame:
    """Convert the iShares holdings CSV into our universe format."""
    csv_rows = list(csv.reader(StringIO(csv_text)))
    as_of_date = csv_rows[1][1]

    holdings = pd.read_csv(StringIO(csv_text), skiprows=8)
    equities = holdings[holdings["Asset Class"] == "Equity"].copy()

    equities = equities[["Ticker", "Name", "Sector"]]
    equities = equities.dropna(subset=["Ticker"])
    equities = equities[equities["Ticker"] != "-"]

    non_tradable_names = equities["Name"].str.contains(
        " CVR|VESTING Prvt",
        case=False,
        na=False,
    )
    equities = equities[non_tradable_names == False].copy()

    equities["security_id"] = equities["Ticker"]
    equities["ticker"] = equities["Ticker"]

    yahoo_ticker_changes = {
        "BRKB": "BRK-B",
        "BFA": "BF-A",
        "BFB": "BF-B",
        "GEFB": "GEF-B",
        "HEIA": "HEI-A",
        "LENB": "LEN-B",
        "MOGA": "MOG-A",
        "UHALB": "UHAL-B",
    }
    equities["ticker"] = equities["ticker"].replace(yahoo_ticker_changes)

    equities = equities.rename(columns={"Name": "name", "Sector": "sector"})
    equities["as_of_date"] = pd.to_datetime(as_of_date)
    equities["downloaded_at"] = pd.Timestamp.now(tz="UTC")
    equities["source"] = "IWV holdings"

    result_columns = [
        "security_id",
        "ticker",
        "name",
        "sector",
        "as_of_date",
        "downloaded_at",
        "source",
    ]
    result = equities[result_columns].reset_index(drop=True)
    validate_universe(result)
    return result


def download_iwv_universe() -> pd.DataFrame:
    """Download the newest available IWV holdings snapshot from iShares."""
    request = Request(IWV_HOLDINGS_URL, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, timeout=30) as response:
        csv_text = response.read().decode("utf-8-sig")

    return parse_iwv_holdings(csv_text)
