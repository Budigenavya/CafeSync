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

from openpyxl import Workbook

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from models import get_connection

orders_bp = Blueprint(

    "orders",

    __name__

)





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

            SELECT

                *

            FROM orders

            ORDER BY id DESC

        """)

        orders = []

        for row in cursor.fetchall():

            order = dict(row)

            cursor.execute("""

                SELECT

                    oi.product_id,

                    oi.quantity,

                    oi.price,

                    p.name

                FROM order_items oi

                LEFT JOIN products p

                ON oi.product_id = p.id

                WHERE oi.order_id = ?

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

        if order["status"] != "Completed":

            conn.close()

            return error(

                "Only Completed Orders Can Be Refunded"

            )

        # --------------------------------------
        # RESTORE STOCK
        # --------------------------------------

        cursor.execute("""

            SELECT

                product_id,

                quantity

            FROM order_items

            WHERE order_id=?

        """,

        (order_id,))

        items = cursor.fetchall()

        for item in items:

            cursor.execute("""

                UPDATE products

                SET stock = stock + ?

                WHERE id=?

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

                status=?,

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

                IFNULL(SUM(total),0) AS revenue,

                SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END) AS pending,

                SUM(CASE WHEN status='Preparing' THEN 1 ELSE 0 END) AS preparing,

                SUM(CASE WHEN status='Ready' THEN 1 ELSE 0 END) AS ready,

                SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed,

                SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled,

                SUM(CASE WHEN status='Refunded' THEN 1 ELSE 0 END) AS refunded

            FROM orders

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

            SELECT *

            FROM orders

            WHERE

                order_number LIKE ?

                OR customer_name LIKE ?

                OR table_number LIKE ?

            ORDER BY id DESC

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

            SELECT *

            FROM orders

            WHERE 1=1

        """

        params = []

        if status:

            query += " AND status=?"

            params.append(status)

        if payment:

            query += " AND payment_method=?"

            params.append(payment)

        if date:

            query += " AND DATE(created_at)=?"

            params.append(date)

        query += " ORDER BY id DESC"

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