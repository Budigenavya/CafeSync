import os
import sqlite3
import shutil
import psycopg

from werkzeug.security import generate_password_hash

from config import DATABASE, DATABASE_URL, USE_POSTGRES
from db_compat import PostgresConnection

# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():

    print(
        f"[DB DIAGNOSTIC] USE_POSTGRES={USE_POSTGRES}, "
        f"DATABASE_URL_CONFIGURED={bool(DATABASE_URL)}"
    )

    if USE_POSTGRES:
        connection = PostgresConnection(DATABASE_URL)
        print(
            f"[DB DIAGNOSTIC] Connection type="
            f"{type(connection).__name__}"
        )
        return connection

    db_dir = os.path.dirname(DATABASE)

    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # If a persistent mount is configured for the first time, preserve the
    # existing app-local database by seeding the mount once. Never overwrite
    # a database already on the persistent disk.
    legacy_database = os.path.join(os.path.dirname(__file__), "database.db")
    if not os.path.exists(DATABASE) and os.path.abspath(DATABASE) != os.path.abspath(legacy_database) and os.path.exists(legacy_database):
        shutil.copy2(legacy_database, DATABASE)

    print("Database:", os.path.abspath(DATABASE))

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    print("[DB DIAGNOSTIC] Connection type=SQLite")
    return conn
def get_postgres_connection():
    """
    Open a separate PostgreSQL connection.
    This function does not change the existing SQLite connection.
    """

    if not USE_POSTGRES:
        raise RuntimeError(
            "PostgreSQL mode is disabled. "
            "Set CAFESYNC_USE_POSTGRES=true to enable it."
        )

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    return PostgresConnection(DATABASE_URL)


def ensure_product_stock_unlimited_column():
    """Apply the small additive migration needed for optional product stock tracking."""
    conn = get_connection()
    try:
        if USE_POSTGRES:
            # IF NOT EXISTS makes this safe when Gunicorn workers start together.
            conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS stock_unlimited INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        else:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()}
            if "stock_unlimited" not in columns:
                conn.execute("ALTER TABLE products ADD COLUMN stock_unlimited INTEGER NOT NULL DEFAULT 0")
                conn.commit()
    finally:
        conn.close()


# ==========================================================
# CREATE TABLES
# ==========================================================

def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    try:

        # ==========================================================
        # USERS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS users(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL

        )

        """)

        print("[OK] Users Table Created")

        user_columns = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
        if "created_at" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
            cursor.execute("UPDATE users SET created_at=CURRENT_TIMESTAMP WHERE created_at IS NULL")
        if "is_active" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

        # ==========================================================
        # CATEGORIES
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS categories(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT UNIQUE NOT NULL

        )

        """)

        print("[OK] Categories Table Created")

        # ==========================================================
        # PRODUCTS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS products(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            category_id INTEGER,

            name TEXT NOT NULL,

            price REAL NOT NULL,

            stock INTEGER DEFAULT 0,
            stock_unlimited INTEGER NOT NULL DEFAULT 0,

            is_available INTEGER NOT NULL DEFAULT 1,

            barcode TEXT UNIQUE,

            image TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(category_id)

            REFERENCES categories(id)

        )

        """)

        print("[OK] Products Table Created")

        product_columns = {
            row[1]
            for row in cursor.execute("PRAGMA table_info(products)").fetchall()
        }
        if "stock_unlimited" not in product_columns:
            cursor.execute("ALTER TABLE products ADD COLUMN stock_unlimited INTEGER NOT NULL DEFAULT 0")
            product_columns.add("stock_unlimited")
        if "is_available" not in product_columns:
            cursor.execute("ALTER TABLE products ADD COLUMN is_available INTEGER NOT NULL DEFAULT 1")
        if "image" not in product_columns:
            cursor.execute("ALTER TABLE products ADD COLUMN image TEXT")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_addons(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0,
                is_available INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS ingredients(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                unit TEXT NOT NULL DEFAULT 'g',
                current_stock REAL NOT NULL DEFAULT 0 CHECK(current_stock >= 0),
                low_stock_threshold REAL NOT NULL DEFAULT 0 CHECK(low_stock_threshold >= 0),
                unit_cost REAL NOT NULL DEFAULT 0 CHECK(unit_cost >= 0),
                active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS recipes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL CHECK(quantity > 0),
                UNIQUE(product_id, ingredient_id),
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
            );
            CREATE TABLE IF NOT EXISTS ingredient_movements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                quantity_change REAL NOT NULL,
                movement_type TEXT NOT NULL,
                reference TEXT DEFAULT '',
                order_id INTEGER,
                notes TEXT DEFAULT '',
                actor TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY(order_id) REFERENCES orders(id)
            );
            CREATE TABLE IF NOT EXISTS suppliers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                phone TEXT DEFAULT '', email TEXT DEFAULT '', notes TEXT DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS stock_receipts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER,
                reference TEXT DEFAULT '',
                total_cost REAL NOT NULL DEFAULT 0,
                received_by TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
            );
            CREATE TABLE IF NOT EXISTS stock_receipt_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL CHECK(quantity > 0),
                unit_cost REAL NOT NULL DEFAULT 0,
                FOREIGN KEY(receipt_id) REFERENCES stock_receipts(id) ON DELETE CASCADE,
                FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
            );
            CREATE TABLE IF NOT EXISTS audit_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT DEFAULT '', action TEXT NOT NULL,
                entity_type TEXT NOT NULL, entity_id TEXT DEFAULT '',
                details TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS day_closings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_date TEXT NOT NULL UNIQUE,
                closed_by TEXT DEFAULT '',
                order_count INTEGER NOT NULL DEFAULT 0,
                gross_sales REAL NOT NULL DEFAULT 0,
                refunds REAL NOT NULL DEFAULT 0,
                payment_summary TEXT NOT NULL DEFAULT '{}',
                closed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # ==========================================================
        # CUSTOMERS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS customers(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            phone TEXT UNIQUE,

            email TEXT,

            address TEXT,

            points INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """)

        print("[OK] Customers Table Created")

        # ==========================================================
        # TABLES
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS tables(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            table_name TEXT UNIQUE NOT NULL,

            status TEXT DEFAULT 'Available'

        )

        """)

        print("[OK] Tables Table Created")
        table_columns = {row[1] for row in cursor.execute("PRAGMA table_info(tables)").fetchall()}
        if "capacity" not in table_columns:
            cursor.execute("ALTER TABLE tables ADD COLUMN capacity INTEGER NOT NULL DEFAULT 4")
        for column, definition in {
            "reservation_name": "TEXT NOT NULL DEFAULT ''",
            "reservation_phone": "TEXT NOT NULL DEFAULT ''",
            "reservation_guests": "INTEGER",
            "reserved_for": "TEXT",
            "reservation_notes": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in table_columns:
                cursor.execute(f"ALTER TABLE tables ADD COLUMN {column} {definition}")

        # ==========================================================
        # ORDERS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS orders(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            bill_no TEXT UNIQUE,

            table_id INTEGER,

            customer_id INTEGER,

            order_type TEXT,
            order_source TEXT DEFAULT 'Cafe',

            subtotal REAL DEFAULT 0,

            gst REAL DEFAULT 0,

            discount REAL DEFAULT 0,

            total REAL DEFAULT 0,

            payment_method TEXT,

            status TEXT DEFAULT 'Pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(table_id)
                REFERENCES tables(id),

            FOREIGN KEY(customer_id)
                REFERENCES customers(id)

        )

        """)

        print("[OK] Orders Table Created")

        order_columns = {
            row[1]
            for row in cursor.execute("PRAGMA table_info(orders)").fetchall()
        }
        if "chef_notes" not in order_columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN chef_notes TEXT DEFAULT ''")
        if "payment_status" not in order_columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'Pending'")
            cursor.execute("""
                UPDATE orders
                SET payment_status='Paid'
                WHERE payment_method IS NOT NULL
                  AND TRIM(payment_method)!=''
                  AND payment_method!='Pending'
            """)
        for column, definition in {
            "cancelled_at": "TIMESTAMP",
            "refund_reason": "TEXT DEFAULT ''",
            "refunded_at": "TIMESTAMP",
            "served_at": "TIMESTAMP",
            "split_details": "TEXT",
            "order_source": "TEXT DEFAULT 'Cafe'",
        }.items():
            if column not in order_columns:
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")
                order_columns.add(column)
        if "rider_id" not in order_columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN rider_id INTEGER")
            order_columns.add("rider_id")
        cursor.execute("""
            UPDATE orders
            SET status='Completed'
            WHERE COALESCE(order_source, 'Cafe')='Cafe'
              AND order_type IN ('Parcel', 'Take Away', 'Dine In')
              AND status IN ('Pending', 'Preparing', 'Ready', 'Served')
        """)

        # Delivery routes use the same normalized order/customer data as the
        # rest of the application. Riders are the one delivery-specific table.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS riders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                vehicle TEXT NOT NULL DEFAULT '',
                vehicle_number TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Available',
                current_location TEXT NOT NULL DEFAULT ''
            )
        """)
        if USE_POSTGRES:
            cursor.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema=current_schema()
                  AND table_name='orders'
                  AND constraint_name='orders_rider_id_fkey'
            """)
            if cursor.fetchone() is None:
                cursor.execute("""
                    ALTER TABLE orders
                    ADD CONSTRAINT orders_rider_id_fkey
                    FOREIGN KEY (rider_id) REFERENCES riders(id)
                """)

        # ==========================================================
        # ORDER ITEMS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS order_items(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL,

            price REAL NOT NULL,

            FOREIGN KEY(order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

            FOREIGN KEY(product_id)
                REFERENCES products(id)

        )

        """)

        print("[OK] Order Items Table Created")
        item_columns = {
            row[1]
            for row in cursor.execute("PRAGMA table_info(order_items)").fetchall()
        }
        if "chef_note" not in item_columns:
            cursor.execute("ALTER TABLE order_items ADD COLUMN chef_note TEXT DEFAULT ''")
        if "addons" not in item_columns:
            cursor.execute("ALTER TABLE order_items ADD COLUMN addons TEXT DEFAULT '[]'")
        # ==========================================================
        # EMPLOYEES
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS employees(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            phone TEXT UNIQUE,

            email TEXT,

            role TEXT,

            salary REAL DEFAULT 0,

            joining_date TEXT,

            status TEXT DEFAULT 'Active'

        )

        """)

        print("[OK] Employees Table Created")

        # ==========================================================
        # SETTINGS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS settings(

            id INTEGER PRIMARY KEY,

            cafe_name TEXT,

            address TEXT,

            phone TEXT,

            email TEXT,

            gst_number TEXT,

            tax_percentage REAL DEFAULT 5,

            currency TEXT DEFAULT '₹'

        )

        """)

        # Billing preferences are stored with the cafe settings so they are
        # shared by every POS session instead of being browser-local.
        settings_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(settings)").fetchall()
        }
        for column, definition in {
            "default_discount": "REAL NOT NULL DEFAULT 0",
            "maximum_discount": "REAL NOT NULL DEFAULT 30",
            "allow_manual_discount": "INTEGER NOT NULL DEFAULT 0",
            "show_gst_on_receipt": "INTEGER NOT NULL DEFAULT 1",
            "owner_name": "TEXT DEFAULT ''",
            "website": "TEXT DEFAULT ''",
            "working_days": "TEXT DEFAULT ''",
            "facebook": "TEXT DEFAULT ''",
            "instagram": "TEXT DEFAULT ''",
            "twitter": "TEXT DEFAULT ''",
            "whatsapp": "TEXT DEFAULT ''",
            "theme": "TEXT NOT NULL DEFAULT 'light'",
            "currency_symbol": "TEXT NOT NULL DEFAULT '₹'",
            "opening_time": "TEXT DEFAULT '09:00'",
            "closing_time": "TEXT DEFAULT '22:00'",
            "receipt_header": "TEXT DEFAULT ''",
            "receipt_footer": "TEXT DEFAULT ''",
            "dashboard_refresh": "INTEGER NOT NULL DEFAULT 30",
            "dashboard_chart_days": "INTEGER NOT NULL DEFAULT 7",
            "low_stock_alert": "INTEGER NOT NULL DEFAULT 1",
            "order_notification": "INTEGER NOT NULL DEFAULT 1",
            "default_payment_method": "TEXT NOT NULL DEFAULT 'Cash'",
            "default_order_type": "TEXT NOT NULL DEFAULT 'Take Away'",
        }.items():
            if column not in settings_columns:
                cursor.execute(f"ALTER TABLE settings ADD COLUMN {column} {definition}")

        print("[OK] Settings Table Created")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS held_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT DEFAULT '',
            customer_id INTEGER,
            table_id INTEGER,
                order_type TEXT DEFAULT 'Dine In',
                payment_method TEXT DEFAULT 'Cash',
                is_paid INTEGER NOT NULL DEFAULT 0,
                items TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        held_order_columns = {row[1] for row in cursor.execute("PRAGMA table_info(held_orders)").fetchall()}
        if "customer_id" not in held_order_columns:
            cursor.execute("ALTER TABLE held_orders ADD COLUMN customer_id INTEGER")

        # ==========================================================
        # INVENTORY LOGS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS inventory_logs(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id INTEGER,

            quantity INTEGER,

            action TEXT,

            remarks TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(product_id)
                REFERENCES products(id)

        )

        """)

        # Older deployments created inventory_logs from models.py with legacy
        # operation/quantity_changed columns, while billing writes action and
        # quantity. Keep both schema generations compatible at startup.
        inventory_log_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(inventory_logs)").fetchall()
        }
        for column, definition in {
            "previous_stock": "INTEGER",
            "new_stock": "INTEGER",
            "quantity_changed": "INTEGER",
            "operation": "TEXT",
            "quantity": "INTEGER",
            "action": "TEXT",
            "remarks": "TEXT",
            "created_at": "TIMESTAMP",
        }.items():
            if column not in inventory_log_columns:
                cursor.execute(f"ALTER TABLE inventory_logs ADD COLUMN {column} {definition}")
                inventory_log_columns.add(column)
        cursor.execute("UPDATE inventory_logs SET action=operation WHERE action IS NULL AND operation IS NOT NULL")
        cursor.execute("UPDATE inventory_logs SET operation=action WHERE operation IS NULL AND action IS NOT NULL")
        cursor.execute("UPDATE inventory_logs SET quantity=quantity_changed WHERE quantity IS NULL AND quantity_changed IS NOT NULL")
        cursor.execute("UPDATE inventory_logs SET quantity_changed=quantity WHERE quantity_changed IS NULL AND quantity IS NOT NULL")
        cursor.execute("UPDATE inventory_logs SET created_at=CURRENT_TIMESTAMP WHERE created_at IS NULL")

        print("[OK] Inventory Logs Table Created")

        # ==========================================================
        # PAYMENTS
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS payments(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id INTEGER,

            payment_type TEXT,

            amount REAL,

            payment_status TEXT DEFAULT 'Paid',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(order_id)
                REFERENCES orders(id)

        )

        """)

        payment_columns = {row[1] for row in cursor.execute("PRAGMA table_info(payments)").fetchall()}
        if "split_person" not in payment_columns:
            cursor.execute("ALTER TABLE payments ADD COLUMN split_person TEXT")

        print("[OK] Payments Table Created")

        # ==========================================================
        # EXPENSES
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS expenses(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            category TEXT,

            amount REAL NOT NULL,

            description TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """)

        print("[OK] Expenses Table Created")
        # ==========================================================
        # DEFAULT ADMIN
        # ==========================================================

        cursor.execute("SELECT COUNT(*) FROM users")

        if cursor.fetchone()[0] == 0:

            admin_password = os.environ.get("CAFESYNC_ADMIN_PASSWORD", "").strip()
            if USE_POSTGRES and not admin_password:
                raise RuntimeError(
                    "Set CAFESYNC_ADMIN_PASSWORD before initializing an empty PostgreSQL database."
                )
            if not admin_password:
                admin_password = "admin123"

            cursor.execute("""

            INSERT INTO users(

                full_name,

                username,

                password,

                role

            )

            VALUES(?, ?, ?, 'Admin')

            """, ("Administrator", "admin", generate_password_hash(admin_password)))

            print("[OK] Default Admin Created")

        # ==========================================================
        # DEFAULT SETTINGS
        # ==========================================================

        cursor.execute("SELECT COUNT(*) FROM settings")

        if cursor.fetchone()[0] == 0:

            cursor.execute("""

            INSERT INTO settings(

                id,

                cafe_name,

                address,

                phone,

                email,

                gst_number,

                tax_percentage,

                currency

            )

            VALUES(

                1,

                'CafeSync',

                'Your Address',

                '9876543210',

                'cafesync@gmail.com',

                'GST123456789',

                5,

                '₹'

            )

            """)

            print("[OK] Default Settings Added")

        # ==========================================================
        # DEFAULT CATEGORIES
        # ==========================================================

        cursor.execute("SELECT COUNT(*) FROM categories")

        if cursor.fetchone()[0] == 0:

            categories = [

                ("Coffee",),

                ("Tea",),

                ("Pizza",),

                ("Burger",),

                ("Pasta",),

                ("Sandwich",),

                ("Snacks",),

                ("Cold Drinks",),

                ("Desserts",),

                ("Ice Cream",)

            ]

            cursor.executemany(

                "INSERT INTO categories(name) VALUES(?)",

                categories

            )

            print("[OK] Default Categories Added")

        # ==========================================================
        # DEFAULT TABLES
        # ==========================================================

        cursor.execute("SELECT COUNT(*) FROM tables")

        if cursor.fetchone()[0] == 0:

            for i in range(1, 21):

                cursor.execute(

                    """

                    INSERT INTO tables(

                        table_name,

                        status

                    )

                    VALUES(

                        ?,?

                    )

                    """,

                    (

                        f"Table {i}",

                        "Available"

                    )

                )

            print("[OK] Cafe Tables Added")

        # ==========================================================
        # SAMPLE PRODUCTS
        # ==========================================================

        cursor.execute("SELECT COUNT(*) FROM products")

        if cursor.fetchone()[0] == 0:

            products = [

                (1,"Espresso",120,100,"100001"),

                (1,"Cappuccino",180,100,"100002"),

                (1,"Latte",190,100,"100003"),

                (2,"Green Tea",90,100,"100004"),

                (3,"Veg Pizza",250,50,"100005"),

                (4,"Cheese Burger",180,50,"100006"),

                (5,"White Pasta",220,50,"100007"),

                (7,"French Fries",120,100,"100008"),

                (8,"Coke",60,200,"100009"),

                (10,"Vanilla Ice Cream",90,100,"100010")

            ]

            cursor.executemany(

                """

                INSERT INTO products(

                    category_id,

                    name,

                    price,

                    stock,

                    barcode

                )

                VALUES(

                    ?,?,?,?,?

                )

                """,

                products

            )

            print("[OK] Sample Products Added")

        if USE_POSTGRES:
            cursor.execute("""
                SELECT table_name FROM information_schema.columns
                WHERE table_schema=current_schema() AND column_name='id'
                  AND (left(column_default, 8)='nextval(' OR is_identity='YES')
            """)
            serial_tables = [row["table_name"] for row in cursor.fetchall()]
            for table_name in serial_tables:
                quoted_table = '"' + table_name.replace('"', '""') + '"'
                cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence(%s, 'id'),
                                  GREATEST(COALESCE(MAX(id), 1), 1), COUNT(*) > 0)
                    FROM {quoted_table}
                """, (table_name,))

            cursor.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema=current_schema()
                  AND table_name='ingredient_movements'
                  AND constraint_name='ingredient_movements_order_id_fkey'
            """)
            if cursor.fetchone() is None:
                cursor.execute("""
                    ALTER TABLE ingredient_movements
                    ADD CONSTRAINT ingredient_movements_order_id_fkey
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                """)
        # ==========================================================
        # COMMIT CHANGES
        # ==========================================================

        conn.commit()

        print("=" * 50)
        print("[OK] CafeSync Database Created Successfully")
        print("=" * 50)

    except Exception as e:

        conn.rollback()

        print("=" * 50)
        print("DATABASE ERROR")
        print("=" * 50)
        print(e)

        raise

    finally:

        conn.close()


# ==========================================================
# RESET DATABASE
# ==========================================================

def reset_database():

    if USE_POSTGRES:
        raise RuntimeError("reset_database is a SQLite-only development utility.")

    if os.path.exists(DATABASE):

        os.remove(DATABASE)

        print("Old Database Deleted")

    create_tables()


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("=" * 50)
    print("CafeSync Database Initialization")
    print("=" * 50)

    create_tables()

    print("Database Ready")
