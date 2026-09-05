"""Build point-in-time CRSP liquidity universes with server-side aggregation."""

from datetime import date

import pandas as pd


CRSP_UNIVERSE_COLUMNS = [
    "formation_date",
    "effective_date",
    "rank",
    "security_id",
    "permno",
    "ticker",
    "median_dollar_volume",
    "observation_count",
    "last_price",
    "market_cap",
    "primary_exchange",
    "source",
]


def build_crsp_liquidity_universe_query() -> str:
    """Return a bounded query that aggregates liquidity inside WRDS."""
    return """
        WITH eligible_days AS (
            SELECT
                permno,
                ticker,
                dlycaldt,
                dlyclose,
                dlyvol,
                dlycap,
                primaryexch
            FROM crsp_q_stock.dsf_v2
            WHERE dlycaldt BETWEEN %(lookback_start)s AND %(formation_date)s
              AND primaryexch IN ('N', 'A', 'Q')
              AND conditionaltype = 'RW'
              AND tradingstatusflg = 'A'
              AND sharetype = 'NS'
              AND securitytype = 'EQTY'
              AND securitysubtype = 'COM'
              AND usincflg = 'Y'
              AND issuertype = 'CORP'
              AND dlyclose > 0
              AND dlyvol >= 0
        ),
        liquidity AS (
            SELECT
                permno,
                COUNT(*) AS observation_count,
                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY dlyclose * dlyvol
                ) AS median_dollar_volume
            FROM eligible_days
            GROUP BY permno
            HAVING COUNT(*) >= %(minimum_observations)s
        ),
        latest AS (
            SELECT DISTINCT ON (permno)
                permno,
                ticker,
                dlycaldt,
                dlyclose,
                dlycap,
                primaryexch
            FROM eligible_days
            ORDER BY permno, dlycaldt DESC
        )
        SELECT
            latest.permno,
            latest.ticker,
            liquidity.median_dollar_volume,
            liquidity.observation_count,
            latest.dlyclose AS last_price,
            latest.dlycap AS market_cap,
            latest.primaryexch AS primary_exchange
        FROM liquidity
        JOIN latest USING (permno)
        WHERE latest.dlyclose >= %(minimum_price)s
          AND latest.dlycap > 0
        ORDER BY
            liquidity.median_dollar_volume DESC,
            latest.dlycap DESC,
            latest.permno
        LIMIT %(universe_size)s
    """


def download_crsp_liquidity_universe(
    connection,
    lookback_start: date | str,
    formation_date: date | str,
    effective_date: date | str,
    universe_size: int = 3_000,
    minimum_observations: int = 40,
    minimum_price: float = 5.0,
) -> pd.DataFrame:
    """Download one point-in-time universe without transferring daily rows."""
    if universe_size <= 0:
        raise ValueError("Universe size must be positive")
    if minimum_observations <= 0:
        raise ValueError("Minimum observations must be positive")
    if minimum_price <= 0:
        raise ValueError("Minimum price must be positive")

    raw_data = connection.raw_sql(
        build_crsp_liquidity_universe_query(),
        params={
            "lookback_start": str(lookback_start),
            "formation_date": str(formation_date),
            "minimum_observations": minimum_observations,
            "minimum_price": minimum_price,
            "universe_size": universe_size,
        },
    )
    return normalize_crsp_liquidity_universe(
        raw_data,
        formation_date=formation_date,
        effective_date=effective_date,
        maximum_size=universe_size,
    )


def normalize_crsp_liquidity_universe(
    raw_data: pd.DataFrame,
    formation_date: date | str,
    effective_date: date | str,
    maximum_size: int,
) -> pd.DataFrame:
    """Normalize and validate one ranked point-in-time universe snapshot."""
    required = {
        "permno",
        "ticker",
        "median_dollar_volume",
        "observation_count",
        "last_price",
        "market_cap",
        "primary_exchange",
    }
    missing = sorted(required - set(raw_data.columns))
    if missing:
        raise ValueError(f"Missing CRSP universe columns: {', '.join(missing)}")

    data = raw_data[list(required)].copy()
    data["permno"] = pd.to_numeric(data["permno"], errors="raise").astype("Int64")
    data["ticker"] = data["ticker"].astype("string")
    for column in (
        "median_dollar_volume",
        "observation_count",
        "last_price",
        "market_cap",
    ):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.sort_values(
        ["median_dollar_volume", "market_cap", "permno"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    data["formation_date"] = pd.Timestamp(formation_date).normalize()
    data["effective_date"] = pd.Timestamp(effective_date).normalize()
    data["rank"] = pd.RangeIndex(1, len(data) + 1)
    data["security_id"] = data["permno"].astype(str)
    data["source"] = "CRSP CIZ quarterly"
    data = data[CRSP_UNIVERSE_COLUMNS]
    validate_crsp_liquidity_universe(data, maximum_size=maximum_size)
    return data


def validate_crsp_liquidity_universe(
    data: pd.DataFrame,
    maximum_size: int,
) -> None:
    """Reject ambiguous, unranked, or look-ahead universe snapshots."""
    if len(data) > maximum_size:
        raise ValueError("CRSP universe exceeds requested size")
    if data["permno"].duplicated().any():
        raise ValueError("Duplicate PERMNO values found in CRSP universe")
    if data["ticker"].isna().any():
        raise ValueError("Missing point-in-time ticker found in CRSP universe")
    if not data["rank"].equals(pd.Series(range(1, len(data) + 1))):
        raise ValueError("CRSP universe ranks are not contiguous")
    if (data["effective_date"] <= data["formation_date"]).any():
        raise ValueError("CRSP universe must become effective after formation")
    if (data["median_dollar_volume"] < 0).any():
        raise ValueError("CRSP median dollar volume cannot be negative")
