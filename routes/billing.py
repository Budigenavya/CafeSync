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
import re
import json
import math

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


def validate_billing_totals(cursor, subtotal, gst, discount, total):
    prefs = cursor.execute("""
        SELECT tax_percentage, default_discount, maximum_discount, allow_manual_discount
        FROM settings WHERE id=1
    """).fetchone()
    if not prefs:
        return "Billing settings are missing."
    tax_rate = float(prefs["tax_percentage"] or 0)
    default_rate = float(prefs["default_discount"] or 0)
    max_rate = float(prefs["maximum_discount"] if prefs["maximum_discount"] is not None else 30)
    expected_gst = subtotal * tax_rate / 100
    if abs(gst - expected_gst) > 0.02:
        return "GST changed. Refresh the bill and try again."
    if bool(prefs["allow_manual_discount"]):
        if discount < -0.01 or discount > subtotal * max_rate / 100 + 0.02:
            return "Discount exceeds the configured maximum."
    elif abs(discount - subtotal * default_rate / 100) > 0.02:
        return "Manual discounts are disabled. Refresh the bill and try again."
    if abs(total - (subtotal + expected_gst - discount)) > 0.02:
        return "The bill total does not match its items and settings."
    return None


def validate_split_details(cursor, order_id, details, subtotal, gst, discount, total):
    if not isinstance(details, dict) or not isinstance(details.get("people"), list):
        return None, "Item split details are invalid."
    people = details["people"]
    if not 1 <= len(people) <= 30:
        return None, "A split bill must contain between 1 and 30 people."
    order_items = cursor.execute(
        "SELECT id, quantity, price FROM order_items WHERE order_id=? ORDER BY id", (order_id,)
    ).fetchall()
    if not order_items:
        return None, "Split order items are missing."

    assigned = [0] * len(order_items)
    subtotals = []
    normalized_people = []
    seen_people = set()
    for person in people:
        try:
            person_number = int(person["person_number"])
            amount = float(person["amount"])
            allocations = person["items"]
        except (KeyError, TypeError, ValueError):
            return None, "A split person entry is invalid."
        if person_number in seen_people or person_number < 1 or not math.isfinite(amount) or amount < 0 or not isinstance(allocations, list):
            return None, "A split person entry is invalid."
        seen_people.add(person_number)
        person_subtotal = 0.0
        normalized_items = []
        seen_lines = set()
        for allocation in allocations:
            try:
                line_index = int(allocation["line_index"])
                quantity = int(allocation["quantity"])
            except (KeyError, TypeError, ValueError):
                return None, "A split item quantity is invalid."
            if line_index < 0 or line_index >= len(order_items) or quantity <= 0 or line_index in seen_lines:
                return None, "A split item allocation is invalid."
            seen_lines.add(line_index)
            assigned[line_index] += quantity
            person_subtotal += float(order_items[line_index]["price"]) * quantity
            normalized_items.append({"line_index": line_index, "quantity": quantity})
        if person_subtotal <= 0:
            return None, "Each person must be assigned at least one item."
        subtotals.append(person_subtotal)
        normalized_people.append({"person_number": person_number, "amount": amount, "items": normalized_items})

    if any(assigned[index] != int(item["quantity"]) for index, item in enumerate(order_items)):
        return None, "Assign every order item quantity exactly once."
    if abs(sum(subtotals) - subtotal) > 0.02:
        return None, "Split item values do not match the order subtotal."

    expected_amounts = [round(value + (gst * value / subtotal if subtotal else 0) - (discount * value / subtotal if subtotal else 0), 2)
                        for value in subtotals]
    expected_total = round(total, 2)
    adjustment = round(expected_total - sum(expected_amounts), 2)
    expected_amounts[0] = round(expected_amounts[0] + adjustment, 2)
    for person, expected in zip(normalized_people, expected_amounts):
        if abs(person["amount"] - expected) > 0.02:
            return None, "A split share does not match its assigned items."
    if abs(sum(person["amount"] for person in normalized_people) - total) > 0.02:
        return None, "Split shares must add up to the order total."
    return {"people": normalized_people}, None


def held_order_payload(row):
    result = dict(row)
    result["items"] = json.loads(result.pop("items"))
    result["is_paid"] = bool(result["is_paid"])
    return result


@billing_bp.route("/held-orders", methods=["GET", "POST"])
def held_orders():
    if request.method == "GET":
        conn = get_connection()
        try:
            rows = conn.execute("SELECT * FROM held_orders ORDER BY created_at DESC, id DESC").fetchall()
            return jsonify({"success": True, "orders": [held_order_payload(row) for row in rows]})
        finally:
            conn.close()

    data = request.get_json(silent=True) or {}
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return jsonify({"success": False, "message": "A held order must include at least one item."}), 400
    try:
        for item in items:
            if not isinstance(item, dict) or int(item.get("id", 0)) <= 0 or int(item.get("quantity", 0)) <= 0:
                raise ValueError
            if not math.isfinite(float(item.get("price", 0))):
                raise ValueError
        table_value = data.get("table_id")
        table_id = int(table_value) if table_value not in (None, "") else None
        customer_value = data.get("customer_id")
        customer_id = int(customer_value) if customer_value not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Held order details are invalid."}), 400

    conn = get_connection()
    try:
        if customer_id is not None and not conn.execute("SELECT 1 FROM customers WHERE id=?", (customer_id,)).fetchone():
            return jsonify({"success": False, "message": "Selected customer no longer exists."}), 409
        cursor = conn.execute("""
            INSERT INTO held_orders(customer, customer_id, table_id, order_type, payment_method, is_paid, items)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ((data.get("customer") or "").strip(), customer_id, table_id,
              data.get("order_type") or "Dine In", data.get("payment_method") or "Cash",
              1 if data.get("is_paid") else 0, json.dumps(items)))
        row = conn.execute("SELECT * FROM held_orders WHERE id=?", (cursor.lastrowid,)).fetchone()
        conn.commit()
        return jsonify({"success": True, "order": held_order_payload(row)}), 201
    except Exception as error:
        conn.rollback()
        print("Could not hold order:", error)
        return jsonify({"success": False, "message": "Unable to hold this order."}), 500
    finally:
        conn.close()


@billing_bp.route("/held-orders/<int:order_id>", methods=["DELETE"])
def delete_held_order(order_id):
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM held_orders WHERE id=?", (order_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Held order not found."}), 404
        return jsonify({"success": True})
    finally:
        conn.close()


def get_or_create_customer(cursor, value):
    name_or_phone = (value or "").strip()
    if not name_or_phone or name_or_phone.lower() == "walk-in":
        return None

    digits = re.sub(r"\D", "", name_or_phone)
    phone = name_or_phone if len(digits) >= 7 else None
    if phone:
        existing = cursor.execute(
            "SELECT id FROM customers WHERE phone=?",
            (phone,)
        ).fetchone()
    else:
        existing = cursor.execute(
            "SELECT id FROM customers WHERE name=? COLLATE NOCASE",
            (name_or_phone,)
        ).fetchone()
    if existing:
        return existing["id"]

    cursor.execute(
        "INSERT INTO customers(name, phone) VALUES (?, ?)",
        (name_or_phone, phone)
    )
    return cursor.lastrowid


@billing_bp.route("/customers/search", methods=["GET"])
def search_customers():
    query = (request.args.get("q") or request.args.get("name") or "").strip()
    if len(query) < 2:
        return jsonify({"success": True, "customers": []})
    pattern = f"%{query}%"
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT c.id, c.name, c.phone, c.email, COALESCE(c.points, 0) AS points,
                   COUNT(DISTINCT o.id) AS visit_count,
                   COALESCE(SUM(CASE WHEN o.payment_status='Paid' THEN o.total ELSE 0 END), 0) AS paid_spend
            FROM customers c
            LEFT JOIN orders o ON o.customer_id=c.id AND o.status NOT IN ('Cancelled', 'Refunded')
            WHERE c.name LIKE ? COLLATE NOCASE OR c.phone LIKE ?
            GROUP BY c.id
            ORDER BY visit_count DESC, c.name COLLATE NOCASE
            LIMIT 8
        """, (pattern, pattern)).fetchall()
        return jsonify({"success": True, "customers": [dict(row) for row in rows]})
    finally:
        conn.close()


def resolve_item_addons(cursor, product_id, item):
    requested = item.get("addons") or []
    ids = []
    for addon in requested:
        addon_id = addon.get("id") if isinstance(addon, dict) else addon
        try:
            addon_id = int(addon_id)
        except (TypeError, ValueError):
            raise ValueError("An add-on selection is invalid.")
        if addon_id in ids:
            raise ValueError("The same add-on cannot be selected twice.")
        ids.append(addon_id)

    resolved = []
    for addon_id in ids:
        row = cursor.execute("""
            SELECT id, name, price
            FROM product_addons
            WHERE id=? AND product_id=? AND is_available=1
        """, (addon_id, product_id)).fetchone()
        if not row:
            raise ValueError("One of the selected add-ons is no longer available.")
        resolved.append({"id": row["id"], "name": row["name"], "price": float(row["price"])})
    return resolved

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


@billing_bp.route("/lookup", methods=["GET"])
def lookup_order():
    """Look up a saved bill or kitchen ticket by its printed number."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Enter a bill or KOT number."}), 400

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.bill_no, o.table_id, o.order_type, o.total,
               o.payment_method, o.payment_status, o.status, o.created_at,
               t.table_name
        FROM orders o
        LEFT JOIN tables t ON t.id=o.table_id
        WHERE UPPER(o.bill_no)=UPPER(?) OR CAST(o.id AS TEXT)=?
        ORDER BY o.id DESC LIMIT 1
    """, (query, query.lstrip("#")))
    order = cursor.fetchone()
    if not order:
        conn.close()
        return jsonify({"success": False, "message": "No matching bill or KOT was found."}), 404

    order_data = dict(order)
    order_data["items"] = [dict(row) for row in conn.execute("""
        SELECT p.name, oi.quantity, oi.price, oi.chef_note, oi.addons
        FROM order_items oi JOIN products p ON p.id=oi.product_id
        WHERE oi.order_id=? ORDER BY p.name
    """, (order_data["id"],)).fetchall()]
    conn.close()
    return jsonify({"success": True, "data": order_data})


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

        table_id = data.get("table_id") or None
        if table_id is not None:
            table_id = int(table_id)

        order_type = data.get("order_type")
        if not order_type:
            order_type = "Dine In" if table_id else data.get("table", "Take Away")

        payment_status = "Paid" if data.get("is_paid") else "Pending"

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

        selected_customer_id = data.get("customer_id")
        if selected_customer_id not in (None, ""):
            try:
                selected_customer_id = int(selected_customer_id)
            except (TypeError, ValueError):
                conn.close()
                return jsonify({"success": False, "message": "Selected customer is invalid."}), 400
            existing_customer = cursor.execute("SELECT id FROM customers WHERE id=?", (selected_customer_id,)).fetchone()
            if not existing_customer:
                conn.close()
                return jsonify({"success": False, "message": "Selected customer no longer exists."}), 409
            customer_id = selected_customer_id
        else:
            customer_id = get_or_create_customer(cursor, customer)

        bill_no = "INV" + datetime.now().strftime("%Y%m%d%H%M%S%f")

        cursor.execute("""

            INSERT INTO orders(

                bill_no,

                table_id,

                customer_id,

                order_type,

                subtotal,

                gst,

                discount,

                total,

                payment_method,

                payment_status,

                status

            )

            VALUES(

                ?,?,?,?,?,?,?,?,?,?,?

            )

        """, (

            bill_no,

            table_id,

            customer_id,

            order_type,

            subtotal,

            gst,

            discount,

            total,

            payment_method,

            payment_status,

            "Pending"

        ))

        order_id = cursor.lastrowid

        if payment_status == "Paid":
            cursor.execute("""
                INSERT INTO payments(order_id, payment_type, amount, payment_status)
                VALUES (?, ?, ?, 'Paid')
            """, (order_id, payment_method, total))

        # ======================================================
        # INSERT ORDER ITEMS
        # ======================================================

        calculated_subtotal = 0.0

        for item in items:

            product_id = item["id"]

            quantity = int(item["quantity"])
            if quantity <= 0:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": "Item quantity must be at least one."}), 400

            price = float(item["price"])

            # ----------------------------------------------
            # CHECK STOCK
            # ----------------------------------------------

            cursor.execute("""

                SELECT stock, is_available, price

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

            if not stock_row["is_available"]:
                conn.rollback()
                conn.close()
                return jsonify({
                    "success": False,
                    "message": "One of the selected items is no longer available."
                }), 409

            if current_stock < quantity:

                conn.rollback()

                conn.close()

                return jsonify({

                    "success": False,

                    "message": "Insufficient stock."

                })

            try:
                selected_addons = resolve_item_addons(cursor, product_id, item)
            except ValueError as addon_error:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": str(addon_error)}), 409
            unit_price = float(stock_row["price"]) + sum(addon["price"] for addon in selected_addons)
            calculated_subtotal += unit_price * quantity
            if abs(float(item.get("price", unit_price)) - unit_price) > 0.01:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": "The item or add-on price changed. Refresh the menu and try again."}), 409

            # ----------------------------------------------
            # INSERT ORDER ITEM
            # ----------------------------------------------

            cursor.execute("""

                INSERT INTO order_items(

                    order_id,

                    product_id,

                    quantity,

                    price,

                    chef_note,

                    addons

                )

                VALUES(

                    ?,?,?,?,?,?

                )

            """, (

                order_id,

                product_id,

                quantity,

                unit_price,

                str(item.get("chef_note") or "").strip()[:180],

                json.dumps(selected_addons, ensure_ascii=False)

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

        if abs(subtotal - calculated_subtotal) > 0.02:
            conn.rollback()
            conn.close()
            return jsonify({"success": False, "message": "The order total changed. Refresh the menu and review the bill."}), 409

        totals_error = validate_billing_totals(cursor, subtotal, gst, discount, total)
        if totals_error:
            conn.rollback()
            conn.close()
            return jsonify({"success": False, "message": totals_error}), 409

        split_details = data.get("split_details")
        if split_details is not None:
            normalized_split, split_error = validate_split_details(
                cursor, order_id, split_details, subtotal, gst, discount, total
            )
            if split_error:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": split_error}), 400
            cursor.execute("UPDATE orders SET split_details=? WHERE id=?", (json.dumps(normalized_split), order_id))

        if table_id:
            cursor.execute("UPDATE tables SET status='Occupied' WHERE id=?", (table_id,))

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

                order_items.chef_note,

                order_items.addons,

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

@billing_bp.route("/split-payment/<int:order_id>", methods=["POST"])
def record_split_payments(order_id):
    data = request.get_json(silent=True) or {}
    shares = data.get("shares") or []
    if not isinstance(shares, list):
        return jsonify({"success": False, "message": "Split payment details are invalid."}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("""
            SELECT total, payment_status, status, split_details FROM orders WHERE id=?
        """, (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[2] in ("Cancelled", "Refunded") or order[1] in ("Refunded",):
            return jsonify({"success": False, "message": "This order cannot accept payments."}), 409
        if not order[3]:
            return jsonify({"success": False, "message": "Saved item split details were not found."}), 409
        split_people = {str(person["person_number"]): float(person["amount"])
                        for person in json.loads(order[3]).get("people", [])}

        paid = float(cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments
            WHERE order_id=? AND payment_status='Paid'
        """, (order_id,)).fetchone()[0] or 0)
        total = float(order[0] or 0)
        remaining = max(0, total - paid)
        normalized = []
        person_paid = {}
        for share in shares:
            if not isinstance(share, dict):
                return jsonify({"success": False, "message": "A split share is invalid."}), 400
            amount = float(share.get("amount", 0))
            raw_method = share.get("payment_type") or "Cash"
            if not isinstance(raw_method, str):
                return jsonify({"success": False, "message": "A payment method is invalid."}), 400
            method = raw_method.strip()
            if not math.isfinite(amount) or amount <= 0 or method not in {"Cash", "Card", "Other", "UPI", "Wallet", "Paytm EDC"}:
                return jsonify({"success": False, "message": "A split share has an invalid amount or payment method."}), 400
            person_number = str(share.get("person_number", ""))
            if person_number not in split_people:
                return jsonify({"success": False, "message": "A split payment does not match a saved person."}), 400
            if person_number in person_paid:
                return jsonify({"success": False, "message": "A person can be paid only once in this split."}), 400
            already_paid = float(cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE order_id=? AND split_person=? AND payment_status='Paid'
            """, (order_id, person_number)).fetchone()[0] or 0)
            if amount > split_people[person_number] - already_paid + 0.02:
                return jsonify({"success": False, "message": "A payment exceeds that person's share."}), 409
            person_paid[person_number] = amount
            normalized.append((method, amount, person_number))
        amount_to_record = sum(amount for _, amount, _ in normalized)
        if amount_to_record > remaining + 0.02:
            return jsonify({"success": False, "message": "Split payments exceed the unpaid balance."}), 409

        for method, amount, person_number in normalized:
            cursor.execute("""
                INSERT INTO payments(order_id, payment_type, amount, payment_status, split_person)
                VALUES (?, ?, ?, 'Paid', ?)
            """, (order_id, method, amount, person_number))

        paid += amount_to_record
        new_status = "Paid" if paid >= total - 0.02 else "Partial"
        methods = {method for method, _, _ in normalized}
        payment_method = next(iter(methods)) if len(methods) == 1 and not order[1] == "Partial" else "Split"
        cursor.execute("""
            UPDATE orders SET payment_status=?, payment_method=? WHERE id=?
        """, (new_status, payment_method, order_id))
        conn.commit()
        return jsonify({"success": True, "payment_status": new_status,
                        "paid": round(paid, 2), "remaining": round(max(0, total - paid), 2)})
    except (TypeError, ValueError) as error:
        conn.rollback()
        return jsonify({"success": False, "message": "Split payment amounts must be valid numbers."}), 400
    except Exception as error:
        conn.rollback()
        print("Split payment failed:", error)
        return jsonify({"success": False, "message": "Unable to record split payments."}), 500
    finally:
        conn.close()

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

                order_items.price,

                order_items.chef_note,

                order_items.addons

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

        selected_customer_id = data.get("customer_id")
        if selected_customer_id not in (None, ""):
            try:
                selected_customer_id = int(selected_customer_id)
            except (TypeError, ValueError):
                conn.close()
                return jsonify({"success": False, "message": "Selected customer is invalid."}), 400
            if not cursor.execute("SELECT 1 FROM customers WHERE id=?", (selected_customer_id,)).fetchone():
                conn.close()
                return jsonify({"success": False, "message": "Selected customer no longer exists."}), 409
            customer_id = selected_customer_id
        else:
            customer_id = get_or_create_customer(cursor, data.get("customer_name", ""))

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
                payment_status,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bill_no,
            table_id,
            customer_id,
            order_type,
            subtotal,
            gst,
            discount,
            total,
            payment_method,
            "Pending",
            "Pending"
        ))

        order_id = cursor.lastrowid

        print("🔥 ORDER CREATED:", order_id)

        # ==============================
        # CREATE ORDER ITEMS
        # ==============================

        calculated_subtotal = 0.0

        for item in items:

            print("🔥 PROCESSING ITEM:", item)

            product_id = int(item["product_id"])

            quantity = int(
                item.get("quantity", 1)
            )
            if quantity <= 0:
                conn.rollback()
                return jsonify({"success": False, "message": "Item quantity must be at least one."}), 400

            price = float(
                item.get("price", 0)
            )

            product = conn.execute(
                "SELECT stock, is_available, price FROM products WHERE id=?",
                (product_id,)
            ).fetchone()
            if not product:
                conn.rollback()
                return jsonify({"success": False, "message": "A selected menu item no longer exists."}), 409
            if not product["is_available"]:
                conn.rollback()
                return jsonify({"success": False, "message": "One of the selected items is no longer available."}), 409
            if product["stock"] < quantity:
                conn.rollback()
                return jsonify({"success": False, "message": "Insufficient stock for a selected item."}), 409

            try:
                selected_addons = resolve_item_addons(cursor, product_id, item)
            except ValueError as addon_error:
                conn.rollback()
                return jsonify({"success": False, "message": str(addon_error)}), 409
            unit_price = float(product["price"]) + sum(addon["price"] for addon in selected_addons)
            calculated_subtotal += unit_price * quantity
            if abs(float(item.get("price", unit_price)) - unit_price) > 0.01:
                conn.rollback()
                return jsonify({"success": False, "message": "The item or add-on price changed. Refresh the menu and try again."}), 409

            cursor.execute("""
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    quantity,
                    price,
                    chef_note,
                    addons
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                product_id,
                quantity,
                unit_price,
                str(item.get("chef_note") or "").strip()[:180],
                json.dumps(selected_addons, ensure_ascii=False)
            ))

            cursor.execute("UPDATE products SET stock=stock-? WHERE id=?", (quantity, product_id))
            cursor.execute("""
                INSERT INTO inventory_logs(product_id, quantity, action, remarks)
                VALUES (?, ?, 'SALE', ?)
            """, (product_id, quantity, f"Kitchen ticket {bill_no}"))

        # ==============================
        # SAVE
        # ==============================

        if abs(subtotal - calculated_subtotal) > 0.02:
            conn.rollback()
            return jsonify({"success": False, "message": "The order total changed. Refresh the menu and review the ticket."}), 409

        totals_error = validate_billing_totals(cursor, subtotal, gst, discount, total)
        if totals_error:
            conn.rollback()
            return jsonify({"success": False, "message": totals_error}), 409

        if table_id:
            cursor.execute("UPDATE tables SET status='Occupied' WHERE id=?", (table_id,))

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


