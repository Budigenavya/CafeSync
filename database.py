import os
import sqlite3

from config import DATABASE

# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():

    db_dir = os.path.dirname(DATABASE)

    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    print("Database:", os.path.abspath(DATABASE))

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


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

        print("✓ Users Table Created")

        # ==========================================================
        # CATEGORIES
        # ==========================================================

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS categories(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT UNIQUE NOT NULL

        )

        """)

        print("✓ Categories Table Created")

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

            barcode TEXT UNIQUE,

            image TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(category_id)

            REFERENCES categories(id)

        )

        """)

        print("✓ Products Table Created")
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

        print("✓ Customers Table Created")

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

        print("✓ Tables Table Created")

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

        print("✓ Orders Table Created")

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

        print("✓ Order Items Table Created")
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

        print("✓ Employees Table Created")

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

        print("✓ Settings Table Created")

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

        print("✓ Inventory Logs Table Created")

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

        print("✓ Payments Table Created")

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

        print("✓ Expenses Table Created")
        # ==========================================================
        # DEFAULT ADMIN
        # ==========================================================

        cursor.execute("SELECT COUNT(*) FROM users")

        if cursor.fetchone()[0] == 0:

            cursor.execute("""

            INSERT INTO users(

                full_name,

                username,

                password,

                role

            )

            VALUES(

                'Administrator',

                'admin',

                'admin123',

                'Admin'

            )

            """)

            print("✓ Default Admin Created")

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

            print("✓ Default Settings Added")

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

            print("✓ Default Categories Added")

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

            print("✓ Cafe Tables Added")

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

            print("✓ Sample Products Added")
        # ==========================================================
        # COMMIT CHANGES
        # ==========================================================

        conn.commit()

        print("=" * 50)
        print("✓ CafeSync Database Created Successfully")
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