"""Small DB-API compatibility layer for the application's gradual PG port.

The application continues to use SQLite by default.  In PostgreSQL mode this
adapter preserves the common SQLite-facing connection/row APIs while SQL and
schema differences are moved into this one boundary.
"""

from __future__ import annotations

import re
import sqlite3

import psycopg


class HybridRow(dict):
    """Mapping row that also supports SQLite's positional indexing."""

    def __init__(self, names, values):
        super().__init__(zip(names, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


def _hybrid_row_factory(cursor):
    names = [column.name for column in cursor.description]
    return lambda values: HybridRow(names, values)


def _qmark_to_pyformat(sql: str) -> str:
    """Convert positional qmark placeholders without touching quoted text."""
    output = []
    quote = None
    i = 0
    while i < len(sql):
        char = sql[i]
        if quote:
            output.append(char)
            if char == quote:
                if i + 1 < len(sql) and sql[i + 1] == quote:
                    output.append(sql[i + 1])
                    i += 1
                else:
                    quote = None
        elif char in ("'", '"'):
            quote = char
            output.append(char)
        elif char == "?":
            output.append("%s")
        else:
            output.append(char)
        i += 1
    return "".join(output)


def _translate_sql(sql: str) -> tuple[str, bool, bool]:
    """Translate the common SQLite SQL used by CafeSync to PostgreSQL.

    Returns (sql, ignore_conflicts, is_insert). Date-function compatibility is
    intentionally narrow and documented here; route-specific SQL is still
    being migrated to explicit PostgreSQL expressions.
    """
    source = sql.strip().rstrip(";").strip()
    if re.match(r"^PRAGMA\s+foreign_keys\s*=", source, re.I):
        return "", False, False

    source = re.sub(
        r"^PRAGMA\s+table_info\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)$",
        r"__CAFESYNC_TABLE_INFO__\1",
        source,
        flags=re.I,
    )
    if source.startswith("__CAFESYNC_TABLE_INFO__"):
        return source, False, False

    ignore_conflicts = bool(re.match(r"^INSERT\s+OR\s+IGNORE\s+INTO\b", source, re.I))
    source = re.sub(r"^INSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", source, flags=re.I)
    source = re.sub(
        r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
        "SERIAL PRIMARY KEY",
        source,
        flags=re.I,
    )
    source = re.sub(r"\bIFNULL\s*\(", "COALESCE(", source, flags=re.I)

    # SQLite's NOCASE collation has no direct PostgreSQL equivalent.
    source = re.sub(
        r"([A-Za-z_][A-Za-z0-9_.]*)\s*=\s*(\?|%s|\$\d+)\s+COLLATE\s+NOCASE",
        r"LOWER(\1)=LOWER(\2)",
        source,
        flags=re.I,
    )
    source = re.sub(
        r"(ORDER\s+BY\s+)([A-Za-z_][A-Za-z0-9_.]*)\s+COLLATE\s+NOCASE",
        r"\1LOWER(\2)",
        source,
        flags=re.I,
    )
    source = re.sub(r"\s+COLLATE\s+NOCASE\b", "", source, flags=re.I)
    source = re.sub(r"\bLIKE\b", "ILIKE", source, flags=re.I)

    # Existing timestamp columns are migrated as UTC-naive timestamps.
    india_today = "(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::date"
    india_timestamp = "(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')"
    strftime_formats = {"%Y-%m": "YYYY-MM", "%Y": "YYYY", "%m": "MM", "%H": "HH24"}

    def sqlite_week_number(expression):
        date_value = f"({expression})::date"
        year_start = f"date_trunc('year', {expression})::date"
        first_monday = f"({year_start} + ((8 - EXTRACT(ISODOW FROM {year_start})::int) % 7))"
        week_value = (
            f"CASE WHEN {date_value} < {first_monday} THEN 0 "
            f"ELSE (({date_value} - {first_monday}) / 7 + 1) END"
        )
        return f"TO_CHAR(({week_value}), 'FM00')"
    source = re.sub(
        r"DATE\(\s*'now'\s*,\s*'\+5 hours'\s*,\s*'\+30 minutes'\s*\)",
        india_today, source, flags=re.I,
    )
    source = re.sub(r"DATE\(\s*'now'\s*,\s*'localtime'\s*\)", india_today, source, flags=re.I)
    source = re.sub(
        r"DATE\(\s*'now'\s*,\s*'(-\d+) day'\s*,\s*'localtime'\s*\)",
        lambda m: f"({india_today} - INTERVAL '{abs(int(m.group(1)))} days')::date",
        source, flags=re.I,
    )
    source = re.sub(
        r"DATE\(\s*'now'\s*,\s*'(-?\d+) day'\s*\)",
        lambda m: f"(CURRENT_DATE + INTERVAL '{int(m.group(1))} days')::date",
        source, flags=re.I,
    )
    source = re.sub(r"DATE\(\s*'now'\s*\)", "CURRENT_DATE", source, flags=re.I)
    source = re.sub(
        r"DATE\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*,\s*'\+5 hours'\s*,\s*'\+30 minutes'\s*\)",
        r"((\1 AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')::date)", source, flags=re.I,
    )
    source = re.sub(
        r"DATE\(\s*datetime\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*,\s*'\+5 hours'\s*,\s*'\+30 minutes'\s*\)\s*\)",
        r"((\1 AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')::date)", source, flags=re.I,
    )
    source = re.sub(
        r"DATE\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*,\s*'localtime'\s*\)",
        r"((\1 AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')::date)", source, flags=re.I,
    )
    source = re.sub(
        r"DATE\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*,\s*'(-\d+) day'\s*\)",
        lambda m: f"({m.group(1)}::date - INTERVAL '{abs(int(m.group(2)))} days')::date",
        source, flags=re.I,
    )
    source = re.sub(r"DATE\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\)", r"(\1::date)", source, flags=re.I)

    source = re.sub(
        r"datetime\(\s*'now'\s*,\s*'\+5 hours'\s*,\s*'\+30 minutes'\s*\)",
        india_timestamp, source, flags=re.I,
    )
    source = re.sub(
        r"datetime\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*,\s*'\+5 hours'\s*,\s*'\+30 minutes'\s*\)",
        r"(\1 AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')", source, flags=re.I,
    )
    source = re.sub(
        r"strftime\(\s*'%H'\s*,\s*datetime\(\s*\?\s*,\s*'\+5 hours'\s*,\s*'\+30 minutes'\s*\)\s*\)",
        "EXTRACT(HOUR FROM (%s::timestamp + INTERVAL '5 hours 30 minutes'))::text",
        source, flags=re.I,
    )
    source = re.sub(
        r"strftime\(\s*'%w'\s*,\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\)",
        r"EXTRACT(DOW FROM \1)::text", source,
    )
    source = re.sub(
        r"strftime\(\s*'%w'\s*,\s*'now'\s*,\s*'localtime'\s*\)",
        f"EXTRACT(DOW FROM {india_timestamp})::text", source,
    )
    source = re.sub(
        r"strftime\(\s*'%w'\s*,\s*'now'\s*\)",
        "EXTRACT(DOW FROM CURRENT_TIMESTAMP)::text", source,
    )
    source = re.sub(
        r"strftime\(\s*'%W'\s*,\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\)",
        lambda m: sqlite_week_number(m.group(1)), source,
    )
    source = re.sub(
        r"strftime\(\s*'%W'\s*,\s*'now'\s*,\s*'localtime'\s*\)",
        lambda _m: sqlite_week_number(india_timestamp), source,
    )
    source = re.sub(
        r"strftime\(\s*'%W'\s*,\s*'now'\s*\)",
        lambda _m: sqlite_week_number("CURRENT_TIMESTAMP"), source,
    )
    source = re.sub(
        r"strftime\(\s*'(%Y(?:-%m)?|%m|%H)'\s*,\s*'now'\s*,\s*'localtime'\s*\)",
        lambda m: f"TO_CHAR({india_timestamp}, '{strftime_formats.get(m.group(1), 'YYYY')}')",
        source, flags=re.I,
    )
    source = re.sub(
        r"strftime\(\s*'(%Y(?:-%m)?|%m|%H)'\s*,\s*'now'\s*\)",
        lambda m: f"TO_CHAR(CURRENT_TIMESTAMP, '{strftime_formats.get(m.group(1), 'YYYY')}')",
        source, flags=re.I,
    )

    # Dashboard/report queries sometimes wrap a timestamp in SQLite's datetime
    # modifier before formatting it. Translate that nested expression before
    # the simpler strftime patterns below.
    source = re.sub(
        r"strftime\(\s*'(%Y(?:-%m)?|%m|%H)'\s*,\s*datetime\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*,\s*'\+5 hours'\s*,\s*'\+30 minutes'\s*\)\s*\)",
        lambda m: (
            f"TO_CHAR(({m.group(2)} AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'), "
            f"'{strftime_formats.get(m.group(1), 'YYYY')}')"
        ),
        source,
        flags=re.I,
    )
    source = re.sub(
        r"strftime\(\s*'(%Y(?:-%m)?|%m|%H)'\s*,\s*\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s+AT\s+TIME\s+ZONE\s+'UTC'\s+AT\s+TIME\s+ZONE\s+'Asia/Kolkata'\s*\)\s*\)",
        lambda m: (
            f"TO_CHAR(({m.group(2)} AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'), "
            f"'{strftime_formats.get(m.group(1), 'YYYY')}')"
        ),
        source,
        flags=re.I,
    )

    for sqlite_format, pg_format in strftime_formats.items():
        source = re.sub(
            rf"strftime\(\s*'{re.escape(sqlite_format)}'\s*,\s*([^,()]+)\s*\)",
            rf"TO_CHAR(\1, '{pg_format}')",
            source,
            flags=re.I,
        )

    # SQLite REAL is an 8-byte float; PostgreSQL REAL is only 4 bytes.
    if re.match(r"^CREATE\s+TABLE\b", source, re.I):
        source = re.sub(r"\bREAL\b", "DOUBLE PRECISION", source, flags=re.I)
        # SQLite accepts this forward reference, but PostgreSQL requires the
        # referenced orders table to exist when the DDL is executed. The FK is
        # added after database.py has created all application tables.
        if re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+ingredient_movements\b", source, re.I):
            source = re.sub(
                r",\s*FOREIGN\s+KEY\s*\(\s*order_id\s*\)\s*REFERENCES\s*orders\s*\(\s*id\s*\)",
                "", source, flags=re.I,
            )

    # SQLite compares DATE(...) results with bound strings implicitly. In
    # PostgreSQL, date = text is not a valid operator, so keep the same intent
    # by typing the bound value when a date expression is compared to a qmark.
    source = re.sub(r"(::date\))\s*(=|<>|!=|<=|>=|<|>)\s*\?", r"\1 \2 ?::date", source, flags=re.I)

    is_insert = bool(re.match(r"^INSERT\s+INTO\b", source, re.I))
    source = _qmark_to_pyformat(source)
    return source, ignore_conflicts, is_insert


class PostgresCursor:
    def __init__(self, connection, raw_cursor=None):
        self.connection = connection
        self.raw = raw_cursor or connection.raw.cursor()
        self._lastrowid = None
        self._pending_row = None
        self._synthetic_rows = None

    def execute(self, sql, params=()):
        translated, ignore_conflicts, is_insert = _translate_sql(sql)
        self._lastrowid = None
        self._pending_row = None
        self._synthetic_rows = None
        if translated == "":
            return self
        if translated.startswith("__CAFESYNC_TABLE_INFO__"):
            table_name = translated.removeprefix("__CAFESYNC_TABLE_INFO__")
            raw = self.connection.raw.cursor()
            raw.execute("""
                SELECT c.ordinal_position - 1 AS cid, c.column_name AS name,
                       c.data_type AS type,
                       CASE WHEN c.is_nullable='NO' THEN 1 ELSE 0 END AS "notnull",
                       c.column_default AS dflt_value,
                       CASE WHEN pk.column_name IS NULL THEN 0 ELSE 1 END AS pk
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT k.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage k
                      ON tc.constraint_name=k.constraint_name
                     AND tc.table_schema=k.table_schema AND tc.table_name=k.table_name
                    WHERE tc.constraint_type='PRIMARY KEY' AND tc.table_schema=current_schema()
                      AND tc.table_name=%s
                ) pk ON pk.column_name=c.column_name
                WHERE c.table_schema=current_schema() AND c.table_name=%s
                ORDER BY c.ordinal_position
            """, (table_name, table_name))
            self.raw = raw
            return self

        query = translated
        if is_insert and " RETURNING " not in query.upper():
            if ignore_conflicts:
                query += " ON CONFLICT DO NOTHING"
            query += " RETURNING id"
        try:
            self.raw.execute(query, params)
            if is_insert and " RETURNING " in query.upper():
                self._pending_row = self.raw.fetchone()
                if self._pending_row is not None:
                    self._lastrowid = self._pending_row["id"]
        except psycopg.IntegrityError as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc
        except psycopg.Error as exc:
            raise sqlite3.OperationalError(str(exc)) from exc
        return self

    def executemany(self, sql, params_seq):
        translated, ignore_conflicts, _ = _translate_sql(sql)
        if ignore_conflicts:
            translated += " ON CONFLICT DO NOTHING"
        self._lastrowid = None
        try:
            self.raw.executemany(translated, params_seq)
        except psycopg.IntegrityError as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc
        except psycopg.Error as exc:
            raise sqlite3.OperationalError(str(exc)) from exc
        return self

    def executescript(self, script):
        # database.py's initialization script contains only simple CREATE TABLE
        # statements, with no semicolons embedded in string literals.
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)
        return self

    def fetchone(self):
        if self._pending_row is not None:
            row, self._pending_row = self._pending_row, None
            return row
        return self.raw.fetchone()

    def fetchall(self):
        rows = []
        if self._pending_row is not None:
            rows.append(self._pending_row)
            self._pending_row = None
        rows.extend(self.raw.fetchall())
        return rows

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self.raw.rowcount

    @property
    def description(self):
        return self.raw.description

    def close(self):
        self.raw.close()

    def __getattr__(self, name):
        return getattr(self.raw, name)


class PostgresConnection:
    def __init__(self, dsn):
        self.raw = psycopg.connect(dsn, sslmode="require", connect_timeout=10,
                                   row_factory=_hybrid_row_factory)
        self._row_factory = None

    @property
    def row_factory(self):
        return self._row_factory

    @row_factory.setter
    def row_factory(self, value):
        # Route modules assign sqlite3.Row; PostgreSQL already returns HybridRow.
        self._row_factory = value

    def cursor(self, *args, **kwargs):
        return PostgresCursor(self)

    def execute(self, sql, params=()):
        return self.cursor().execute(sql, params)

    def executemany(self, sql, params_seq):
        return self.cursor().executemany(sql, params_seq)

    def commit(self):
        return self.raw.commit()

    def rollback(self):
        return self.raw.rollback()

    def close(self):
        return self.raw.close()

    def __getattr__(self, name):
        return getattr(self.raw, name)
