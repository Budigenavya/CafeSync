"""
==========================================================
                CafeSync POS
                dashboard.py
                PART 1
        DASHBOARD SUMMARY & STATISTICS
==========================================================
"""

from flask import Blueprint, jsonify, request, render_template
from models import fetch_one
from database import get_connection
from routes.auth import login_required

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ==========================================================
# DASHBOARD SUMMARY
# ==========================================================

@dashboard_bp.route(
    "/dashboard/summary",
    methods=["GET"]
)
def dashboard_summary():

    total_sales = fetch_one("""

        SELECT

            IFNULL(

                SUM(total),

                0

            ) AS total

        FROM orders

        WHERE payment_status='Paid'

    """)

    total_orders = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM orders

    """)

    total_products = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM products

    """)

    total_categories = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM categories

    """)

    total_customers = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM customers

    """)

    total_employees = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM employees

    """)

    low_stock = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM products

        WHERE stock<=min_stock

    """)

    inventory_value = fetch_one("""

        SELECT

            IFNULL(

                SUM(stock*cost_price),

                0

            ) AS total

        FROM products

    """)

    return jsonify({

        "total_sales":
            total_sales["total"],

        "total_orders":
            total_orders["total"],

        "total_products":
            total_products["total"],

        "total_categories":
            total_categories["total"],

        "total_customers":
            total_customers["total"],

        "total_employees":
            total_employees["total"],

        "low_stock":
            low_stock["total"],

        "inventory_value":
            inventory_value["total"]

    })


# ==========================================================
# SALES CARD
# ==========================================================

@dashboard_bp.route(
    "/dashboard/sales-card",
    methods=["GET"]
)
def sales_card():

    result = fetch_one("""

        SELECT

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS sales,

            IFNULL(

                AVG(total),

                0

            ) AS average_bill,

            IFNULL(

                SUM(gst),

                0

            ) AS tax

        FROM orders

        WHERE payment_status='Paid'

    """)

    return jsonify(dict(result))


# ==========================================================
# INVENTORY CARD
# ==========================================================

@dashboard_bp.route(
    "/dashboard/inventory-card",
    methods=["GET"]
)
def inventory_card():

    result = fetch_one("""

        SELECT

            COUNT(*) AS products,

            IFNULL(

                SUM(stock),

                0

            ) AS stock,

            IFNULL(

                SUM(

                    stock*cost_price

                ),

                0

            ) AS value

        FROM products

    """)

    return jsonify(dict(result))


# ==========================================================
# CUSTOMER CARD
# ==========================================================

@dashboard_bp.route(
    "/dashboard/customer-card",
    methods=["GET"]
)
def customer_card():

    result = fetch_one("""

        SELECT

            COUNT(*) AS customers,

            IFNULL(

                SUM(total_orders),

                0

            ) AS orders,

            IFNULL(

                SUM(total_spent),

                0

            ) AS revenue

        FROM customers

    """)

    return jsonify(dict(result))


# ==========================================================
# EMPLOYEE CARD
# ==========================================================

@dashboard_bp.route(
    "/dashboard/employee-card",
    methods=["GET"]
)
def employee_card():

    result = fetch_one("""

        SELECT

            COUNT(*) AS employees,

            IFNULL(

                SUM(salary),

                0

            ) AS payroll

        FROM employees

        WHERE status='Active'

    """)

    return jsonify(dict(result))
# ==========================================================
# TODAY SALES
# ==========================================================

@dashboard_bp.route(
    "/dashboard/today-sales",
    methods=["GET"]
)
def today_sales():

    result = fetch_one("""

        SELECT

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS sales,

            IFNULL(

                AVG(total),

                0

            ) AS average_bill

        FROM orders

        WHERE DATE(created_at)=DATE('now','localtime')

        AND payment_status='Paid'

    """)

    return jsonify(dict(result))


# ==========================================================
# WEEK SALES
# ==========================================================

@dashboard_bp.route(
    "/dashboard/week-sales",
    methods=["GET"]
)
def week_sales():

    result = fetch_one("""

        SELECT

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS sales

        FROM orders

        WHERE DATE(created_at)>=DATE('now','-6 day')

        AND payment_status='Paid'

    """)

    return jsonify(dict(result))


# ==========================================================
# MONTH SALES
# ==========================================================

@dashboard_bp.route(
    "/dashboard/month-sales",
    methods=["GET"]
)
def month_sales():

    result = fetch_one("""

        SELECT

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS sales

        FROM orders

        WHERE strftime('%Y-%m',created_at)=

              strftime('%Y-%m','now')

        AND payment_status='Paid'

    """)

    return jsonify(dict(result))


# ==========================================================
# RECENT ORDERS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/recent-orders",
    methods=["GET"]
)
def recent_orders():

    rows = fetch_one("""
        SELECT COUNT(*) AS total
        FROM orders
    """)

    recent = fetch_all("""

        SELECT

            id,

            total,

            payment_method,

            payment_status,

            order_status,

            created_at

        FROM orders

        ORDER BY created_at DESC

        LIMIT 10

    """)

    return jsonify({

        "total_orders":

            rows["total"],

        "recent_orders":[

            dict(r)

            for r in recent

        ]

    })


# ==========================================================
# RECENT CUSTOMERS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/recent-customers",
    methods=["GET"]
)
def recent_customers():

    rows = fetch_all("""

        SELECT

            id,

            name,

            phone,

            total_orders,

            total_spent,

            created_at

        FROM customers

        ORDER BY created_at DESC

        LIMIT 10

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# LOW STOCK PRODUCTS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/low-stock",
    methods=["GET"]
)
def dashboard_low_stock():

    rows = fetch_all("""

        SELECT

            id,

            name,

            stock,

            min_stock,

            barcode,

            price

        FROM products

        WHERE stock<=min_stock

        ORDER BY stock ASC

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# TOP SELLING PRODUCTS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/top-products",
    methods=["GET"]
)
def dashboard_top_products():

    rows = fetch_all("""

        SELECT

            p.id,

            p.name,

            IFNULL(

                SUM(oi.quantity),

                0

            ) AS quantity_sold,

            IFNULL(

                SUM(oi.total),

                0

            ) AS revenue

        FROM products p

        LEFT JOIN order_items oi

        ON p.id=oi.product_id

        GROUP BY p.id

        ORDER BY quantity_sold DESC

        LIMIT 10

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])
# ==========================================================
# SALES TREND (LAST 7 DAYS)
# ==========================================================

@dashboard_bp.route(
    "/dashboard/sales-trend",
    methods=["GET"]
)
def sales_trend():

    rows = fetch_all("""

        SELECT

            DATE(created_at) AS sales_date,

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY DATE(created_at)

        ORDER BY DATE(created_at) DESC

        LIMIT 7

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])


# ==========================================================
# MONTHLY REVENUE
# ==========================================================

@dashboard_bp.route(
    "/dashboard/monthly-revenue",
    methods=["GET"]
)
def monthly_revenue():

    rows = fetch_all("""

        SELECT

            strftime('%Y-%m',created_at)

            AS month,

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY month

        ORDER BY month

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])


# ==========================================================
# PAYMENT METHOD STATISTICS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/payment-stats",
    methods=["GET"]
)
def payment_statistics():

    rows = fetch_all("""

        SELECT

            payment_method,

            COUNT(*) AS transactions,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY payment_method

        ORDER BY revenue DESC

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])


# ==========================================================
# CATEGORY SALES
# ==========================================================

@dashboard_bp.route(
    "/dashboard/category-sales",
    methods=["GET"]
)
def category_sales():

    rows = fetch_all("""

        SELECT

            c.name AS category,

            IFNULL(

                SUM(oi.quantity),

                0

            ) AS quantity,

            IFNULL(

                SUM(oi.total),

                0

            ) AS revenue

        FROM categories c

        LEFT JOIN products p

            ON c.id=p.category_id

        LEFT JOIN order_items oi

            ON p.id=oi.product_id

        GROUP BY c.id

        ORDER BY revenue DESC

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])


# ==========================================================
# SALES BY HOUR
# ==========================================================

@dashboard_bp.route(
    "/dashboard/hourly-sales",
    methods=["GET"]
)
def hourly_sales():

    rows = fetch_all("""

        SELECT

            strftime('%H',created_at)

            AS hour,

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY hour

        ORDER BY hour

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])


# ==========================================================
# ORDER STATUS STATISTICS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/order-status",
    methods=["GET"]
)
def order_status_statistics():

    rows = fetch_all("""

        SELECT

            order_status,

            COUNT(*) AS total

        FROM orders

        GROUP BY order_status

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])


# ==========================================================
# SALES BY DAY OF WEEK
# ==========================================================

@dashboard_bp.route(
    "/dashboard/weekday-sales",
    methods=["GET"]
)
def weekday_sales():

    rows = fetch_all("""

        SELECT

            CASE strftime('%w',created_at)

                WHEN '0' THEN 'Sunday'
                WHEN '1' THEN 'Monday'
                WHEN '2' THEN 'Tuesday'
                WHEN '3' THEN 'Wednesday'
                WHEN '4' THEN 'Thursday'
                WHEN '5' THEN 'Friday'
                WHEN '6' THEN 'Saturday'
            END AS day,

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY strftime('%w',created_at)

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])


# ==========================================================
# AVERAGE ORDER VALUE TREND
# ==========================================================

@dashboard_bp.route(
    "/dashboard/average-order-trend",
    methods=["GET"]
)
def average_order_trend():

    rows = fetch_all("""

        SELECT

            DATE(created_at)

            AS sales_date,

            IFNULL(

                AVG(total),

                0

            ) AS average_order

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY DATE(created_at)

        ORDER BY DATE(created_at) DESC

        LIMIT 7

    """)

    return jsonify([

        dict(row)

        for row in rows

    ])
# ==========================================================
# KITCHEN DASHBOARD
# ==========================================================

@dashboard_bp.route(
    "/dashboard/kitchen",
    methods=["GET"]
)
def kitchen_dashboard():

    result = fetch_one("""

        SELECT

            COUNT(*) AS total_orders,

            SUM(
                CASE
                    WHEN order_status='Pending'
                    THEN 1
                    ELSE 0
                END
            ) AS pending,

            SUM(
                CASE
                    WHEN order_status='Preparing'
                    THEN 1
                    ELSE 0
                END
            ) AS preparing,

            SUM(
                CASE
                    WHEN order_status='Ready'
                    THEN 1
                    ELSE 0
                END
            ) AS ready,

            SUM(
                CASE
                    WHEN order_status='Served'
                    THEN 1
                    ELSE 0
                END
            ) AS served

        FROM orders

    """)

    return jsonify(dict(result))


# ==========================================================
# EMPLOYEE DASHBOARD
# ==========================================================

@dashboard_bp.route(
    "/dashboard/employees",
    methods=["GET"]
)
def dashboard_employees():

    result = fetch_one("""

        SELECT

            COUNT(*) AS total,

            SUM(
                CASE
                    WHEN status='Active'
                    THEN 1
                    ELSE 0
                END
            ) AS active,

            SUM(
                CASE
                    WHEN status='Inactive'
                    THEN 1
                    ELSE 0
                END
            ) AS inactive,

            IFNULL(
                SUM(salary),
                0
            ) AS payroll

        FROM employees

    """)

    return jsonify(dict(result))


# ==========================================================
# CUSTOMER DASHBOARD
# ==========================================================

@dashboard_bp.route(
    "/dashboard/customers",
    methods=["GET"]
)
def dashboard_customers():

    result = fetch_one("""

        SELECT

            COUNT(*) AS total_customers,

            IFNULL(
                SUM(total_orders),
                0
            ) AS total_orders,

            IFNULL(
                SUM(total_spent),
                0
            ) AS total_spent,

            IFNULL(
                AVG(total_spent),
                0
            ) AS average_spent

        FROM customers

    """)

    return jsonify(dict(result))


# ==========================================================
# INVENTORY ALERTS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/inventory-alerts",
    methods=["GET"]
)
def inventory_alerts():

    rows = fetch_all("""

        SELECT

            id,

            name,

            stock,

            min_stock

        FROM products

        WHERE stock<=min_stock

        ORDER BY stock ASC

        LIMIT 20

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# RECENT NOTIFICATIONS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/notifications",
    methods=["GET"]
)
def dashboard_notifications():

    notifications = []

    low_stock = fetch_one("""

        SELECT COUNT(*)

        AS total

        FROM products

        WHERE stock<=min_stock

    """)

    pending_orders = fetch_one("""

        SELECT COUNT(*)

        AS total

        FROM orders

        WHERE order_status='Pending'

    """)

    if low_stock["total"] > 0:

        notifications.append({

            "type": "warning",

            "title": "Low Stock",

            "message":

            f"{low_stock['total']} products need restocking."

        })

    if pending_orders["total"] > 0:

        notifications.append({

            "type": "info",

            "title": "Pending Orders",

            "message":

            f"{pending_orders['total']} orders are pending."

        })

    return jsonify(notifications)


# ==========================================================
# BUSINESS PERFORMANCE
# ==========================================================

@dashboard_bp.route(
    "/dashboard/business-performance",
    methods=["GET"]
)
def business_performance():

    sales = fetch_one("""

        SELECT

            IFNULL(
                SUM(total),
                0
            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

    """)

    products = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM products

    """)

    customers = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM customers

    """)

    employees = fetch_one("""

        SELECT

            COUNT(*)

            AS total

        FROM employees

    """)

    return jsonify({

        "revenue":
            sales["revenue"],

        "products":
            products["total"],

        "customers":
            customers["total"],

        "employees":
            employees["total"]

    })


# ==========================================================
# DASHBOARD KPI
# ==========================================================

@dashboard_bp.route(
    "/dashboard/kpi",
    methods=["GET"]
)
def dashboard_kpi():

    result = fetch_one("""

        SELECT

            COUNT(*) AS orders,

            IFNULL(
                SUM(total),
                0
            ) AS sales,

            IFNULL(
                AVG(total),
                0
            ) AS avg_order

        FROM orders

        WHERE payment_status='Paid'

    """)

    return jsonify(dict(result))
# ==========================================================
# COMPLETE ANALYTICS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/analytics",
    methods=["GET"]
)
def dashboard_analytics():

    analytics = {

        "sales": fetch_one("""

            SELECT

                IFNULL(SUM(total),0)

                AS total_sales

            FROM orders

            WHERE payment_status='Paid'

        """)["total_sales"],

        "orders": fetch_one("""

            SELECT COUNT(*)

            AS total

            FROM orders

        """)["total"],

        "customers": fetch_one("""

            SELECT COUNT(*)

            AS total

            FROM customers

        """)["total"],

        "products": fetch_one("""

            SELECT COUNT(*)

            AS total

            FROM products

        """)["total"],

        "employees": fetch_one("""

            SELECT COUNT(*)

            AS total

            FROM employees

        """)["total"]

    }

    return jsonify(analytics)


# ==========================================================
# MONTHLY CHART
# ==========================================================

@dashboard_bp.route(
    "/dashboard/chart/monthly",
    methods=["GET"]
)
def monthly_chart():

    rows = fetch_all("""

        SELECT

            strftime('%m',created_at)

            AS month,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY month

        ORDER BY month

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# YEARLY CHART
# ==========================================================

@dashboard_bp.route(
    "/dashboard/chart/yearly",
    methods=["GET"]
)
def yearly_chart():

    rows = fetch_all("""

        SELECT

            strftime('%Y',created_at)

            AS year,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY year

        ORDER BY year

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# DATABASE STATUS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/database",
    methods=["GET"]
)
def database_status():

    tables = {

        "products": fetch_one(

            "SELECT COUNT(*) AS total FROM products"

        )["total"],

        "orders": fetch_one(

            "SELECT COUNT(*) AS total FROM orders"

        )["total"],

        "customers": fetch_one(

            "SELECT COUNT(*) AS total FROM customers"

        )["total"],

        "employees": fetch_one(

            "SELECT COUNT(*) AS total FROM employees"

        )["total"]

    }

    return jsonify(tables)


# ==========================================================
# SYSTEM HEALTH
# ==========================================================

@dashboard_bp.route(
    "/dashboard/system-health",
    methods=["GET"]
)
def system_health():

    return jsonify({

        "status": "Healthy",

        "database": "Connected",

        "api": "Running",

        "version": "1.0.0"

    })


# ==========================================================
# LIVE METRICS
# ==========================================================

@dashboard_bp.route(
    "/dashboard/live",
    methods=["GET"]
)
def live_dashboard():

    orders = fetch_one("""

        SELECT COUNT(*)

        AS total

        FROM orders

        WHERE DATE(created_at)=

              DATE('now','localtime')

    """)

    revenue = fetch_one("""

        SELECT

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE DATE(created_at)=

              DATE('now','localtime')

        AND payment_status='Paid'

    """)

    pending = fetch_one("""

        SELECT COUNT(*)

        AS total

        FROM orders

        WHERE order_status='Pending'

    """)

    return jsonify({

        "today_orders":

            orders["total"],

        "today_revenue":

            revenue["revenue"],

        "pending_orders":

            pending["total"]

    })


# ==========================================================
# DASHBOARD VERSION
# ==========================================================

@dashboard_bp.route(
    "/dashboard/version",
    methods=["GET"]
)
def dashboard_version():

    return jsonify({

        "application":

            "CafeSync POS",

        "version":

            "1.0.0",

        "backend":

            "Flask",

        "database":

            "SQLite"

    })
@dashboard_bp.route("/dashboard/sales-chart", methods=["GET"])
def sales_chart():

    period = request.args.get("period", "daily")

    conn = get_connection()
    cursor = conn.cursor()

    if period == "daily":
        cursor.execute("""
            SELECT DATE(created_at) AS label,
                   SUM(total) AS revenue,
                   COUNT(*) AS orders
            FROM orders
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
            LIMIT 7
        """)

    elif period == "weekly":
        cursor.execute("""
            SELECT strftime('%W', created_at) AS label,
                   SUM(total) AS revenue,
                   COUNT(*) AS orders
            FROM orders
            GROUP BY strftime('%W', created_at)
            ORDER BY label
            LIMIT 8
        """)

    elif period == "monthly":
        cursor.execute("""
            SELECT strftime('%Y-%m', created_at) AS label,
                   SUM(total) AS revenue,
                   COUNT(*) AS orders
            FROM orders
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY label
        """)

    else:  # yearly
        cursor.execute("""
            SELECT strftime('%Y', created_at) AS label,
                   SUM(total) AS revenue,
                   COUNT(*) AS orders
            FROM orders
            GROUP BY strftime('%Y', created_at)
            ORDER BY label
        """)

    rows = cursor.fetchall()
    conn.close()

    return jsonify({
        "labels": [r[0] for r in rows],
        "revenue": [r[1] or 0 for r in rows],
        "orders": [r[2] or 0 for r in rows]
    })

@dashboard_bp.route("/dashboard/data")
def dashboard_data():

    conn = get_connection()
    cursor = conn.cursor()

    # total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # total categories
    cursor.execute("SELECT COUNT(*) FROM categories")
    total_categories = cursor.fetchone()[0]

    # total orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # revenue
    cursor.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM orders
    """)
    revenue = cursor.fetchone()[0]


    return jsonify({

        "success": True,

        "data": {

            "total_products": total_products,

            "total_categories": total_categories,

            "total_orders": total_orders,

            "revenue": revenue

        }

    })


# ==========================================================
# PING
# ==========================================================

@dashboard_bp.route(
    "/dashboard/ping",
    methods=["GET"]
)
def dashboard_ping():

    return jsonify({

        "status": "OK"

    })


# ==========================================================
# END OF DASHBOARD
# ==========================================================