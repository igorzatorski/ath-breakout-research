"""Audit CRSP CIZ table metadata without downloading licensed observations."""

import argparse
import json
import os
from pathlib import Path

from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_SCHEMA = "crsp_q_stock"
DEFAULT_OUTPUT = Path("data/state/wrds_crsp_schema_audit.json")
RELEVANT_TERMS = (
    "dsf",
    "daily",
    "dly",
    "delist",
    "distribution",
    "securityinfo",
    "stockname",
    "share",
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save CRSP table and column metadata for adapter design."
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("WRDS_USERNAME"),
        help="WRDS username (or set WRDS_USERNAME).",
    )
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    username = arguments.username or input("WRDS username: ").strip()
    if not username:
        raise SystemExit("A WRDS username is required.")
    if not arguments.schema.replace("_", "").isalnum():
        raise SystemExit("Schema names may contain only letters, digits, and underscores.")

    try:
        import wrds
    except ImportError as error:
        raise SystemExit(
            'WRDS support is not installed. Run: python -m pip install -e ".[wrds]"'
        ) from error

    password = load_wrds_password(username)
    if password is None:
        print("No Windows credential found; WRDS will request the password.")

    connection_arguments = {"wrds_username": username}
    if password is not None:
        connection_arguments["wrds_password"] = password

    print(f"Reading metadata for {arguments.schema}...")
    connection = wrds.Connection(**connection_arguments)
    try:
        tables = connection.raw_sql(
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = %(schema)s
            ORDER BY table_name
            """,
            params={"schema": arguments.schema},
        )
        columns = connection.raw_sql(
            """
            SELECT
                table_name,
                column_name,
                ordinal_position,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = %(schema)s
            ORDER BY table_name, ordinal_position
            """,
            params={"schema": arguments.schema},
        )
    finally:
        connection.close()

    table_records = tables.to_dict(orient="records")
    column_records = columns.to_dict(orient="records")
    relevant_tables = sorted(
        table["table_name"]
        for table in table_records
        if any(term in table["table_name"].lower() for term in RELEVANT_TERMS)
    )
    column_counts = (
        columns.groupby("table_name").size().astype(int).to_dict()
        if not columns.empty
        else {}
    )
    audit = {
        "schema": arguments.schema,
        "table_count": len(table_records),
        "column_count": len(column_records),
        "relevant_tables": relevant_tables,
        "column_counts": column_counts,
        "tables": table_records,
        "columns": column_records,
    }

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"Success: found {len(table_records):,} tables and {len(column_records):,} columns.")
    print(f"Relevant table names: {', '.join(relevant_tables)}")
    print(f"Local metadata file: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
