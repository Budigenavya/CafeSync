from flask import Blueprint, jsonify, request, send_file, render_template
from models import get_connection
import sqlite3
import io
import datetime
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from routes.auth import login_required

reports_bp = Blueprint(
    "reports",
    __name__
)



# ==========================================================
# RESPONSE HELPERS
# ==========================================================

def success(message, data=None):

    return jsonify({

        "success": True,

        "message": message,

        "data": data

    })


def error(message, code=400):

    return jsonify({

        "success": False,

        "message": message

    }), code


@reports_bp.route("/")
@login_required
def reports():

    return render_template("reports.html")

@reports_bp.route("/dashboard", methods=["GET"])
@login_required
def reports_dashboard():

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Add your actual report queries here
        # For now, return valid data structure

        data = {
            "labels": [],
            "revenue": [],
            "orders": [],
            "profit": []
        }

        conn.close()

        return jsonify({
            "success": True,
            "data": data
        })

    except Exception as e:

        if conn:
            conn.close()

        print("REPORT DASHBOARD ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e),
            "data": {
                "labels": [],
                "revenue": [],
                "orders": [],
                "profit": []
            }
        }), 500


@reports_bp.route("/charts", methods=["GET"])
@login_required
def reports_charts():

    conn = None

    try:

        # ==================================================
        # DATABASE CONNECTION
        # ==================================================

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()


        # ==================================================
        # 1. DAILY SALES / REVENUE
        # ==================================================

        cursor.execute("""
            SELECT
                DATE(created_at) AS date,
                COALESCE(SUM(total), 0) AS revenue,
                COUNT(*) AS orders
            FROM orders
            WHERE status != 'Cancelled'
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)

        rows = cursor.fetchall()

        sales_labels = []
        sales_revenue = []
        sales_orders = []

        for row in rows:

            sales_labels.append(
                row["date"]
            )

            sales_revenue.append(
                float(row["revenue"] or 0)
            )

            sales_orders.append(
                int(row["orders"] or 0)
            )


        # ==================================================
        # 2. PAYMENT METHOD CHART
        # ==================================================

        cursor.execute("""
            SELECT
                COALESCE(payment_method, 'Unknown') AS payment_method,
                COUNT(*) AS count,
                COALESCE(SUM(total), 0) AS amount
            FROM orders
            WHERE status != 'Cancelled'
            GROUP BY payment_method
            ORDER BY amount DESC
        """)

        payment_rows = cursor.fetchall()

        payment_labels = []
        payment_values = []

        for row in payment_rows:

            payment_labels.append(
                row["payment_method"]
            )

            payment_values.append(
                float(row["amount"] or 0)
            )


        # ==================================================
        # 3. ORDER TYPE CHART
        # ==================================================

        cursor.execute("""
            SELECT
                COALESCE(order_type, 'Unknown') AS order_type,
                COUNT(*) AS count
            FROM orders
            WHERE status != 'Cancelled'
            GROUP BY order_type
            ORDER BY count DESC
        """)

        order_type_rows = cursor.fetchall()

        order_type_labels = []
        order_type_values = []

        for row in order_type_rows:

            order_type_labels.append(
                row["order_type"]
            )

            order_type_values.append(
                int(row["count"] or 0)
            )


        # ==================================================
        # 4. TOP PRODUCTS
        # ==================================================

        cursor.execute("""
            SELECT
                p.name,
                SUM(oi.quantity) AS quantity,
                COALESCE(
                    SUM(oi.quantity * oi.price),
                    0
                ) AS revenue

            FROM order_items oi

            JOIN products p
                ON oi.product_id = p.id

            JOIN orders o
                ON oi.order_id = o.id

            WHERE o.status != 'Cancelled'

            GROUP BY p.id, p.name

            ORDER BY revenue DESC

            LIMIT 10
        """)

        product_rows = cursor.fetchall()

        product_labels = []
        product_values = []

        for row in product_rows:

            product_labels.append(
                row["name"]
            )

            product_values.append(
                float(row["revenue"] or 0)
            )


        # ==================================================
        # 5. CATEGORY SALES
        # ==================================================

        cursor.execute("""
            SELECT
                c.name AS category,

                COALESCE(
                    SUM(oi.quantity * oi.price),
                    0
                ) AS revenue

            FROM order_items oi

            JOIN products p
                ON oi.product_id = p.id

            JOIN categories c
                ON p.category_id = c.id

            JOIN orders o
                ON oi.order_id = o.id

            WHERE o.status != 'Cancelled'

            GROUP BY c.id, c.name

            ORDER BY revenue DESC
        """)

        category_rows = cursor.fetchall()

        category_labels = []
        category_values = []

        for row in category_rows:

            category_labels.append(
                row["category"]
            )

            category_values.append(
                float(row["revenue"] or 0)
            )


        # ==================================================
        # 6. FINAL RESPONSE
        # ==================================================

        response_data = {

            # ----------------------------------------------
            # SALES
            # ----------------------------------------------

            "labels": sales_labels,

            "revenue": sales_revenue,

            "orders": sales_orders,


            # ----------------------------------------------
            # PAYMENT
            # ----------------------------------------------

            "payment": {

                "labels": payment_labels,

                "values": payment_values

            },


            # ----------------------------------------------
            # ORDER TYPE
            # ----------------------------------------------

            "order_type": {

                "labels": order_type_labels,

                "values": order_type_values

            },


            # ----------------------------------------------
            # PRODUCTS
            # ----------------------------------------------

            "products": {

                "labels": product_labels,

                "values": product_values

            },


            # ----------------------------------------------
            # CATEGORIES
            # ----------------------------------------------

            "categories": {

                "labels": category_labels,

                "values": category_values

            }

        }


        print(
            "🔥 REPORT CHART DATA:",
            response_data
        )


        return jsonify({

            "success": True,

            "data": response_data

        })


    # ======================================================
    # ERROR HANDLING
    # ======================================================

    except Exception as e:

        print(
            "🔥🔥🔥 REPORT CHART ERROR 🔥🔥🔥"
        )

        print(
            "ERROR TYPE:",
            type(e).__name__
        )

        print(
            "ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message": str(e),

            "data": {

                "labels": [],

                "revenue": [],

                "orders": [],

                "payment": {

                    "labels": [],

                    "values": []

                },

                "order_type": {

                    "labels": [],

                    "values": []

                },

                "products": {

                    "labels": [],

                    "values": []

                },

                "categories": {

                    "labels": [],

                    "values": []

                }

            }

        }), 500


    # ======================================================
    # CLOSE DATABASE
    # ======================================================

    finally:

        if conn:

            conn.close()

# ==========================================================
# DASHBOARD
# ==========================================================

@reports_bp.route(

    "/dashboard",

    methods=["GET"]

)

def dashboard():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # Today's Revenue

        cursor.execute("""

            SELECT

            IFNULL(SUM(total),0)

            FROM orders

            WHERE DATE(created_at)=DATE('now','localtime')

            AND status='Completed'

        """)

        today_revenue = cursor.fetchone()[0]

        # Today's Orders

        cursor.execute("""

            SELECT COUNT(*)

            FROM orders

            WHERE DATE(created_at)=DATE('now','localtime')

        """)

        today_orders = cursor.fetchone()[0]

        # Total Revenue

        cursor.execute("""

            SELECT

            IFNULL(SUM(total),0)

            FROM orders

            WHERE status='Completed'

        """)

        total_revenue = cursor.fetchone()[0]

        # Total Orders

        cursor.execute("""

            SELECT COUNT(*)

            FROM orders

        """)

        total_orders = cursor.fetchone()[0]

        # Average Bill

        cursor.execute("""

            SELECT

            IFNULL(AVG(total),0)

            FROM orders

            WHERE status='Completed'

        """)

        average_bill = cursor.fetchone()[0]

        # GST

        cursor.execute("""

            SELECT

            IFNULL(SUM(gst),0)

            FROM orders

            WHERE status='Completed'

        """)

        gst = cursor.fetchone()[0]

        # Refunds

        cursor.execute("""

            SELECT

            IFNULL(SUM(total),0)

            FROM orders

            WHERE status='Refunded'

        """)

        refunds = cursor.fetchone()[0]

        # Customers

        cursor.execute("""

            SELECT

            COUNT(DISTINCT customer_name)

            FROM orders

        """)

        customers = cursor.fetchone()[0]

        conn.close()

        return success(

            "Dashboard Loaded",

            {

                "today_revenue": today_revenue,

                "today_orders": today_orders,

                "total_revenue": total_revenue,

                "total_orders": total_orders,

                "average_bill": average_bill,

                "gst": gst,

                "refunds": refunds,

                "customers": customers

            }

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Dashboard",

            500

        )
# ==========================================================
# CHART DATA
# ==========================================================

@reports_bp.route(

    "/charts",

    methods=["GET"]

)

def chart_data():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # --------------------------------------------------
        # DAILY SALES (LAST 7 DAYS)
        # --------------------------------------------------

        cursor.execute("""

            SELECT

                DATE(created_at) AS day,

                IFNULL(SUM(total),0) AS revenue

            FROM orders

            WHERE status='Completed'

            GROUP BY DATE(created_at)

            ORDER BY DATE(created_at) DESC

            LIMIT 7

        """)

        rows = cursor.fetchall()[::-1]

        sales = {

            "labels":[row["day"] for row in rows],

            "values":[row["revenue"] for row in rows]

        }

        # --------------------------------------------------
        # PAYMENT METHODS
        # --------------------------------------------------

        cursor.execute("""

            SELECT

                payment_method,

                COUNT(*) total

            FROM orders

            GROUP BY payment_method

        """)

        rows = cursor.fetchall()

        payments = {

            "labels":[

                row["payment_method"]

                for row in rows

            ],

            "values":[

                row["total"]

                for row in rows

            ]

        }

        # --------------------------------------------------
        # TOP PRODUCTS
        # --------------------------------------------------

        cursor.execute("""

            SELECT

                p.name,

                SUM(oi.quantity) qty

            FROM order_items oi

            JOIN products p

            ON oi.product_id=p.id

            GROUP BY p.id

            ORDER BY qty DESC

            LIMIT 10

        """)

        rows = cursor.fetchall()

        products = {

            "labels":[

                row["name"]

                for row in rows

            ],

            "values":[

                row["qty"]

                for row in rows

            ]

        }

        # --------------------------------------------------
        # CATEGORY SALES
        # --------------------------------------------------

        cursor.execute("""

            SELECT

                c.name,

                SUM(oi.quantity) qty

            FROM order_items oi

            JOIN products p

            ON oi.product_id=p.id

            JOIN categories c

            ON p.category_id=c.id

            GROUP BY c.id

            ORDER BY qty DESC

        """)

        rows = cursor.fetchall()

        categories = {

            "labels":[

                row["name"]

                for row in rows

            ],

            "values":[

                row["qty"]

                for row in rows

            ]

        }

        conn.close()

        return success(

            "Charts Loaded",

            {

                "sales":sales,

                "payments":payments,

                "products":products,

                "categories":categories

            }

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Charts",

            500

        )
# ==========================================================
# REPORT TABLES
# ==========================================================

@reports_bp.route("/tables", methods=["GET"])
@login_required
def report_tables():

    conn = None

    try:

        conn = get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # ==================================================
        # RECENT ORDERS
        # ==================================================

        cursor.execute("""
            SELECT
                o.id,
                o.bill_no,
                o.order_type,
                o.payment_method,
                o.status,
                o.subtotal,
                o.gst,
                o.discount,
                o.total,
                o.created_at
            FROM orders o
            ORDER BY o.id DESC
            LIMIT 20
        """)

        recent_orders = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ==================================================
        # TOP PRODUCTS
        # ==================================================

        cursor.execute("""
            SELECT
                p.name,
                c.name AS category,
                SUM(oi.quantity) AS quantity,
                SUM(oi.quantity * oi.price) AS revenue

            FROM order_items oi

            JOIN products p
                ON oi.product_id = p.id

            LEFT JOIN categories c
                ON p.category_id = c.id

            GROUP BY p.id, p.name, c.name

            ORDER BY quantity DESC

            LIMIT 10
        """)

        top_products = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ==================================================
        # LOW STOCK
        # ==================================================

        cursor.execute("""
            SELECT
                p.name,
                c.name AS category,
                p.stock

            FROM products p

            LEFT JOIN categories c
                ON p.category_id = c.id

            WHERE p.stock <= 15

            ORDER BY p.stock ASC
        """)

        low_stock = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ==================================================
        # REFUNDED ORDERS
        # ==================================================

        cursor.execute("""
            SELECT
                id,
                bill_no,
                order_type,
                payment_method,
                total,
                status,
                created_at

            FROM orders

            WHERE status = 'Refunded'

            ORDER BY created_at DESC
        """)

        refunds = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ==================================================
        # RESPONSE
        # ==================================================

        return success(
            "Tables Loaded",
            {
                "recent_orders": recent_orders,
                "top_products": top_products,
                "low_stock": low_stock,
                "refunds": refunds
            }
        )

    except Exception as e:

        print(
            "🔥 REPORT TABLES ERROR:",
            e
        )

        return error(
            str(e),
            500
        )

    finally:

        if conn:
            conn.close()# ==========================================================
# FILTER REPORTS
# ==========================================================

@reports_bp.route("/filter", methods=["GET"])
def filter_reports():

    try:

        report_type = request.args.get("type", "today")
        start = request.args.get("start")
        end = request.args.get("end")

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if report_type == "today":

            where = "DATE(created_at)=DATE('now','localtime')"

        elif report_type == "yesterday":

            where = "DATE(created_at)=DATE('now','-1 day','localtime')"

        elif report_type == "week":

            where = "DATE(created_at)>=DATE('now','-6 day','localtime')"

        elif report_type == "month":

            where = "strftime('%Y-%m',created_at)=strftime('%Y-%m','now','localtime')"

        elif report_type == "year":

            where = "strftime('%Y',created_at)=strftime('%Y','now','localtime')"

        elif report_type == "custom" and start and end:

            where = f"DATE(created_at) BETWEEN '{start}' AND '{end}'"

        else:

            where = "1=1"

        cursor.execute(f"""

            SELECT *

            FROM orders

            WHERE {where}

            ORDER BY created_at DESC

        """)

        orders = [dict(r) for r in cursor.fetchall()]

        total_orders = len(orders)

        total_revenue = sum(
            float(o.get("total", 0))
            for o in orders
            if o.get("status") == "Completed"
        )

        average_bill = (
            total_revenue / total_orders
            if total_orders
            else 0
        )

        dashboard = {

            "today_revenue": total_revenue,
            "today_orders": total_orders,
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_bill": average_bill,
            "gst": sum(float(o.get("gst", 0)) for o in orders),
            "refunds": sum(
                float(o.get("total", 0))
                for o in orders
                if o.get("status") == "Refunded"
            ),
            "customers": len(
                set(
                    o.get("customer_name")
                    for o in orders
                    if o.get("customer_name")
                )
            )

        }

        conn.close()

        return success(

            "Report Filtered",

            {

                "dashboard": dashboard,
                "recent_orders": orders,
                "top_products": [],
                "low_stock": [],
                "refunds": [],
                "sales": {
                    "labels": [],
                    "values": []
                },
                "payments": {
                    "labels": [],
                    "values": []
                },
                "products": {
                    "labels": [],
                    "values": []
                },
                "categories": {
                    "labels": [],
                    "values": []
                }

            }

        )

    except Exception as e:

        print(e)

        return error("Unable To Filter Report", 500)


# ==========================================================
# EXPORT EXCEL
# ==========================================================

@reports_bp.route("/export/excel", methods=["GET"])
def export_excel():

    try:

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            ORDER BY created_at DESC

        """)

        rows = cursor.fetchall()

        wb = Workbook()

        ws = wb.active

        ws.title = "CafeSync Reports"

        if rows:

            ws.append(rows[0].keys())

            for row in rows:

                ws.append(list(row))

        output = io.BytesIO()

        wb.save(output)

        output.seek(0)

        conn.close()

        return send_file(

            output,

            as_attachment=True,

            download_name="CafeSync_Report.xlsx",

            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        )

    except Exception as e:

        print(e)

        return error("Unable To Export Excel", 500)


# ==========================================================
# EXPORT PDF
# ==========================================================

@reports_bp.route("/export/pdf", methods=["GET"])
def export_pdf():

    try:

        buffer = io.BytesIO()

        pdf = canvas.Canvas(

            buffer,

            pagesize=letter

        )

        pdf.setFont("Helvetica-Bold", 18)

        pdf.drawString(

            180,

            760,

            "CafeSync Sales Report"

        )

        pdf.setFont(

            "Helvetica",

            11

        )

        pdf.drawString(

            50,

            730,

            f"Generated : {datetime.datetime.now()}"

        )

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                order_number,
                customer_name,
                total,
                status

            FROM orders

            ORDER BY id DESC

            LIMIT 30

        """)

        y = 700

        for row in cursor.fetchall():

            pdf.drawString(

                40,

                y,

                f"{row['order_number']}"

            )

            pdf.drawString(

                150,

                y,

                f"{row['customer_name']}"

            )

            pdf.drawString(

                330,

                y,

                f"₹{row['total']}"

            )

            pdf.drawString(

                430,

                y,

                row["status"]

            )

            y -= 18

            if y < 60:

                pdf.showPage()

                y = 760

        pdf.save()

        buffer.seek(0)

        conn.close()

        return send_file(

            buffer,

            as_attachment=True,

            download_name="CafeSync_Report.pdf",

            mimetype="application/pdf"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Export PDF",

            500

        )
# ==========================================================
# HEALTH CHECK
# ==========================================================

@reports_bp.route(

    "/status",

    methods=["GET"]

)

def reports_status():

    return success(

        "Reports Module Running",

        {

            "module":"CafeSync Reports",

            "status":"OK"

        }

    )


# ==========================================================
# SALES SUMMARY
# ==========================================================

@reports_bp.route(

    "/summary",

    methods=["GET"]

)

def sales_summary():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) total_orders,

                IFNULL(SUM(total),0) total_sales,

                IFNULL(AVG(total),0) average_bill,

                IFNULL(MAX(total),0) highest_bill,

                IFNULL(MIN(total),0) lowest_bill

            FROM orders

            WHERE status='Completed'

        """)

        row = dict(cursor.fetchone())

        conn.close()

        return success(

            "Summary Loaded",

            row

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Summary",

            500

        )


# ==========================================================
# LOW STOCK COUNT
# ==========================================================

@reports_bp.route(

    "/low-stock-count",

    methods=["GET"]

)

def low_stock_count():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM products

            WHERE stock<=10

        """)

        count = cursor.fetchone()[0]

        conn.close()

        return success(

            "Low Stock Count",

            {

                "count":count

            }

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load",

            500

        )


# ==========================================================
# BEST SELLER
# ==========================================================

@reports_bp.route(

    "/best-seller",

    methods=["GET"]

)

def best_seller():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                p.name,

                SUM(oi.quantity) qty

            FROM order_items oi

            JOIN products p

            ON oi.product_id=p.id

            GROUP BY p.id

            ORDER BY qty DESC

            LIMIT 1

        """)

        row = cursor.fetchone()

        conn.close()

        if row:

            return success(

                "Best Seller",

                dict(row)

            )

        return success(

            "No Data",

            {}

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load",

            500

        )






# ==========================================================
# REGISTER BLUEPRINT
# ==========================================================
#
# In app.py register this blueprint:
#
# from routes.reports import reports_bp
#
# app.register_blueprint(reports_bp)
#
# ==========================================================