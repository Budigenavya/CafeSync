"""Read-only checks for a CafeSync PostgreSQL migration.

Run with DATABASE_URL configured in the environment or backend/.env.
This utility never writes to the target database.
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from psycopg import sql


backend_dir = Path(__file__).resolve().parent

# Load configuration files without overriding existing environment variables.
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env", override=False)
load_dotenv(
    backend_dir.parent / "CafeSync_Postgres_Migration" / ".env",
    override=False,
)

database_url = os.environ.get("DATABASE_URL", "").strip()

# Build a connection string from the existing PG* settings if needed.
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
app_postgres_enabled = os.environ.get("CAFESYNC_USE_POSTGRES", "false").strip().lower() in {
    "1", "true", "yes"
}
print(f"CafeSync PostgreSQL mode: {'enabled' if app_postgres_enabled else 'disabled'}.")
if not database_url:
    print("BLOCKED: DATABASE_URL is not configured in the environment, backend/.env, or project-root .env.")
    raise SystemExit(2)


REQUIRED_TABLES = {
    "users",
    "categories",
    "products",
    "product_addons",
    "ingredients",
    "recipes",
    "ingredient_movements",
    "suppliers",
    "stock_receipts",
    "stock_receipt_items",
    "audit_log",
    "day_closings",
    "customers",
    "tables",
    "orders",
    "order_items",
    "employees",
    "settings",
    "held_orders",
    "inventory_logs",
    "payments",
    "expenses",
    "riders",
}

REQUIRED_COLUMNS = {
    "orders": {
        "id", "bill_no", "customer_id", "order_type", "order_source",
        "total", "status", "payment_status", "created_at", "rider_id",
    },
    "customers": {"id", "name", "phone", "address"},
    "riders": {
        "id", "name", "phone", "vehicle", "vehicle_number",
        "status", "current_location",
    },
}


def main() -> int:
    failures = []
    if not app_postgres_enabled:
        failures.append("CAFESYNC_USE_POSTGRES is disabled; the app will use SQLite instead of this PostgreSQL database.")
    try:
        with psycopg.connect(database_url, sslmode="require", connect_timeout=10) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SELECT current_database(), current_schema()")
                database_name, schema_name = cursor.fetchone()
                print(f"Connected read-only to database '{database_name}', schema '{schema_name}'.")

                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema=current_schema() AND table_type='BASE TABLE'
                    """
                )
                tables = {row[0] for row in cursor.fetchall()}
                missing = sorted(REQUIRED_TABLES - tables)
                print(f"Required tables: {len(REQUIRED_TABLES) - len(missing)}/{len(REQUIRED_TABLES)} present.")
                if missing:
                    failures.append("Missing tables: " + ", ".join(missing))

                cursor.execute(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema=current_schema()
                      AND table_name=ANY(%s)
                    """,
                    (sorted(REQUIRED_COLUMNS),),
                )
                columns_by_table = {}
                for table, column in cursor.fetchall():
                    columns_by_table.setdefault(table, set()).add(column)
                for table, required_columns in REQUIRED_COLUMNS.items():
                    if table not in tables:
                        continue
                    absent_columns = sorted(required_columns - columns_by_table.get(table, set()))
                    if absent_columns:
                        failures.append(
                            f"{table} is missing required columns: " + ", ".join(absent_columns)
                        )
                    else:
                        print(f"{table} required columns: present.")

                cursor.execute(
                    """
                    SELECT tc.table_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name=kcu.constraint_name
                     AND tc.table_schema=kcu.table_schema
                     AND tc.table_name=kcu.table_name
                    WHERE tc.constraint_type='PRIMARY KEY'
                      AND tc.table_schema=current_schema()
                      AND tc.table_name=ANY(%s)
                    ORDER BY tc.table_name, kcu.ordinal_position
                    """,
                    (sorted(REQUIRED_TABLES),),
                )
                primary_keys = {}
                for table, column in cursor.fetchall():
                    primary_keys.setdefault(table, []).append(column)
                print("Insert-target primary keys:")
                for table in sorted(REQUIRED_TABLES):
                    if table in tables:
                        columns = primary_keys.get(table, [])
                        print(f"{table}: {', '.join(columns) if columns else 'MISSING PRIMARY KEY'}")
                        if columns != ["id"]:
                            failures.append(f"{table} does not have the expected id primary key.")

                if "products" in tables:
                    cursor.execute(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema=current_schema() AND table_name='products'
                        """
                    )
                    product_columns = {row[0] for row in cursor.fetchall()}
                    needed = {"id", "name", "price"}
                    absent = sorted(needed - product_columns)
                    if absent:
                        failures.append("Products table is missing columns: " + ", ".join(absent))
                    else:
                        cursor.execute("SELECT COUNT(*) FROM products")
                        product_count = cursor.fetchone()[0]
                        print(f"Products migrated: {product_count}.")
                        if product_count == 0:
                            failures.append("Products table is empty.")

                for table in ("users", "categories", "orders", "order_items", "payments"):
                    if table in tables:
                        cursor.execute(
                            sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                                sql.Identifier(schema_name), sql.Identifier(table)
                            )
                        )
                        print(f"{table} rows: {cursor.fetchone()[0]}.")

                if "ingredient_movements" in tables:
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM information_schema.key_column_usage kcu
                        JOIN information_schema.table_constraints tc
                          ON tc.constraint_schema = kcu.constraint_schema
                         AND tc.constraint_name = kcu.constraint_name
                         AND tc.table_name = kcu.table_name
                        JOIN information_schema.constraint_column_usage ccu
                          ON ccu.constraint_schema = tc.constraint_schema
                         AND ccu.constraint_name = tc.constraint_name
                        WHERE tc.constraint_schema = current_schema()
                          AND tc.table_name = 'ingredient_movements'
                          AND tc.constraint_type = 'FOREIGN KEY'
                          AND kcu.column_name = 'order_id'
                          AND ccu.table_name = 'orders'
                          AND ccu.column_name = 'id'
                        """
                    )
                    if cursor.fetchone()[0] != 1:
                        failures.append("ingredient_movements.order_id foreign key is missing.")
                    else:
                        print("ingredient_movements.order_id foreign key: present.")

                if "orders" in tables and "riders" in tables:
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM information_schema.key_column_usage kcu
                        JOIN information_schema.table_constraints tc
                          ON tc.constraint_schema=kcu.constraint_schema
                         AND tc.constraint_name=kcu.constraint_name
                         AND tc.table_name=kcu.table_name
                        JOIN information_schema.constraint_column_usage ccu
                          ON ccu.constraint_schema=tc.constraint_schema
                         AND ccu.constraint_name=tc.constraint_name
                        WHERE tc.constraint_schema=current_schema()
                          AND tc.table_name='orders'
                          AND tc.constraint_type='FOREIGN KEY'
                          AND kcu.column_name='rider_id'
                          AND ccu.table_name='riders'
                          AND ccu.column_name='id'
                        """
                    )
                    if cursor.fetchone()[0] != 1:
                        failures.append("orders.rider_id foreign key to riders.id is missing.")
                    else:
                        print("orders.rider_id foreign key: present.")

                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.columns
                    WHERE table_schema=current_schema() AND column_name='id'
                      AND (left(column_default, 8)='nextval(' OR is_identity='YES')
                    """
                )
                sequence_tables = [row[0] for row in cursor.fetchall()]
                sequence_problems = []
                for table in sequence_tables:
                    cursor.execute(
                        "SELECT pg_get_serial_sequence(%s, 'id')",
                        (f'"{schema_name}"."{table}"',),
                    )
                    sequence_name = cursor.fetchone()[0]
                    if not sequence_name:
                        sequence_problems.append(f"{table}: sequence not discoverable")
                        continue
                    cursor.execute(
                        sql.SQL("SELECT COALESCE(MAX(id), 0) FROM {}.{}").format(
                            sql.Identifier(schema_name), sql.Identifier(table)
                        )
                    )
                    max_id = cursor.fetchone()[0]
                    cursor.execute(
                        sql.SQL("SELECT last_value, is_called FROM {}").format(
                            sql.Identifier(*sequence_name.split("."))
                        )
                    )
                    last_value, is_called = cursor.fetchone()
                    if (is_called and last_value < max_id) or (not is_called and last_value <= max_id):
                        sequence_problems.append(
                            f"{table}: sequence value {last_value} is behind max id {max_id}"
                        )
                print(f"ID sequences checked: {len(sequence_tables)}.")
                if sequence_problems:
                    failures.extend(sequence_problems)
                elif sequence_tables:
                    print("ID sequences: current with migrated IDs.")

        if failures:
            print("MIGRATION CHECK: FAILED")
            for failure in failures:
                print(f"- {failure}")
            return 1
        print("MIGRATION CHECK: PASSED")
        return 0
    except Exception as exc:
        print(f"MIGRATION CHECK: BLOCKED ({type(exc).__name__}: {exc})")
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
