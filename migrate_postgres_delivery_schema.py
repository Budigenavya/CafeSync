"""Apply the small, idempotent PostgreSQL schema update needed by delivery.

This command only creates the riders table and adds its nullable reference to
orders. It never copies, updates, or deletes order/product/customer data.
Run it deliberately before deploying delivery routes against PostgreSQL.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from psycopg import sql
from dotenv import load_dotenv


backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env", override=False)
load_dotenv(backend_dir.parent / "CafeSync_Postgres_Migration" / ".env", override=False)

database_url = os.environ.get("DATABASE_URL", "").strip()
if not database_url and all(
    os.environ.get(key)
    for key in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
):
    database_url = psycopg.conninfo.make_conninfo(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        sslmode="require",
        connect_timeout=10,
    )
if not database_url:
    raise SystemExit("DATABASE_URL is required in the environment or a supported .env file.")


def main() -> int:
    with psycopg.connect(database_url, sslmode="require", connect_timeout=10) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_schema()")
            schema_name = cursor.fetchone()[0]

            cursor.execute(
                "SELECT to_regclass(%s), to_regclass(%s)",
                (f'"{schema_name}"."orders"', f'"{schema_name}"."customers"'),
            )
            orders_table, customers_table = cursor.fetchone()
            if not orders_table or not customers_table:
                raise RuntimeError(
                    f"Expected orders and customers tables in schema {schema_name!r}; no changes applied."
                )

            schema = sql.Identifier(schema_name)
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.riders (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL DEFAULT '',
                    vehicle TEXT NOT NULL DEFAULT '',
                    vehicle_number TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'Available',
                    current_location TEXT NOT NULL DEFAULT ''
                )
            """).format(schema))
            for column, definition in {
                "name": "TEXT NOT NULL DEFAULT ''",
                "phone": "TEXT NOT NULL DEFAULT ''",
                "vehicle": "TEXT NOT NULL DEFAULT ''",
                "vehicle_number": "TEXT NOT NULL DEFAULT ''",
                "status": "TEXT NOT NULL DEFAULT 'Available'",
                "current_location": "TEXT NOT NULL DEFAULT ''",
            }.items():
                cursor.execute(sql.SQL("ALTER TABLE {}.riders ADD COLUMN IF NOT EXISTS {} " + definition)
                               .format(schema, sql.Identifier(column)))
            cursor.execute(sql.SQL("""
                ALTER TABLE {}.orders
                ADD COLUMN IF NOT EXISTS rider_id INTEGER
            """).format(schema))

            cursor.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema=%s AND table_name='orders'
                  AND constraint_name='orders_rider_id_fkey'
            """, (schema_name,))
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("""
                    ALTER TABLE {}.orders
                    ADD CONSTRAINT orders_rider_id_fkey
                    FOREIGN KEY (rider_id) REFERENCES {}.riders(id)
                """).format(schema, schema))

            cursor.execute(sql.SQL("""
                SELECT setval(pg_get_serial_sequence(%s, 'id'),
                              GREATEST(COALESCE(MAX(id), 1), 1), COUNT(*) > 0)
                FROM {}.riders
            """).format(schema), (f'"{schema_name}"."riders"',))

        conn.commit()

    print(f"Delivery schema migration applied to schema {schema_name!r}.")
    print("Created/verified riders and orders.rider_id; existing order data was not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
