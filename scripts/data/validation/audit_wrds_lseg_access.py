"""Audit accessible LSEG-related WRDS metadata without reading observations."""

import argparse
import json
import os
from pathlib import Path

from ath_breakout.data.wrds_credentials import load_wrds_password


DEFAULT_OUTPUT = Path("data/state/wrds_lseg_schema_audit.json")
RELEVANT_TERMS = (
    "daily",
    "price",
    "equity",
    "security",
    "datastream",
    "worldscope",
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save accessible LSEG-related WRDS metadata for source evaluation."
    )
    parser.add_argument("--username", default=os.environ.get("WRDS_USERNAME"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    username = arguments.username or input("WRDS username: ").strip()
    if not username:
        raise SystemExit("A WRDS username is required.")

    try:
        import wrds
    except ImportError as error:
        raise SystemExit(
            'WRDS support is not installed. Run: python -m pip install -e ".[wrds]"'
        ) from error

    connection_arguments = {"wrds_username": username}
    password = load_wrds_password(username)
    if password is not None:
        connection_arguments["wrds_password"] = password

    print("Reading accessible LSEG-related WRDS metadata...")
    connection = wrds.Connection(**connection_arguments)
    try:
        schemas = connection.raw_sql(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE LOWER(schema_name) LIKE 'tr\\_%%' ESCAPE '\\'
               OR LOWER(schema_name) LIKE '%%lseg%%'
               OR LOWER(schema_name) LIKE '%%refinitiv%%'
               OR LOWER(schema_name) LIKE '%%datastream%%'
               OR LOWER(schema_name) LIKE '%%worldscope%%'
               OR LOWER(schema_name) LIKE 'ibes%%'
            ORDER BY schema_name
            """
        )
        schema_names = schemas["schema_name"].astype(str).tolist()
        if schema_names:
            tables = connection.raw_sql(
                """
                SELECT table_schema, table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = ANY(%(schemas)s)
                ORDER BY table_schema, table_name
                """,
                params={"schemas": schema_names},
            )
            columns = connection.raw_sql(
                """
                SELECT
                    table_schema,
                    table_name,
                    column_name,
                    ordinal_position,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = ANY(%(schemas)s)
                ORDER BY table_schema, table_name, ordinal_position
                """,
                params={"schemas": schema_names},
            )
        else:
            tables = schemas.iloc[0:0].copy()
            columns = schemas.iloc[0:0].copy()
    finally:
        connection.close()

    table_records = tables.to_dict(orient="records")
    column_records = columns.to_dict(orient="records")
    relevant_tables = [
        f"{row['table_schema']}.{row['table_name']}"
        for row in table_records
        if any(term in row["table_name"].lower() for term in RELEVANT_TERMS)
    ]
    audit = {
        "schemas": schema_names,
        "table_count": len(table_records),
        "column_count": len(column_records),
        "relevant_tables": relevant_tables,
        "tables": table_records,
        "columns": column_records,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"Accessible matching schemas: {len(schema_names):,}.")
    print(f"Tables found: {len(table_records):,}; columns found: {len(column_records):,}.")
    print(f"Schema names: {', '.join(schema_names) if schema_names else 'none'}")
    print(f"Relevant table candidates: {len(relevant_tables):,}.")
    print(f"Local metadata file: {arguments.output.resolve()}")
    print("Licensed observations transferred: 0.")


if __name__ == "__main__":
    main()
