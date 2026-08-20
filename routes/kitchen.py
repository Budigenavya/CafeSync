# ==========================================================
# CafeSync Kitchen Module
# ==========================================================

from flask import Blueprint, jsonify, render_template
from routes.auth import login_required
from database import get_connection

import sqlite3
from datetime import datetime

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


# ==========================================================
# BLUEPRINT
# ==========================================================

kitchen_bp = Blueprint(
    "kitchen",
    __name__
)


# ==========================================================
# KITCHEN PAGE
# ==========================================================

@kitchen_bp.route("/kitchen")
@login_required
def kitchen():

    return render_template("kitchen.html")


# ==========================================================
# KITCHEN ORDERS
# ==========================================================

@kitchen_bp.route("/kitchen/orders", methods=["GET"])
def get_kitchen_orders():

    try:

        conn = get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.bill_no,
                o.table_id,
                o.customer_id,
                o.order_type,
                o.subtotal,
                o.gst,
                o.discount,
                o.total,
                o.payment_method,
                o.status,
                o.created_at

            FROM orders o

            WHERE o.status IN (
                'Pending',
                'Preparing',
                'Ready'
            )

            ORDER BY o.created_at ASC
        """)

        orders = []

        for order in cursor.fetchall():

            # Get products in this order
            item_cursor = conn.execute("""
                SELECT
                    oi.product_id,
                    p.name,
                    oi.quantity,
                    oi.price

                FROM order_items oi

                JOIN products p
                    ON p.id = oi.product_id

                WHERE oi.order_id = ?

                ORDER BY p.name
            """, (order["id"],))

            items = [
                dict(item)
                for item in item_cursor.fetchall()
            ]

            order_data = dict(order)

            order_data["items"] = items

            order_data["total_items"] = sum(
                item["quantity"]
                for item in items
            )

            orders.append(order_data)

        conn.close()

        return success(
            "Kitchen Orders Loaded",
            orders
        )

    except Exception as e:

        print("🔥🔥🔥 KITCHEN ORDERS ERROR 🔥🔥🔥")
        print(e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==========================================================
# START PREPARING ORDER
# ==========================================================

@kitchen_bp.route("/kitchen/start-preparing/<int:order_id>", methods=["PUT"])
@login_required
def start_preparing(order_id):

    conn = None

    try:

        print("🔥 START PREPARING:", order_id)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE orders
            SET status = 'Preparing'
            WHERE id = ?
        """, (order_id,))

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        conn.commit()

        print(
            "🔥 ORDER NOW PREPARING:",
            order_id
        )

        return jsonify({
            "success": True,
            "message": "Order is now Preparing",
            "data": {
                "order_id": order_id,
                "status": "Preparing"
            }
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("\n🔥🔥🔥 START PREPARING ERROR 🔥🔥🔥")
        print(type(e).__name__)
        print(str(e))
        print("🔥🔥🔥 END ERROR 🔥🔥🔥\n")

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()
# ==========================================================
# MARK ORDER READY
# ==========================================================

@kitchen_bp.route("/kitchen/ready/<int:order_id>", methods=["PUT"])
@login_required
def mark_ready(order_id):

    conn = None

    try:
        print("🔥 MARK READY CALLED:", order_id)

        conn = get_connection()
        cursor = conn.cursor()

        # Check order exists
        cursor.execute("""
            SELECT id, status
            FROM orders
            WHERE id = ?
        """, (order_id,))

        order = cursor.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        print(
            "🔥 CURRENT STATUS:",
            order[1]
        )

        # Change status
        cursor.execute("""
            UPDATE orders
            SET status = 'Ready'
            WHERE id = ?
        """, (order_id,))

        conn.commit()

        print(
            "🔥 ORDER MARKED READY:",
            order_id
        )

        return jsonify({
            "success": True,
            "message": "Order marked as Ready",
            "data": {
                "order_id": order_id,
                "status": "Ready"
            }
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("\n🔥🔥🔥 MARK READY ERROR 🔥🔥🔥")
        print("TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("🔥🔥🔥 END ERROR 🔥🔥🔥\n")

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()
# ==========================================================
# SERVE ORDER
# ==========================================================

@kitchen_bp.route("/kitchen/serve/<int:order_id>", methods=["PUT"])
@login_required
def serve_order(order_id):

    conn = None

    try:
        print("🔥 SERVE ORDER CALLED:", order_id)

        conn = get_connection()
        cursor = conn.cursor()

        # Check order exists
        cursor.execute("""
            SELECT id, status
            FROM orders
            WHERE id = ?
        """, (order_id,))

        order = cursor.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        print("🔥 CURRENT STATUS:", order[1])

        # Mark order as served/completed
        cursor.execute("""
            UPDATE orders
            SET status = 'Served'
            WHERE id = ?
        """, (order_id,))

        conn.commit()

        print("🔥 ORDER SERVED:", order_id)

        return jsonify({
            "success": True,
            "message": "Order served successfully",
            "data": {
                "order_id": order_id,
                "status": "Served"
            }
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("\n🔥🔥🔥 SERVE ORDER ERROR 🔥🔥🔥")
        print("TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("🔥🔥🔥 END ERROR 🔥🔥🔥\n")

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()

# ==========================================================
# SAVE CHEF NOTES
# ==========================================================

@kitchen_bp.route(

    "/kitchen/notes/<int:order_id>",

    methods=["PUT"]

)

def save_chef_notes(order_id):

    try:

        data = request.get_json()

        notes = data.get("notes", "").strip()

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT id

            FROM orders

            WHERE id = ?

        """,

        (order_id,))

        if cursor.fetchone() is None:

            conn.close()

            return error(

                "Order Not Found",

                404

            )

        cursor.execute("""

            UPDATE orders

            SET chef_notes = ?

            WHERE id = ?

        """,

        (

            notes,

            order_id

        ))

        conn.commit()

        conn.close()

        return success(

            "Chef Notes Saved"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Save Chef Notes",

            500

        )

        

    except Exception as e:

        print(e)

        return error(

            "Unable To Mark Order Ready",

            500

        )
# ==========================================================
# KITCHEN DASHBOARD
# ==========================================================

@kitchen_bp.route(

    "/kitchen/dashboard",

    methods=["GET"]

)

def kitchen_dashboard():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # --------------------------------------
        # Pending Orders
        # --------------------------------------

        cursor.execute("""

            SELECT COUNT(*) AS total

            FROM orders

            WHERE status='Pending'

        """)

        pending = cursor.fetchone()["total"]

        # --------------------------------------
        # Preparing Orders
        # --------------------------------------

        cursor.execute("""

            SELECT COUNT(*) AS total

            FROM orders

            WHERE status='Preparing'

        """)

        preparing = cursor.fetchone()["total"]

        # --------------------------------------
        # Ready Orders
        # --------------------------------------

        cursor.execute("""

            SELECT COUNT(*) AS total

            FROM orders

            WHERE status='Ready'

        """)

        ready = cursor.fetchone()["total"]

        # --------------------------------------
        # Today's Completed Orders
        # --------------------------------------

        cursor.execute("""

            SELECT COUNT(*) AS total

            FROM orders

            WHERE status='Completed'

            AND DATE(completed_at)=DATE('now')

        """)

        served_today = cursor.fetchone()["total"]

        # --------------------------------------
        # Today's Revenue
        # --------------------------------------

        cursor.execute("""

            SELECT

                IFNULL(SUM(total),0) AS revenue

            FROM orders

            WHERE status='Completed'

            AND DATE(completed_at)=DATE('now')

        """)

        revenue = cursor.fetchone()["revenue"]

        # --------------------------------------
        # Average Preparation Time
        # --------------------------------------

        cursor.execute("""

            SELECT

            AVG(

                JULIANDAY(completed_at)

                -

                JULIANDAY(created_at)

            ) * 24 * 60

            AS avg_time

            FROM orders

            WHERE

                completed_at IS NOT NULL

        """)

        avg = cursor.fetchone()["avg_time"]

        conn.close()

        return success(

            "Kitchen Dashboard Loaded",

            {

                "pending": pending,

                "preparing": preparing,

                "ready": ready,

                "served_today": served_today,

                "today_revenue": round(revenue,2),

                "average_preparation_time":

                round(avg or 0,2)

            }

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Kitchen Dashboard",

            500

        )
# ==========================================================
# CLEAN OLD COMPLETED ORDERS
# ==========================================================

@kitchen_bp.route(

    "/kitchen/cleanup",

    methods=["DELETE"]

)

def cleanup_completed_orders():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            DELETE FROM orders

            WHERE status='Completed'

            AND DATE(completed_at)

            < DATE('now','-30 day')

        """)

        deleted = cursor.rowcount

        conn.commit()

        conn.close()

        return success(

            f"{deleted} old orders removed"

        )

    except Exception as e:

        print(e)

        return error(

            "Cleanup Failed",

            500

        )
