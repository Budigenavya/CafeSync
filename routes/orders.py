# ==========================================================
# CafeSync Orders
# ==========================================================

from flask import Blueprint, render_template
from flask import jsonify
from flask import request
from flask import send_file
from routes.auth import login_required

import sqlite3
import io
import datetime
import json

from openpyxl import Workbook

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from models import get_connection

orders_bp = Blueprint(

    "orders",

    __name__

)


@orders_bp.route("/orders/page", methods=["GET"])
@login_required
def orders_page():
    return render_template("orders.html")





# ==========================================================
# RESPONSE HELPERS
# ==========================================================

def success(message,data=None):

    return jsonify({

        "success":True,

        "message":message,

        "data":data

    })


def error(message,status=400):

    return jsonify({

        "success":False,

        "message":message

    }),status


@orders_bp.route("/orders/<int:order_id>/payment", methods=["PUT"])
@login_required
def mark_order_paid(order_id):
    data = request.get_json(silent=True) or {}
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT total, payment_status, payment_method, status FROM orders WHERE id=?", (order_id,))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return error("Order Not Found", 404)
        if order[3] in ("Cancelled", "Refunded"):
            conn.close()
            return error("Cancelled or refunded orders cannot be marked paid")
        if str(order[1] or "").lower() != "paid":
            method = (data.get("payment_method") or order[2] or "Cash").strip()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE order_id=? AND payment_status='Paid'
            """, (order_id,))
            amount_paid = float(cursor.fetchone()[0] or 0)
            amount_due = max(0, float(order[0] or 0) - amount_paid)
            cursor.execute("UPDATE orders SET payment_status='Paid', payment_method=? WHERE id=?", (method, order_id))
            if amount_due > 0.009:
                cursor.execute("INSERT INTO payments(order_id, payment_type, amount, payment_status) VALUES (?, ?, ?, 'Paid')", (order_id, method, amount_due))
            conn.commit()
        conn.close()
        return success("Payment marked as paid")
    except Exception as e:
        print(e)
        return error("Unable To Update Payment", 500)



# ==========================================================
# GET ALL ORDERS
# ==========================================================

@orders_bp.route(

    "/orders",

    methods=["GET"]

)

def get_orders():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT o.*, o.bill_no AS order_number,
                   t.table_name AS table_number,
                   c.name AS customer_name,
                   o.payment_status AS payment_state
            FROM orders o
            LEFT JOIN tables t ON t.id = o.table_id
            LEFT JOIN customers c ON c.id = o.customer_id
            ORDER BY o.id DESC

        """)

        orders = []

        for row in cursor.fetchall():

            order = dict(row)

            cursor.execute("""

                SELECT

                    oi.id,
                    oi.product_id,

                    oi.quantity,

                    oi.price,

                    oi.chef_note,

                    oi.addons,

                    p.name

                FROM order_items oi

                LEFT JOIN products p

                ON oi.product_id = p.id

                WHERE oi.order_id = ?
                ORDER BY oi.id

            """,

            (order["id"],))

            items = []

            total_items = 0

            for item in cursor.fetchall():

                item = dict(item)

                total_items += item["quantity"]

                items.append(item)

            order["items"] = items

            order["total_items"] = total_items

            if order.get("split_details"):
                try:
                    order["split_details"] = json.loads(order["split_details"])
                except (TypeError, ValueError):
                    order["split_details"] = None

            orders.append(order)

        conn.close()

        return success(

            "Orders Loaded",

            orders

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Orders",

            500

        )


# ==========================================================
# GET SINGLE ORDER
# ==========================================================

@orders_bp.route(

    "/orders/<int:order_id>",

    methods=["GET"]

)

def get_order(order_id):

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                *

            FROM orders

            WHERE id = ?

        """,

        (order_id,))

        row = cursor.fetchone()

        if row is None:

            conn.close()

            return error(

                "Order Not Found",

                404

            )

        order = dict(row)

        cursor.execute("""

            SELECT

                oi.product_id,

                oi.quantity,

                oi.price,

                oi.chef_note,

                oi.addons,

                p.name

            FROM order_items oi

            LEFT JOIN products p

            ON oi.product_id = p.id

            WHERE oi.order_id = ?

        """,

        (order_id,))

        items = []

        total_items = 0

        for item in cursor.fetchall():

            item = dict(item)

            total_items += item["quantity"]

            items.append(item)

        order["items"] = items

        order["total_items"] = total_items

        conn.close()

        return success(

            "Order Loaded",

            order

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Order",

            500

        )
# ==========================================================
# CANCEL ORDER
# ==========================================================

@orders_bp.route(

    "/orders/cancel/<int:order_id>",

    methods=["PUT"]

)

def cancel_order(order_id):

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # --------------------------------------
        # CHECK ORDER
        # --------------------------------------

        cursor.execute("""

            SELECT

                *

            FROM orders

            WHERE id = ?

        """,

        (order_id,))

        order = cursor.fetchone()

        if order is None:

            conn.close()

            return error(

                "Order Not Found",

                404

            )

        order = dict(order)

        # --------------------------------------
        # VALIDATE STATUS
        # --------------------------------------

        if order["status"] in [

            "Completed",

            "Served",

            "Cancelled",

            "Refunded"

        ]:

            conn.close()

            return error(

                "Order Cannot Be Cancelled"

            )

        # --------------------------------------
        # RESTORE INVENTORY
        # --------------------------------------

        cursor.execute("""

            SELECT

                product_id,

                quantity

            FROM order_items

            WHERE order_id = ?

        """,

        (order_id,))

        items = cursor.fetchall()

        for item in items:

            cursor.execute("""

                UPDATE products

                SET stock = stock + ?

                WHERE id = ?

            """,

            (

                item["quantity"],

                item["product_id"]

            ))

        # --------------------------------------
        # UPDATE ORDER
        # --------------------------------------

        cursor.execute("""

            UPDATE orders

            SET

                status = ?,

                cancelled_at = ?

            WHERE id = ?

        """,

        (

            "Cancelled",

            datetime.datetime.now(),

            order_id

        ))

        conn.commit()

        conn.close()

        return success(

            "Order Cancelled Successfully"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Cancel Order",

            500

        )


# ==========================================================
# GET CANCELLED ORDERS
# ==========================================================

@orders_bp.route(

    "/orders/cancelled",

    methods=["GET"]

)

def cancelled_orders():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                *

            FROM orders

            WHERE status='Cancelled'

            ORDER BY id DESC

        """)

        data = [

            dict(row)

            for row in cursor.fetchall()

        ]

        conn.close()

        return success(

            "Cancelled Orders Loaded",

            data

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Cancelled Orders",

            500

        )
# ==========================================================
# REFUND ORDER
# ==========================================================

@orders_bp.route(

    "/orders/refund/<int:order_id>",

    methods=["PUT"]

)

def refund_order(order_id):

    try:

        data = request.get_json()

        reason = data.get(

            "reason",

            ""

        ).strip()

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # --------------------------------------
        # CHECK ORDER
        # --------------------------------------

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE id=?

        """,

        (order_id,))

        row = cursor.fetchone()

        if row is None:

            conn.close()

            return error(

                "Order Not Found",

                404

            )

        order = dict(row)

        # --------------------------------------
        # VALIDATE STATUS
        # --------------------------------------

        if order["status"] not in ("Completed", "Served"):

            conn.close()

            return error(

                "Only Completed Orders Can Be Refunded"

            )

        if str(order.get("payment_status") or "").lower() != "paid":
            conn.close()
            return error("Only paid orders can be refunded")

        # --------------------------------------
        # UPDATE ORDER
        # --------------------------------------

        cursor.execute("""

            UPDATE orders

            SET

                status=?,

                payment_status='Refunded',

                refund_reason=?,

                refunded_at=?

            WHERE id=?

        """,

        (

            "Refunded",

            reason,

            datetime.datetime.now(),

            order_id

        ))

        cursor.execute("""
            INSERT INTO payments(order_id, payment_type, amount, payment_status)
            VALUES (?, ?, ?, 'Refunded')
        """, (
            order_id,
            order.get("payment_method") or "Other",
            -float(order.get("total") or 0)
        ))

        conn.commit()

        conn.close()

        return success(

            "Order Refunded Successfully"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Refund Order",

            500

        )


# ==========================================================
# GET REFUNDED ORDERS
# ==========================================================

@orders_bp.route(

    "/orders/refunded",

    methods=["GET"]

)

def refunded_orders():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE status='Refunded'

            ORDER BY id DESC

        """)

        data = [

            dict(row)

            for row in cursor.fetchall()

        ]

        conn.close()

        return success(

            "Refunded Orders Loaded",

            data

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Refunded Orders",

            500

        )


# ==========================================================
# REFUND SUMMARY
# ==========================================================

@orders_bp.route(

    "/orders/refund-summary",

    methods=["GET"]

)

def refund_summary():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) AS total_refunds,

                IFNULL(SUM(total),0) AS refund_amount

            FROM orders

            WHERE status='Refunded'

        """)

        summary = dict(

            cursor.fetchone()

        )

        conn.close()

        return success(

            "Refund Summary Loaded",

            summary

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Refund Summary",

            500

        )
# ==========================================================
# EXPORT ORDERS TO EXCEL
# ==========================================================

@orders_bp.route(

    "/orders/export/excel",

    methods=["GET"]

)

def export_orders_excel():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                order_number,

                customer_name,

                table_number,

                payment_method,

                status,

                total,

                created_at

            FROM orders

            ORDER BY id DESC

        """)

        rows = cursor.fetchall()

        workbook = Workbook()

        sheet = workbook.active

        sheet.title = "Orders"

        sheet.append([

            "Order No",

            "Customer",

            "Table",

            "Payment",

            "Status",

            "Total",

            "Created At"

        ])

        for row in rows:

            sheet.append([

                row["order_number"],

                row["customer_name"],

                row["table_number"],

                row["payment_method"],

                row["status"],

                row["total"],

                row["created_at"]

            ])

        output = io.BytesIO()

        workbook.save(output)

        output.seek(0)

        conn.close()

        return send_file(

            output,

            as_attachment=True,

            download_name="CafeSync_Orders.xlsx",

            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Export Excel",

            500

        )


# ==========================================================
# EXPORT ORDERS TO PDF
# ==========================================================

@orders_bp.route(

    "/orders/export/pdf",

    methods=["GET"]

)

def export_orders_pdf():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                order_number,

                customer_name,

                total,

                payment_method,

                status,

                created_at

            FROM orders

            ORDER BY id DESC

        """)

        rows = cursor.fetchall()

        buffer = io.BytesIO()

        pdf = canvas.Canvas(

            buffer,

            pagesize=letter

        )

        width, height = letter

        y = height - 40

        pdf.setFont(

            "Helvetica-Bold",

            18

        )

        pdf.drawString(

            40,

            y,

            "CafeSync Orders Report"

        )

        y -= 35

        pdf.setFont(

            "Helvetica",

            10

        )

        for row in rows:

            line = (

                f"{row['order_number']} | "

                f"{row['customer_name'] or 'Walk-in'} | "

                f"₹{row['total']} | "

                f"{row['payment_method']} | "

                f"{row['status']} | "

                f"{row['created_at']}"

            )

            pdf.drawString(

                40,

                y,

                line

            )

            y -= 18

            if y < 50:

                pdf.showPage()

                pdf.setFont(

                    "Helvetica",

                    10

                )

                y = height - 40

        pdf.save()

        buffer.seek(0)

        conn.close()

        return send_file(

            buffer,

            as_attachment=True,

            download_name="CafeSync_Orders.pdf",

            mimetype="application/pdf"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Export PDF",

            500

        )
# ==========================================================
# ORDERS DASHBOARD SUMMARY
# ==========================================================

@orders_bp.route(

    "/orders/dashboard",

    methods=["GET"]

)

def orders_dashboard():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) AS total_orders,

                IFNULL(SUM(CASE WHEN payment_status='Paid' THEN total ELSE 0 END),0) AS revenue,

                IFNULL(SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END),0) AS pending,

                IFNULL(SUM(CASE WHEN status='Preparing' THEN 1 ELSE 0 END),0) AS preparing,

                IFNULL(SUM(CASE WHEN status='Ready' THEN 1 ELSE 0 END),0) AS ready,

                IFNULL(SUM(CASE WHEN status IN ('Completed','Served') THEN 1 ELSE 0 END),0) AS completed,

                IFNULL(SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END),0) AS cancelled,

                IFNULL(SUM(CASE WHEN status='Refunded' THEN 1 ELSE 0 END),0) AS refunded

            FROM orders
            WHERE DATE(created_at)=DATE('now','localtime')

        """)

        summary = dict(cursor.fetchone())

        conn.close()

        return success(

            "Dashboard Loaded",

            summary

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Dashboard",

            500

        )


# ==========================================================
# SEARCH ORDERS
# ==========================================================

@orders_bp.route(

    "/orders/search",

    methods=["GET"]

)

def search_orders():

    try:

        keyword = request.args.get(

            "q",

            ""

        ).strip()

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT o.*, o.bill_no AS order_number,
                   t.table_name AS table_number,
                   c.name AS customer_name,
                   o.payment_status AS payment_state
            FROM orders o
            LEFT JOIN tables t ON t.id = o.table_id
            LEFT JOIN customers c ON c.id = o.customer_id
            WHERE o.bill_no LIKE ? OR c.name LIKE ?
               OR CAST(t.table_name AS TEXT) LIKE ?
            ORDER BY o.id DESC

        """,

        (

            f"%{keyword}%",

            f"%{keyword}%",

            f"%{keyword}%"

        ))

        data = [

            dict(row)

            for row in cursor.fetchall()

        ]

        conn.close()

        return success(

            "Search Completed",

            data

        )

    except Exception as e:

        print(e)

        return error(

            "Search Failed",

            500

        )


# ==========================================================
# FILTER ORDERS
# ==========================================================

@orders_bp.route(

    "/orders/filter",

    methods=["GET"]

)

def filter_orders():

    try:

        status = request.args.get(

            "status",

            ""

        )

        payment = request.args.get(

            "payment",

            ""

        )

        date = request.args.get(

            "date",

            ""

        )

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        query = """

            SELECT o.*, o.bill_no AS order_number,
                   t.table_name AS table_number,
                   c.name AS customer_name,
                   o.payment_status AS payment_state
            FROM orders o
            LEFT JOIN tables t ON t.id = o.table_id
            LEFT JOIN customers c ON c.id = o.customer_id
            WHERE 1=1

        """

        params = []

        if status:

            query += " AND o.status=?"

            params.append(status)

        if payment:

            query += " AND o.payment_method=?"

            params.append(payment)

        if date:

            query += " AND DATE(o.created_at)=?"

            params.append(date)

        query += " ORDER BY o.id DESC"

        cursor.execute(

            query,

            params

        )

        data = [

            dict(row)

            for row in cursor.fetchall()

        ]

        conn.close()

        return success(

            "Orders Filtered",

            data

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Filter Orders",

            500

        )


# ==========================================================
# TODAY'S SALES
# ==========================================================

@orders_bp.route(

    "/orders/today",

    methods=["GET"]

)

def today_sales():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) AS total_orders,

                IFNULL(SUM(total),0) AS revenue

            FROM orders

            WHERE DATE(created_at)=DATE('now','localtime')

        """)

        result = dict(

            cursor.fetchone()

        )

        conn.close()

        return success(

            "Today's Sales",

            result

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Today's Sales",

            500

        )


# ==========================================================
# DELETE ORDER
# ==========================================================

@orders_bp.route(

    "/orders/<int:order_id>",

    methods=["DELETE"]

)

def delete_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(

            "DELETE FROM order_items WHERE order_id=?",

            (order_id,)

        )

        cursor.execute(

            "DELETE FROM orders WHERE id=?",

            (order_id,)

        )

        conn.commit()

        conn.close()

        return success(

            "Order Deleted Successfully"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Delete Order",

            500

        )
