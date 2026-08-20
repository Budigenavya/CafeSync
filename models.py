"""
==========================================================
                CafeSync POS System
                    models.py
                    PART 1
        DATABASE CONNECTION & CORE TABLES
==========================================================
"""

import sqlite3
from datetime import datetime

DATABASE = "database.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==========================================================
# EXECUTE QUERY
# ==========================================================

def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query, params)

    conn.commit()

    last_id = cursor.lastrowid

    conn.close()

    return last_id


# ==========================================================
# FETCH ONE
# ==========================================================

def fetch_one(query, params=()):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(query, params)

    row = cursor.fetchone()

    conn.close()

    return row


# ==========================================================
# FETCH ALL
# ==========================================================

def fetch_all(query, params=()):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================================
# CREATE DATABASE TABLES
# ==========================================================

def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    # ======================================================
    # USERS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        full_name TEXT,

        email TEXT UNIQUE,

        phone TEXT,

        role TEXT DEFAULT 'Cashier',

        status TEXT DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        last_login TIMESTAMP

    )

    """)
# ==========================================================
# RESET DATABASE
# ==========================================================

def reset_database():

    conn = get_connection()

    cursor = conn.cursor()

    tables = [

        "order_items",
        "orders",
        "payments",
        "inventory_logs",
        "customer_reviews",
        "daily_reports",
        "sales_summary",
        "attendance",
        "leave_requests",
        "payroll",
        "employee_performance",
        "employee_rewards",
        "employee_training",
        "notifications",
        "audit_logs"

    ]

    for table in tables:

        cursor.execute(f"DELETE FROM {table}")

    conn.commit()

    conn.close()


# ==========================================================
# DATABASE STATUS
# ==========================================================

    def database_status():

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

        SELECT COUNT(*)

        FROM products

        """)

        products = cursor.fetchone()[0]

        cursor.execute("""

        SELECT COUNT(*)

        FROM customers

        """)

        customers = cursor.fetchone()[0]

        cursor.execute("""

        SELECT COUNT(*)

        FROM employees

        """)

        employees = cursor.fetchone()[0]

        cursor.execute("""

        SELECT COUNT(*)

        FROM orders

        """)

        orders = cursor.fetchone()[0]

        conn.close()

        return {

            "products": products,

            "customers": customers,

            "employees": employees,

            "orders": orders

        }


    # ======================================================
    # CATEGORIES
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS categories(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT UNIQUE NOT NULL,

        description TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # PRODUCTS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS products(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        category_id INTEGER,

        name TEXT NOT NULL,

        description TEXT,

        barcode TEXT UNIQUE,

        price REAL NOT NULL,

        cost_price REAL DEFAULT 0,

        stock INTEGER DEFAULT 0,

        min_stock INTEGER DEFAULT 10,

        unit TEXT DEFAULT 'Piece',

        image TEXT,

        status TEXT DEFAULT 'Available',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(category_id)

        REFERENCES categories(id)

        ON DELETE SET NULL

    )

    """)

    # ======================================================
    # DEFAULT ADMIN
    # ======================================================

    cursor.execute("""

    INSERT OR IGNORE INTO users(

        id,

        username,

        password,

        full_name,

        role

    )

    VALUES(

        1,

        'admin',

        'admin123',

        'Administrator',

        'Admin'

    )

    """)

    # ======================================================
    # DEFAULT CATEGORIES
    # ======================================================

    default_categories = [

        ("Coffee",),

        ("Tea",),

        ("Pizza",),

        ("Burger",),

        ("Pasta",),

        ("Dessert",),

        ("Cold Drinks",),

        ("Snacks",)

    ]

    cursor.executemany("""

    INSERT OR IGNORE INTO categories(name)

    VALUES(?)

    """, default_categories)

    conn.commit()

    conn.close()


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

if __name__ == "__main__":

    create_tables()

    print("Database initialized successfully.")
    # ======================================================
    # CUSTOMERS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS customers(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        phone TEXT UNIQUE,

        email TEXT,

        address TEXT,

        loyalty_points INTEGER DEFAULT 0,

        total_orders INTEGER DEFAULT 0,

        total_spent REAL DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # CAFE TABLES
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS cafe_tables(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        table_name TEXT UNIQUE NOT NULL,

        capacity INTEGER DEFAULT 4,

        status TEXT DEFAULT 'Available',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # ORDERS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS orders(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER,

        table_id INTEGER,

        order_type TEXT DEFAULT 'Dine-In',

        subtotal REAL DEFAULT 0,

        discount REAL DEFAULT 0,

        gst REAL DEFAULT 0,

        total REAL DEFAULT 0,

        payment_status TEXT DEFAULT 'Pending',

        order_status TEXT DEFAULT 'Pending',

        payment_method TEXT,

        notes TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(customer_id)

        REFERENCES customers(id)

        ON DELETE SET NULL,

        FOREIGN KEY(table_id)

        REFERENCES cafe_tables(id)

        ON DELETE SET NULL

    )

    """)

    # ======================================================
    # ORDER ITEMS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS order_items(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        order_id INTEGER NOT NULL,

        product_id INTEGER NOT NULL,

        quantity INTEGER NOT NULL,

        price REAL NOT NULL,

        total REAL NOT NULL,

        FOREIGN KEY(order_id)

        REFERENCES orders(id)

        ON DELETE CASCADE,

        FOREIGN KEY(product_id)

        REFERENCES products(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # DEFAULT CAFE TABLES
    # ======================================================

    default_tables = [

        ("Table 1",4),

        ("Table 2",4),

        ("Table 3",2),

        ("Table 4",6),

        ("Table 5",4),

        ("Table 6",8),

        ("Take Away",0)

    ]

    cursor.executemany("""

    INSERT OR IGNORE INTO cafe_tables(

        table_name,

        capacity

    )

    VALUES(?,?)

    """, default_tables)
    # ======================================================
    # EMPLOYEES
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS employees(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id TEXT UNIQUE,

        name TEXT NOT NULL,

        designation TEXT NOT NULL,

        role TEXT DEFAULT 'Staff',

        phone TEXT UNIQUE,

        email TEXT UNIQUE,

        address TEXT,

        gender TEXT,

        dob DATE,

        joining_date DATE,

        shift TEXT DEFAULT 'Morning',

        salary REAL DEFAULT 0,

        photo TEXT,

        status TEXT DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # ATTENDANCE
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS attendance(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER NOT NULL,

        attendance_date DATE NOT NULL,

        check_in TIME,

        check_out TIME,

        working_hours REAL DEFAULT 0,

        status TEXT DEFAULT 'Present',

        remarks TEXT,

        FOREIGN KEY(employee_id)

        REFERENCES employees(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # LEAVE MANAGEMENT
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS leave_requests(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER NOT NULL,

        from_date DATE,

        to_date DATE,

        leave_type TEXT,

        reason TEXT,

        status TEXT DEFAULT 'Pending',

        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(employee_id)

        REFERENCES employees(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # PAYROLL
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS payroll(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER NOT NULL,

        salary_month TEXT,

        basic_salary REAL DEFAULT 0,

        bonus REAL DEFAULT 0,

        overtime REAL DEFAULT 0,

        deductions REAL DEFAULT 0,

        net_salary REAL DEFAULT 0,

        payment_status TEXT DEFAULT 'Pending',

        payment_date DATE,

        FOREIGN KEY(employee_id)

        REFERENCES employees(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # EMPLOYEE PERFORMANCE
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS employee_performance(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER NOT NULL,

        review_month TEXT,

        orders_completed INTEGER DEFAULT 0,

        customer_rating REAL DEFAULT 0,

        performance_score REAL DEFAULT 0,

        remarks TEXT,

        FOREIGN KEY(employee_id)

        REFERENCES employees(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # EMPLOYEE REWARDS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS employee_rewards(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER NOT NULL,

        reward_name TEXT,

        reward_description TEXT,

        reward_date DATE,

        FOREIGN KEY(employee_id)

        REFERENCES employees(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # EMPLOYEE TRAINING
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS employee_training(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER NOT NULL,

        course_name TEXT,

        trainer TEXT,

        completion_date DATE,

        certificate TEXT,

        status TEXT DEFAULT 'Assigned',

        FOREIGN KEY(employee_id)

        REFERENCES employees(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # DEFAULT EMPLOYEES
    # ======================================================

    default_employees = [

        (

            "EMP001",

            "Admin User",

            "Manager",

            "Admin",

            "9999999999",

            "admin@cafesync.com",

            "Morning",

            50000

        ),

        (

            "EMP002",

            "Cashier",

            "Cashier",

            "Cashier",

            "8888888888",

            "cashier@cafesync.com",

            "Morning",

            25000

        ),

        (

            "EMP003",

            "Kitchen Staff",

            "Chef",

            "Kitchen",

            "7777777777",

            "chef@cafesync.com",

            "Evening",

            28000

        )

    ]

    cursor.executemany("""

    INSERT OR IGNORE INTO employees(

        employee_id,

        name,

        designation,

        role,

        phone,

        email,

        shift,

        salary

    )

    VALUES(

        ?,?,?,?,?,?,?,?

    )

    """, default_employees)
    # ======================================================
    # PAYMENTS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS payments(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        order_id INTEGER NOT NULL,

        transaction_id TEXT UNIQUE,

        payment_method TEXT NOT NULL,

        amount REAL NOT NULL,

        payment_status TEXT DEFAULT 'Success',

        payment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        remarks TEXT,

        FOREIGN KEY(order_id)

        REFERENCES orders(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # NOTIFICATIONS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS notifications(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT NOT NULL,

        message TEXT NOT NULL,

        notification_type TEXT,

        is_read INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # DAILY REPORTS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS daily_reports(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        report_date DATE UNIQUE,

        total_orders INTEGER DEFAULT 0,

        total_sales REAL DEFAULT 0,

        total_customers INTEGER DEFAULT 0,

        total_items INTEGER DEFAULT 0,

        total_discount REAL DEFAULT 0,

        total_tax REAL DEFAULT 0,

        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # AUDIT LOGS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS audit_logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        action TEXT,

        description TEXT,

        ip_address TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE SET NULL

    )

    """)

    # ======================================================
    # CUSTOMER REVIEWS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS customer_reviews(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER,

        order_id INTEGER,

        rating INTEGER,

        review TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(customer_id)

        REFERENCES customers(id)

        ON DELETE SET NULL,

        FOREIGN KEY(order_id)

        REFERENCES orders(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # INVENTORY LOGS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS inventory_logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        product_id INTEGER,

        previous_stock INTEGER,

        new_stock INTEGER,

        quantity_changed INTEGER,

        operation TEXT,

        remarks TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(product_id)

        REFERENCES products(id)

        ON DELETE CASCADE

    )

    """)

    # ======================================================
    # SALES SUMMARY
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS sales_summary(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        sales_date DATE UNIQUE,

        gross_sales REAL DEFAULT 0,

        net_sales REAL DEFAULT 0,

        tax_amount REAL DEFAULT 0,

        discount_amount REAL DEFAULT 0,

        total_orders INTEGER DEFAULT 0,

        average_order REAL DEFAULT 0

    )

    """)

    # ======================================================
    # COUPONS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS coupons(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        coupon_code TEXT UNIQUE,

        discount_type TEXT,

        discount_value REAL,

        minimum_amount REAL,

        expiry_date DATE,

        status TEXT DEFAULT 'Active'

    )

    """)

    # ======================================================
    # SUPPLIERS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS suppliers(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        supplier_name TEXT NOT NULL,

        contact_person TEXT,

        phone TEXT,

        email TEXT,

        address TEXT,

        gst_number TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # PURCHASES
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS purchases(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        supplier_id INTEGER,

        invoice_number TEXT,

        total_amount REAL,

        purchase_date DATE,

        payment_status TEXT DEFAULT 'Pending',

        remarks TEXT,

        FOREIGN KEY(supplier_id)

        REFERENCES suppliers(id)

        ON DELETE SET NULL

    )

    """)

    # ======================================================
    # PURCHASE ITEMS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS purchase_items(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        purchase_id INTEGER,

        product_id INTEGER,

        quantity INTEGER,

        cost_price REAL,

        total REAL,

        FOREIGN KEY(purchase_id)

        REFERENCES purchases(id)

        ON DELETE CASCADE,

        FOREIGN KEY(product_id)

        REFERENCES products(id)

        ON DELETE CASCADE

    )

    """)
    # ======================================================
    # SETTINGS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS settings(

        id INTEGER PRIMARY KEY CHECK(id=1),

        cafe_name TEXT DEFAULT 'CafeSync',

        owner_name TEXT,

        address TEXT,

        phone TEXT,

        email TEXT,

        gst_number TEXT,

        tax_percentage REAL DEFAULT 5,

        currency TEXT DEFAULT 'INR',

        timezone TEXT DEFAULT 'Asia/Kolkata',

        logo TEXT,

        invoice_prefix TEXT DEFAULT 'INV',

        invoice_footer TEXT DEFAULT 'Thank You! Visit Again.',

        printer_name TEXT,

        smtp_server TEXT,

        smtp_port INTEGER,

        sender_email TEXT,

        sender_password TEXT,

        swiggy_api_key TEXT,

        zomato_api_key TEXT,

        razorpay_key TEXT,

        stripe_key TEXT,

        enable_email_notifications INTEGER DEFAULT 1,

        enable_sms_notifications INTEGER DEFAULT 0,

        enable_desktop_notifications INTEGER DEFAULT 1,

        enable_low_stock_alert INTEGER DEFAULT 1,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # BACKUPS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS backups(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        backup_name TEXT,

        backup_path TEXT,

        backup_size TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # API TOKENS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS api_tokens(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        service_name TEXT UNIQUE,

        api_key TEXT,

        api_secret TEXT,

        status TEXT DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # SYSTEM LOGS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS system_logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        log_level TEXT,

        module TEXT,

        message TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # DEFAULT SETTINGS
    # ======================================================

    cursor.execute("""

    INSERT OR IGNORE INTO settings(

        id,

        cafe_name,

        owner_name,

        address,

        phone,

        email,

        gst_number,

        tax_percentage,

        currency,

        timezone

    )

    VALUES(

        1,

        'CafeSync',

        'Administrator',

        'Your Address',

        '9999999999',

        'admin@cafesync.com',

        'GST123456789',

        5,

        'INR',

        'Asia/Kolkata'

    )

    """)
    if __name__ == "__main__":

        create_tables()

        print("=" * 50)
        print(" CafeSync Database Initialized Successfully ")
        print("=" * 50)

        status = database_status()

        print(f"Products   : {status['products']}")
        print(f"Customers  : {status['customers']}")
        print(f"Employees  : {status['employees']}")
        print(f"Orders     : {status['orders']}")

        print("=" * 50)