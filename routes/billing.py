"""
==========================================================
                CafeSync POS
                billing.py
                PART 1
==========================================================
"""

from flask import (
    Blueprint,
    jsonify,
    request,
    render_template
)

from database import get_connection
from routes.auth import login_required

import sqlite3

from datetime import datetime



# ==========================================================
# BLUEPRINT
# ==========================================================

billing_bp = Blueprint(
    "billing",
    __name__,
    url_prefix="/billing"
)

print("🔥 BILLING BLUEPRINT CREATED")
print("🔥 BILLING FILE:", __file__)

# ==========================================================
# HELPER
# ==========================================================

def dict_from_row(row):

    return dict(zip(row.keys(), row))

@billing_bp.route("/")
@login_required
def billing():

    return render_template("billing.html")


# ==========================================================
# GET PRODUCTS
# ==========================================================

@billing_bp.route("/products", methods=["GET"])
def get_products():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                products.id,

                products.name,

                products.price,

                products.stock,

                products.image,

                products.barcode,

                categories.name AS category_name

            FROM products

            LEFT JOIN categories

            ON products.category_id = categories.id

            ORDER BY products.name

        """)

        rows = cursor.fetchall()

        conn.close()

        products = []

        for row in rows:

            products.append(dict_from_row(row))

        return jsonify({

            "success": True,

            "products": products

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# CREATE ORDER
# ==========================================================

@billing_bp.route("/create-order", methods=["POST"])
def create_order():

    try:

        data = request.get_json()

        items = data.get("items", [])

        subtotal = float(data.get("subtotal", 0))
        gst = float(data.get("gst", 0))
        discount = float(data.get("discount", 0))
        total = float(data.get("total", 0))

        payment_method = data.get(
            "payment_method",
            "Cash"
        )

        table = data.get(
            "table",
            "Take Away"
        )

        customer = data.get(
            "customer",
            "Walk-in"
        )

        if len(items) == 0:

            return jsonify({

                "success": False,

                "message": "Cart Empty"

            })

        conn = get_connection()

        cursor = conn.cursor()

        bill_no = "INV" + datetime.now().strftime("%Y%m%d%H%M%S")

        cursor.execute("""

            INSERT INTO orders(

                bill_no,

                order_type,

                subtotal,

                gst,

                discount,

                total,

                payment_method,

                status

            )

            VALUES(

                ?,?,?,?,?,?,?,?

            )

        """, (

            bill_no,

            table,

            subtotal,

            gst,

            discount,

            total,

            payment_method,

            "Pending"

        ))

        order_id = cursor.lastrowid
        # ======================================================
        # INSERT ORDER ITEMS
        # ======================================================

        for item in items:

            product_id = item["id"]

            quantity = int(item["quantity"])

            price = float(item["price"])

            # ----------------------------------------------
            # CHECK STOCK
            # ----------------------------------------------

            cursor.execute("""

                SELECT stock

                FROM products

                WHERE id = ?

            """, (product_id,))

            stock_row = cursor.fetchone()

            if stock_row is None:

                conn.rollback()

                conn.close()

                return jsonify({

                    "success": False,

                    "message": f"Product {product_id} not found."

                })

            current_stock = stock_row["stock"]

            if current_stock < quantity:

                conn.rollback()

                conn.close()

                return jsonify({

                    "success": False,

                    "message": "Insufficient stock."

                })

            # ----------------------------------------------
            # INSERT ORDER ITEM
            # ----------------------------------------------

            cursor.execute("""

                INSERT INTO order_items(

                    order_id,

                    product_id,

                    quantity,

                    price

                )

                VALUES(

                    ?,?,?,?

                )

            """, (

                order_id,

                product_id,

                quantity,

                price

            ))

            # ----------------------------------------------
            # UPDATE STOCK
            # ----------------------------------------------

            cursor.execute("""

                UPDATE products

                SET stock = stock - ?

                WHERE id = ?

            """, (

                quantity,

                product_id

            ))

            # ----------------------------------------------
            # INVENTORY LOG
            # ----------------------------------------------

            cursor.execute("""

                INSERT INTO inventory_logs(

                    product_id,

                    quantity,

                    action

                )

                VALUES(

                    ?,?,'SALE'

                )

            """, (

                product_id,

                quantity

            ))

        # ======================================================
        # COMMIT
        # ======================================================

        conn.commit()

        conn.close()

        return jsonify({

            "success": True,

            "message": "Order Created Successfully",

            "order_id": order_id,

            "bill_no": bill_no

        })

    except sqlite3.Error as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500
# ==========================================================
# GET ALL ORDERS
# ==========================================================

@billing_bp.route("/orders", methods=["GET"])
def get_orders():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            ORDER BY created_at DESC

        """)

        rows = cursor.fetchall()

        conn.close()

        orders = []

        for row in rows:

            orders.append(dict_from_row(row))

        return jsonify({

            "success": True,

            "orders": orders

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# GET SINGLE ORDER
# ==========================================================

@billing_bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE id = ?

        """, (order_id,))

        order = cursor.fetchone()

        if order is None:

            conn.close()

            return jsonify({

                "success": False,

                "message": "Order not found"

            }),404

        cursor.execute("""

            SELECT

                order_items.id,

                order_items.quantity,

                order_items.price,

                products.name

            FROM order_items

            JOIN products

            ON products.id = order_items.product_id

            WHERE order_items.order_id = ?

        """, (order_id,))

        items = cursor.fetchall()

        conn.close()

        return jsonify({

            "success": True,

            "order": dict_from_row(order),

            "items": [dict_from_row(i) for i in items]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }),500


# ==========================================================
# HOLD ORDER
# ==========================================================

@billing_bp.route("/hold/<int:order_id>", methods=["PUT"])
def hold_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Hold'

            WHERE id=?

        """,(order_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Held"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# RESUME ORDER
# ==========================================================

@billing_bp.route("/resume/<int:order_id>", methods=["PUT"])
def resume_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Pending'

            WHERE id=?

        """,(order_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Resumed"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# CANCEL ORDER
# ==========================================================

@billing_bp.route("/cancel/<int:order_id>", methods=["PUT"])
def cancel_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                product_id,

                quantity

            FROM order_items

            WHERE order_id=?

        """,(order_id,))

        items = cursor.fetchall()

        for item in items:

            cursor.execute("""

                UPDATE products

                SET stock = stock + ?

                WHERE id = ?

            """,(

                item["quantity"],

                item["product_id"]

            ))

        cursor.execute("""

            UPDATE orders

            SET status='Cancelled'

            WHERE id=?

        """,(order_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Cancelled"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500
# ==========================================================
# COMPLETE ORDER
# ==========================================================

@billing_bp.route("/complete/<int:order_id>", methods=["PUT"])
def complete_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Completed'

            WHERE id=?

        """, (order_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success": True,

            "message": "Order Completed"

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }),500


# ==========================================================
# PAYMENT
# ==========================================================

@billing_bp.route("/payment/<int:order_id>", methods=["POST"])
def make_payment(order_id):

    try:

        data = request.get_json()

        payment_type = data.get("payment_type","Cash")

        amount = float(data.get("amount",0))

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            INSERT INTO payments(

                order_id,

                payment_type,

                amount

            )

            VALUES(

                ?,?,?

            )

        """,(

            order_id,

            payment_type,

            amount

        ))

        cursor.execute("""

            UPDATE orders

            SET status='Paid'

            WHERE id=?

        """,(order_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Payment Successful"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# TODAY SALES
# ==========================================================

@billing_bp.route("/today-sales", methods=["GET"])
def today_sales():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) as orders,

                IFNULL(SUM(total),0) as revenue

            FROM orders

            WHERE DATE(created_at)=DATE('now')

            AND status IN ('Completed','Paid')

        """)

        row = cursor.fetchone()

        conn.close()

        return jsonify({

            "success":True,

            "orders":row["orders"],

            "revenue":row["revenue"]

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# DASHBOARD STATS
# ==========================================================

@billing_bp.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        stats = {}

        cursor.execute("""

            SELECT COUNT(*)

            FROM orders

        """)

        stats["orders"] = cursor.fetchone()[0]

        cursor.execute("""

            SELECT COUNT(*)

            FROM products

        """)

        stats["products"] = cursor.fetchone()[0]

        cursor.execute("""

            SELECT COUNT(*)

            FROM customers

        """)

        stats["customers"] = cursor.fetchone()[0]

        cursor.execute("""

            SELECT IFNULL(SUM(total),0)

            FROM orders

            WHERE status IN ('Completed','Paid')

        """)

        stats["sales"] = cursor.fetchone()[0]

        conn.close()

        return jsonify({

            "success":True,

            "stats":stats

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# TOP SELLING PRODUCTS
# ==========================================================

@billing_bp.route("/top-products", methods=["GET"])
def top_products():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                products.name,

                SUM(order_items.quantity) AS sold

            FROM order_items

            JOIN products

            ON products.id = order_items.product_id

            GROUP BY products.id

            ORDER BY sold DESC

            LIMIT 10

        """)

        rows = cursor.fetchall()

        conn.close()

        return jsonify({

            "success":True,

            "products":[dict_from_row(r) for r in rows]

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# CUSTOMER HISTORY
# ==========================================================

@billing_bp.route("/customer-history/<string:name>", methods=["GET"])
def customer_history(name):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE customer_id IN(

                SELECT id

                FROM customers

                WHERE name=?

            )

            ORDER BY created_at DESC

        """,(name,))

        rows = cursor.fetchall()

        conn.close()

        return jsonify({

            "success":True,

            "orders":[dict_from_row(r) for r in rows]

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500
# ==========================================================
# SEARCH BILL
# ==========================================================

@billing_bp.route("/search", methods=["GET"])
def search_bill():

    try:

        keyword = request.args.get("q", "")

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE bill_no LIKE ?

            ORDER BY created_at DESC

        """, (f"%{keyword}%",))

        rows = cursor.fetchall()

        conn.close()

        return jsonify({

            "success": True,

            "orders": [dict_from_row(r) for r in rows]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# DELETE ORDER
# ==========================================================

@billing_bp.route("/delete/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        # Restore stock
        cursor.execute("""

            SELECT product_id, quantity

            FROM order_items

            WHERE order_id = ?

        """, (order_id,))

        items = cursor.fetchall()

        for item in items:

            cursor.execute("""

                UPDATE products

                SET stock = stock + ?

                WHERE id = ?

            """, (

                item["quantity"],

                item["product_id"]

            ))

        cursor.execute("""

            DELETE FROM order_items

            WHERE order_id = ?

        """, (order_id,))

        cursor.execute("""

            DELETE FROM payments

            WHERE order_id = ?

        """, (order_id,))

        cursor.execute("""

            DELETE FROM orders

            WHERE id = ?

        """, (order_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success": True,

            "message": "Order Deleted Successfully"

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# REFUND ORDER
# ==========================================================

@billing_bp.route("/refund/<int:order_id>", methods=["PUT"])
def refund_order(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Refunded'

            WHERE id = ?

        """, (order_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success": True,

            "message": "Refund Completed"

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# SALES REPORT
# ==========================================================

@billing_bp.route("/sales-report", methods=["GET"])
def sales_report():

    try:

        start = request.args.get("start")
        end = request.args.get("end")

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE DATE(created_at)

            BETWEEN ? AND ?

            ORDER BY created_at DESC

        """, (

            start,

            end

        ))

        rows = cursor.fetchall()

        conn.close()

        return jsonify({

            "success": True,

            "orders": [dict_from_row(r) for r in rows]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# PRINT RECEIPT DATA
# ==========================================================

@billing_bp.route("/receipt/<int:order_id>", methods=["GET"])
def receipt(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE id = ?

        """, (order_id,))

        order = cursor.fetchone()

        cursor.execute("""

            SELECT

                products.name,

                order_items.quantity,

                order_items.price

            FROM order_items

            JOIN products

            ON products.id = order_items.product_id

            WHERE order_items.order_id = ?

        """, (order_id,))

        items = cursor.fetchall()

        conn.close()

        return jsonify({

            "success": True,

            "order": dict_from_row(order),

            "items": [dict_from_row(i) for i in items]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# KITCHEN ORDERS
# ==========================================================

@billing_bp.route("/kot", methods=["POST"])
@login_required
def create_kot():

    conn = None

    try:
        data = request.get_json()

        print("🔥 KOT DATA:", data)

        if not data:
            return jsonify({
                "success": False,
                "message": "No order data received"
            }), 400

        items = data.get("items", [])

        print("🔥 KOT ITEMS:", items)

        if not items:
            return jsonify({
                "success": False,
                "message": "No items in order"
            }), 400

        # ==============================
        # ORDER DETAILS
        # ==============================

        table_id = data.get("table_id")

        if table_id in ("", None):
            table_id = None
        else:
            table_id = int(table_id)

        order_type = data.get("order_type", "Dine In")

        subtotal = float(data.get("subtotal", 0))
        gst = float(data.get("gst", 0))
        discount = float(data.get("discount", 0))
        total = float(data.get("total", 0))

        payment_method = data.get(
            "payment_method",
            "Pending"
        )

        # ==============================
        # DATABASE
        # ==============================

        conn = get_connection()
        cursor = conn.cursor()

        # ==============================
        # BILL NUMBER
        # ==============================

        cursor.execute("""
            SELECT COUNT(*) + 1
            FROM orders
        """)

        count = cursor.fetchone()[0]

        bill_no = f"KOT-{count:05d}"

        print("🔥 BILL NO:", bill_no)

        # ==============================
        # CREATE ORDER
        # ==============================

        cursor.execute("""
            INSERT INTO orders (
                bill_no,
                table_id,
                customer_id,
                order_type,
                subtotal,
                gst,
                discount,
                total,
                payment_method,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bill_no,
            table_id,
            None,
            order_type,
            subtotal,
            gst,
            discount,
            total,
            payment_method,
            "Pending"
        ))

        order_id = cursor.lastrowid

        print("🔥 ORDER CREATED:", order_id)

        # ==============================
        # CREATE ORDER ITEMS
        # ==============================

        for item in items:

            print("🔥 PROCESSING ITEM:", item)

            product_id = int(item["product_id"])

            quantity = int(
                item.get("quantity", 1)
            )

            price = float(
                item.get("price", 0)
            )

            cursor.execute("""
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    quantity,
                    price
                )
                VALUES (?, ?, ?, ?)
            """, (
                order_id,
                product_id,
                quantity,
                price
            ))

        # ==============================
        # SAVE
        # ==============================

        conn.commit()

        print(
            "🔥🔥 KOT CREATED SUCCESSFULLY:",
            order_id,
            bill_no
        )

        return jsonify({
            "success": True,
            "message": "Kitchen Order Created",
            "data": {
                "order_id": order_id,
                "bill_no": bill_no
            }
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("\n🔥🔥🔥 KOT ERROR 🔥🔥🔥")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("🔥🔥🔥 END KOT ERROR 🔥🔥🔥\n")

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()

print("🔥🔥 CREATE KOT ROUTE DEFINED 🔥🔥")

# ==========================================================
# UPDATE ORDER STATUS
# ==========================================================

@billing_bp.route("/status/<int:order_id>", methods=["PUT"])
def update_status(order_id):

    try:

        status = request.get_json().get("status")

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status = ?

            WHERE id = ?

        """, (

            status,

            order_id

        ))

        conn.commit()

        conn.close()

        return jsonify({

            "success": True,

            "message": "Status Updated"

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500

print("🔥🔥 BILLING.PY LOADED 🔥🔥")


