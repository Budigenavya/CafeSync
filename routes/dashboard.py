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
from models import fetch_all
from datetime import date as date_type, datetime, time, timedelta, timezone

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@dashboard_bp.route("/dashboard/sales-statistics", methods=["GET"])
@login_required
def dashboard_sales_statistics():
    """Sales and order-channel breakdown for an India-local business date."""
    selected_date = request.args.get("date", "")
    if selected_date:
        try:
            selected_date = date_type.fromisoformat(selected_date).isoformat()
        except ValueError:
            return jsonify({"error": "date must use YYYY-MM-DD"}), 400
    else:
        selected_date = date_type.today().isoformat()

    conn = get_connection()
    try:
        # created_at is stored in SQLite's server time (UTC on Render); convert
        # it to the cafe's India-local date before grouping.
        day_expr = "DATE(datetime(o.created_at, '+5 hours', '+30 minutes'))"
        orders = conn.execute(f"""
            SELECT o.id, o.total, o.subtotal, o.discount, o.payment_method,
                   o.payment_status, o.status, o.order_type, o.order_source,
                   o.created_at
            FROM orders o WHERE {day_expr}=?
            ORDER BY o.created_at
        """, (selected_date,)).fetchall()
        order_ids = [row["id"] for row in orders]
        payments = {}
        if order_ids:
            placeholders = ",".join("?" for _ in order_ids)
            for row in conn.execute(f"""
                SELECT order_id, payment_type, SUM(amount) AS amount
                FROM payments WHERE order_id IN ({placeholders})
                  AND LOWER(COALESCE(payment_status,'paid'))='paid'
                GROUP BY order_id, payment_type
            """, order_ids).fetchall():
                payments.setdefault(row["order_id"], []).append(row)

        channel_names = {"dine in": "Dine In", "dine-in": "Dine In",
                         "parcel": "Parcel", "take away": "Parcel", "takeaway": "Parcel",
                         "delivery": "Delivery"}
        channels = {name: {"orders": 0, "sales": 0.0} for name in ("Dine In", "Parcel", "Delivery")}
        hourly = {}
        payment_totals = {}
        successful = cancelled = unpaid = 0
        gross_sales = discount_total = 0.0
        for row in orders:
            status = str(row["status"] or "").lower()
            payment_status = str(row["payment_status"] or "").lower()
            if status == "cancelled" or payment_status == "cancelled":
                cancelled += 1
                continue
            if status == "refunded" or payment_status == "refunded":
                continue
            paid = payment_status == "paid"
            if paid:
                successful += 1
                gross_sales += float(row["total"] or 0)
            else:
                unpaid += 1
            discount_total += float(row["discount"] or 0)
            channel_key = str(row["order_type"] or "").strip().lower()
            channel = channel_names.get(channel_key)
            if not channel and str(row["order_source"] or "").lower() in ("swiggy", "zomato"):
                channel = "Delivery"
            if channel in channels:
                channels[channel]["orders"] += 1
                if paid:
                    channels[channel]["sales"] += float(row["total"] or 0)
            hour = conn.execute("SELECT strftime('%H', datetime(?, '+5 hours', '+30 minutes'))", (row["created_at"],)).fetchone()[0]
            slot = (int(hour or 0) // 2) * 2
            bucket = hourly.setdefault(slot, {"Dine In": 0.0, "Parcel": 0.0, "Delivery": 0.0})
            if paid and channel in bucket:
                bucket[channel] += float(row["total"] or 0)
            if paid:
                if payments.get(row["id"]):
                    for payment in payments[row["id"]]:
                        method = str(payment["payment_type"] or "Other").title()
                        payment_totals[method] = payment_totals.get(method, 0) + float(payment["amount"] or 0)
                else:
                    method = str(row["payment_method"] or "Other").title()
                    payment_totals[method] = payment_totals.get(method, 0) + float(row["total"] or 0)

        # Item performance follows paid, non-cancelled bills for the selected day.
        top_items = []
        if order_ids:
            placeholders = ",".join("?" for _ in order_ids)
            top_items = [dict(r) for r in conn.execute(f"""
                SELECT COALESCE(p.name, 'Item') AS name, SUM(oi.quantity) AS quantity,
                       SUM(oi.quantity * oi.price) AS sales
                FROM order_items oi JOIN orders o ON o.id=oi.order_id
                LEFT JOIN products p ON p.id=oi.product_id
                WHERE oi.order_id IN ({placeholders}) AND LOWER(COALESCE(o.payment_status,''))='paid'
                  AND LOWER(COALESCE(o.status,'')) NOT IN ('cancelled','refunded')
                GROUP BY oi.product_id, p.name ORDER BY sales DESC LIMIT 5
            """, order_ids).fetchall()]
        return jsonify({
            "date": selected_date, "sales": gross_sales, "total_orders": len(orders),
            "successful_orders": successful, "cancelled_orders": cancelled, "unpaid_orders": unpaid,
            "average_order": gross_sales / successful if successful else 0,
            "discounts": discount_total, "payment_methods": payment_totals,
            "channels": channels,
            "hourly": [{"label": f"{h:02d}:00–{(h+2)%24:02d}:00", **values}
                       for h, values in sorted(hourly.items())],
            "top_items": top_items,
            "audit": {"cancelled": cancelled, "discounted_bills": sum(1 for r in orders if float(r["discount"] or 0) > 0),
                      "modified_kots": None, "shifted_kots": None, "modified_bills": None, "reprinted_bills": None}
        })
    finally:
        conn.close()


@dashboard_bp.route("/dashboard/overview", methods=["GET"])
def dashboard_overview():
    """Return cafe dashboard figures for the current local business day."""
    india_tz = timezone(timedelta(hours=5, minutes=30))
    today_india = datetime.now(timezone.utc).astimezone(india_tz).date()
    start_utc = datetime.combine(today_india, time.min, tzinfo=india_tz).astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = start_utc + timedelta(days=1)
    conn = get_connection()
    try:
        sales = conn.execute("""
            SELECT COUNT(*) AS orders,
                   IFNULL(SUM(CASE WHEN payment_status='Paid'
                       AND status NOT IN ('Cancelled','Refunded') THEN total ELSE 0 END), 0) AS sales,
                   IFNULL(AVG(CASE WHEN payment_status='Paid'
                       AND status NOT IN ('Cancelled','Refunded') THEN total END), 0) AS average_order
            FROM orders
            WHERE created_at >= ? AND created_at < ?
        """, (start_utc, end_utc)).fetchone()
        return jsonify({
            "today_orders": sales["orders"] or 0,
            "today_sales": sales["sales"] or 0,
            "average_order": sales["average_order"] or 0
        })
    finally:
        conn.close()


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

        WHERE stock_unlimited=0 AND stock<=min_stock

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

                SUM(CASE WHEN stock_unlimited=0 THEN stock ELSE 0 END),

                0

            ) AS stock,

            IFNULL(

                SUM(

                    CASE WHEN stock_unlimited=0 THEN stock*cost_price ELSE 0 END

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

        WHERE DATE(datetime(created_at, '+5 hours', '+30 minutes')) =
              DATE('now', '+5 hours', '+30 minutes')

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

            status,

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

            barcode,

            price

        FROM products

        WHERE stock_unlimited=0 AND stock<=5

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

            DATE(datetime(created_at, '+5 hours', '+30 minutes')) AS sales_date,

            COUNT(*) AS orders,

            IFNULL(

                SUM(total),

                0

            ) AS revenue

        FROM orders

        WHERE payment_status='Paid'

        GROUP BY DATE(datetime(created_at, '+5 hours', '+30 minutes'))

        ORDER BY DATE(datetime(created_at, '+5 hours', '+30 minutes')) DESC

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

        WHERE stock_unlimited=0 AND stock<=min_stock

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

        WHERE stock_unlimited=0 AND stock<=min_stock

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
