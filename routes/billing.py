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
    render_template,
    render_template_string,
    send_file,
    current_app,
    url_for,
    session
)

from database import get_connection
from routes.auth import login_required

import sqlite3
import re
import json
import math
import secrets
from io import BytesIO

from datetime import datetime



# ==========================================================
# BLUEPRINT
# ==========================================================

billing_bp = Blueprint(
    "billing",
    __name__,
    url_prefix="/billing"
)

print(" BILLING BLUEPRINT CREATED")
print(" BILLING FILE:", __file__)

# ==========================================================
# HELPER
# ==========================================================

def dict_from_row(row):
    # sqlite3.Row and the PostgreSQL HybridRow both expose a mapping interface.
    # Iterating a mapping yields its keys, so zipping row.keys() with row
    # silently produced {column: column} for PostgreSQL results.
    return dict(row)


def invoice_payload(conn, order_id):
    order = conn.execute("""
        SELECT o.*, c.name AS customer_name, c.phone AS customer_phone,
               t.table_name AS table_name
        FROM orders o
        LEFT JOIN customers c ON c.id=o.customer_id
        LEFT JOIN tables t ON t.id=o.table_id
        WHERE o.id=?
    """, (order_id,)).fetchone()
    if not order:
        return None
    items = conn.execute("""
        SELECT p.name, oi.quantity, oi.price, oi.chef_note, oi.addons
        FROM order_items oi
        LEFT JOIN products p ON p.id=oi.product_id
        WHERE oi.order_id=? ORDER BY oi.id
    """, (order_id,)).fetchall()
    item_data = []
    for row in items:
        item = dict(row)
        item["name"] = item.get("name") or "Deleted menu item"
        item["quantity"] = int(item.get("quantity") or 0)
        item["price"] = float(item.get("price") or 0)
        item["total"] = round(item["price"] * item["quantity"], 2)
        item_data.append(item)
    data = dict(order)
    data["items"] = item_data
    data["customer"] = {
        "name": data.pop("customer_name", None) or "Walk-in Customer",
        "phone": data.pop("customer_phone", None) or ""
    }
    data["invoice_date"] = data.get("created_at") or ""
    data["summary"] = {
        "subtotal": float(data.get("subtotal") or 0),
        "gst": float(data.get("gst") or 0),
        "discount": float(data.get("discount") or 0),
        "grand_total": float(data.get("total") or 0)
    }
    return data


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

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Held order details are invalid."}), 400
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
            product = dict_from_row(row)
            product["image_url"] = url_for("inventory.product_image", filename=product["image"]) if product.get("image") else None
            try:
                product["is_billable"] = math.isfinite(float(product.get("price")))
            except (TypeError, ValueError):
                product["is_billable"] = False
            products.append(product)

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
    conn = None
    error_id = secrets.token_hex(4)
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "message": "Order details were missing or invalid. Refresh the POS and try again."}), 400

        items = data.get("items", [])
        if not isinstance(items, list):
            return jsonify({"success": False, "message": "Order items were invalid. Refresh the POS and try again."}), 400

        try:
            subtotal = float(data.get("subtotal", 0))
            gst = float(data.get("gst", 0))
            discount = float(data.get("discount", 0))
            total = float(data.get("total", 0))
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Bill totals must be valid amounts."}), 400
        if not all(math.isfinite(value) for value in (subtotal, gst, discount, total)) or min(subtotal, gst, discount, total) < 0:
            return jsonify({"success": False, "message": "Bill totals must be valid non-negative amounts."}), 400

        payment_method = data.get(
            "payment_method",
            "Cash"
        )
        if not isinstance(payment_method, str) or payment_method.strip() not in {"Cash", "Card", "Other", "UPI", "Wallet", "Paytm EDC", "Split"}:
            return jsonify({"success": False, "message": "Choose a valid payment method."}), 400
        payment_method = payment_method.strip()
        is_paid = data.get("is_paid", False)
        if not isinstance(is_paid, bool):
            return jsonify({"success": False, "message": "Payment status must be selected explicitly."}), 400
        if is_paid and payment_method == "Split":
            return jsonify({"success": False, "message": "Record split payments using the split payment flow."}), 400

        table_value = data.get("table_id")
        if table_value in (None, ""):
            table_id = None
        else:
            try:
                table_id = int(table_value)
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": "Choose a valid table."}), 400
            if table_id <= 0:
                return jsonify({"success": False, "message": "Choose a valid table."}), 400

        order_type = data.get("order_type")
        if not order_type:
            order_type = "Dine In" if table_id else data.get("table", "Take Away")
        if not isinstance(order_type, str) or order_type not in {"Dine In", "Parcel", "Delivery", "Take Away"}:
            return jsonify({"success": False, "message": "Choose a valid order type."}), 400

        order_source = data.get("order_source", "Cafe")
        if not isinstance(order_source, str) or order_source not in {"Cafe", "Swiggy", "Zomato"}:
            return jsonify({"success": False, "message": "Choose a valid order source."}), 400
        if order_source in {"Swiggy", "Zomato"} and order_type != "Delivery":
            return jsonify({"success": False, "message": "Swiggy and Zomato orders must use Delivery order type."}), 400
        order_status = "Pending" if order_type == "Delivery" and order_source in {"Swiggy", "Zomato"} else "Completed"

        payment_status = "Paid" if is_paid else "Pending"

        customer = data.get(
            "customer",
            "Walk-in"
        )
        if customer is not None and not isinstance(customer, str):
            return jsonify({"success": False, "message": "Customer name or phone must be text."}), 400

        if len(items) == 0:

            return jsonify({

                "success": False,

                "message": "Cart Empty"

            }), 400

        conn = get_connection()

        cursor = conn.cursor()

        if table_id is not None:
            selected_table = cursor.execute("SELECT status FROM tables WHERE id=?", (table_id,)).fetchone()
            if not selected_table:
                conn.close()
                return jsonify({"success": False, "message": "The selected table no longer exists."}), 409
            if selected_table[0] not in ("Available", "Occupied"):
                conn.close()
                return jsonify({"success": False, "message": "The selected table is not available for a new order."}), 409

        ingredient_demand = {}
        for cart_item in items:
            try:
                recipe_product_id = int(cart_item.get("id"))
                recipe_quantity = int(cart_item.get("quantity"))
            except (TypeError, ValueError, AttributeError):
                conn.close()
                return jsonify({"success": False, "message": "An order item has invalid details."}), 400
            if recipe_product_id <= 0 or recipe_quantity <= 0:
                conn.close()
                return jsonify({"success": False, "message": "An order item has invalid details."}), 400
            for recipe in cursor.execute("SELECT ingredient_id, quantity FROM recipes WHERE product_id=?", (recipe_product_id,)).fetchall():
                ingredient_demand[recipe[0]] = ingredient_demand.get(recipe[0], 0) + float(recipe[1]) * recipe_quantity
        for ingredient_id, required_quantity in ingredient_demand.items():
            available = cursor.execute("SELECT name, current_stock FROM ingredients WHERE id=? AND active=1", (ingredient_id,)).fetchone()
            if not available or float(available["current_stock"]) + 1e-9 < required_quantity:
                conn.close()
                label = available["name"] if available else "recipe ingredient"
                return jsonify({"success": False, "message": f"Insufficient ingredient stock: {label}."}), 409

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

                order_source,

                subtotal,

                gst,

                discount,

                total,

                payment_method,

                payment_status,

                status

            )

            VALUES(

                ?,?,?,?,?,?,?,?,?,?,?,?

            )

        """, (

            bill_no,

            table_id,

            customer_id,

            order_type,

            order_source,

            subtotal,

            gst,

            discount,

            total,

            payment_method,

            payment_status,

            order_status

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
            if not isinstance(item, dict):
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": "An order item is invalid."}), 400
            try:
                product_id = int(item["id"])
                quantity = int(item["quantity"])
                price = float(item["price"])
            except (KeyError, TypeError, ValueError):
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": "An order item has invalid details."}), 400
            if product_id <= 0 or not math.isfinite(price) or price < 0:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": "An order item has invalid details."}), 400

            if quantity <= 0:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "message": "Item quantity must be at least one."}), 400

            # ----------------------------------------------
            # CHECK STOCK
            # ----------------------------------------------

            cursor.execute("""

                SELECT stock, stock_unlimited, is_available, price

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

                }), 409

            current_stock = int(stock_row["stock"] or 0)

            if not stock_row["is_available"]:
                conn.rollback()
                conn.close()
                return jsonify({
                    "success": False,
                    "message": "One of the selected items is no longer available."
                }), 409

            if not stock_row["stock_unlimited"] and current_stock < quantity:

                conn.rollback()

                conn.close()

                return jsonify({

                    "success": False,

                    "message": "Insufficient stock."

                }), 409

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

            if not stock_row["stock_unlimited"]:
                cursor.execute("UPDATE products SET stock=stock-? WHERE id=?", (quantity, product_id))
                cursor.execute("INSERT INTO inventory_logs(product_id,quantity,action) VALUES(?,?,'SALE')",
                               (product_id, quantity))

            recipe_rows = cursor.execute(
                "SELECT ingredient_id, quantity FROM recipes WHERE product_id=?",
                (product_id,)
            ).fetchall()
            for recipe in recipe_rows:
                used = float(recipe["quantity"]) * quantity
                cursor.execute("UPDATE ingredients SET current_stock=current_stock-? WHERE id=?", (used, recipe["ingredient_id"]))
                cursor.execute("""
                    INSERT INTO ingredient_movements(ingredient_id,quantity_change,movement_type,reference,order_id,actor)
                    VALUES(?,?,'SALE',?,?,?)
                """, (recipe["ingredient_id"], -used, bill_no, order_id, session.get("username", "")))

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

        cursor.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                       (session.get("username", ""), "order_created", "order", str(order_id),
                        json.dumps({"bill_no": bill_no, "total": total, "status": order_status,
                                    "order_type": order_type, "order_source": order_source})))

        conn.commit()

        conn.close()

        return jsonify({

            "success": True,

            "message": "Order Created Successfully",

            "order_id": order_id,

            "bill_no": bill_no

        })

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
                conn.close()
            except sqlite3.Error:
                pass
        current_app.logger.exception("Order creation failed (reference %s)", error_id)
        return jsonify({
            "success": False,
            "message": "Order could not be saved. Please retry and share the error reference with support if it happens again.",
            "error_id": error_id
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
    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("SELECT status, payment_status FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[0] in ("Cancelled", "Refunded", "Completed") or order[1] == "Paid":
            return jsonify({"success": False, "message": "This order cannot be put on hold."}), 409
        cursor.execute("UPDATE orders SET status='Hold' WHERE id=?", (order_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Order held."})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not hold order %s", order_id)
        return jsonify({"success": False, "message": "Unable to hold this order."}), 500
    finally:
        conn.close()


# ==========================================================
# RESUME ORDER
# ==========================================================

@billing_bp.route("/resume/<int:order_id>", methods=["PUT"])
def resume_order(order_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[0] != "Hold":
            return jsonify({"success": False, "message": "Only held orders can be resumed."}), 409
        cursor.execute("UPDATE orders SET status='Pending' WHERE id=?", (order_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Order resumed."})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not resume order %s", order_id)
        return jsonify({"success": False, "message": "Unable to resume this order."}), 500
    finally:
        conn.close()


# ==========================================================
# CANCEL ORDER
# ==========================================================

@billing_bp.route("/cancel/<int:order_id>", methods=["PUT"])
def cancel_order(order_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("SELECT status, payment_status, table_id FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[0] in ("Cancelled", "Refunded", "Served", "Completed"):
            return jsonify({"success": False, "message": "This order is already closed."}), 409
        if order[1] in ("Paid", "Partial"):
            return jsonify({"success": False, "message": "Paid orders must be refunded instead of cancelled."}), 409
        items = cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall()
        for item in items:
            cursor.execute("UPDATE products SET stock=stock+? WHERE id=? AND stock_unlimited=0", (item["quantity"], item["product_id"]))
            if cursor.rowcount:
                cursor.execute("INSERT INTO inventory_logs(product_id, quantity, action, remarks) VALUES (?, ?, 'CANCEL', ?)",
                               (item["product_id"], item["quantity"], f"Cancelled order {order_id}"))
        ingredient_sales = cursor.execute("""
            SELECT ingredient_id, -SUM(quantity_change) AS quantity
            FROM ingredient_movements WHERE order_id=? AND movement_type='SALE'
            GROUP BY ingredient_id
        """, (order_id,)).fetchall()
        for movement in ingredient_sales:
            cursor.execute("UPDATE ingredients SET current_stock=current_stock+? WHERE id=?", (movement["quantity"], movement["ingredient_id"]))
            cursor.execute("INSERT INTO ingredient_movements(ingredient_id,quantity_change,movement_type,reference,order_id,actor) VALUES(?,?,'CANCEL',?,?,?)",
                           (movement["ingredient_id"], movement["quantity"], f"Cancelled order {order_id}", order_id, session.get("username", "")))
        cursor.execute("UPDATE orders SET status='Cancelled', payment_status='Cancelled', cancelled_at=CURRENT_TIMESTAMP WHERE id=?", (order_id,))
        cursor.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                       (session.get("username", ""), "order_cancelled", "order", str(order_id), "{}"))
        if order[2] is not None:
            active = cursor.execute("SELECT 1 FROM orders WHERE table_id=? AND id<>? AND status NOT IN ('Cancelled','Refunded','Completed') LIMIT 1", (order[2], order_id)).fetchone()
            if not active:
                cursor.execute("UPDATE tables SET status='Available' WHERE id=?", (order[2],))
        conn.commit()
        return jsonify({"success": True, "message": "Order cancelled and stock restored."})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not cancel order %s", order_id)
        return jsonify({"success": False, "message": "Unable to cancel this order."}), 500
    finally:
        conn.close()
# ==========================================================
# COMPLETE ORDER
# ==========================================================

@billing_bp.route("/complete/<int:order_id>", methods=["PUT"])
def complete_order(order_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[0] in ("Cancelled", "Refunded"):
            return jsonify({"success": False, "message": "Closed orders cannot be completed."}), 409
        cursor.execute("UPDATE orders SET status='Completed' WHERE id=?", (order_id,))
        cursor.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                       (session.get("username", ""), "order_completed", "order", str(order_id), "{}"))
        conn.commit()
        return jsonify({"success": True, "message": "Order completed."})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not complete order %s", order_id)
        return jsonify({"success": False, "message": "Unable to complete this order."}), 500
    finally:
        conn.close()


# ==========================================================
# PAYMENT
# ==========================================================

@billing_bp.route("/split-payment/<int:order_id>", methods=["POST"])
def record_split_payments(order_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Split payment details are invalid."}), 400
    shares = data.get("shares") or []
    if not isinstance(shares, list) or not shares:
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
        if order[1] == "Paid":
            return jsonify({"success": False, "message": "This order is already fully paid."}), 409
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
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Payment details are invalid."}), 400
    raw_method = data.get("payment_type", "Cash")
    if not isinstance(raw_method, str):
        return jsonify({"success": False, "message": "Choose a valid payment method."}), 400
    payment_method = raw_method.strip()
    if payment_method not in {"Cash", "Card", "Other", "UPI", "Wallet", "Paytm EDC"}:
        return jsonify({"success": False, "message": "Choose a valid payment method."}), 400
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Enter a valid payment amount."}), 400
    if not math.isfinite(amount) or amount <= 0:
        return jsonify({"success": False, "message": "Payment amount must be greater than zero."}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("SELECT total, status, payment_status FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[1] in ("Cancelled", "Refunded") or order[2] == "Refunded":
            return jsonify({"success": False, "message": "This order cannot accept payments."}), 409
        if order[2] == "Paid":
            return jsonify({"success": False, "message": "This order is already fully paid."}), 409
        already_paid = float(cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE order_id=? AND payment_status='Paid'", (order_id,)).fetchone()[0] or 0)
        due = max(0.0, float(order[0] or 0) - already_paid)
        if amount > due + 0.02:
            return jsonify({"success": False, "message": f"Payment exceeds the remaining balance of ₹{due:.2f}."}), 409
        cursor.execute("INSERT INTO payments(order_id, payment_type, amount, payment_status) VALUES (?, ?, ?, 'Paid')", (order_id, payment_method, amount))
        total_paid = already_paid + amount
        new_status = "Paid" if total_paid >= float(order[0] or 0) - 0.02 else "Partial"
        payment_methods = {row[0] for row in cursor.execute("SELECT DISTINCT payment_type FROM payments WHERE order_id=? AND payment_status='Paid'", (order_id,)).fetchall()}
        cursor.execute("UPDATE orders SET payment_status=?, payment_method=? WHERE id=?", (new_status, next(iter(payment_methods)) if len(payment_methods) == 1 else "Split", order_id))
        conn.commit()
        return jsonify({"success": True, "message": "Payment recorded.", "payment_status": new_status,
                        "paid": round(total_paid, 2), "remaining": round(max(0.0, float(order[0] or 0) - total_paid), 2)})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not record payment for order %s", order_id)
        return jsonify({"success": False, "message": "Unable to record this payment."}), 500
    finally:
        conn.close()


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

            WHERE DATE(created_at,'+5 hours','+30 minutes')=DATE('now','+5 hours','+30 minutes')

            AND payment_status='Paid'
            AND status NOT IN ('Cancelled','Refunded')

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

            WHERE payment_status='Paid'
              AND status NOT IN ('Cancelled','Refunded')

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

            JOIN orders ON orders.id = order_items.order_id

            WHERE orders.status NOT IN ('Cancelled','Refunded')

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

                WHERE name=? COLLATE NOCASE OR phone=?

            )

            ORDER BY created_at DESC

        """, (name, name))

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
    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("SELECT status, payment_status, table_id FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[1] in ("Paid", "Partial") or order[0] in ("Completed", "Served", "Refunded"):
            return jsonify({"success": False, "message": "Paid or completed orders must be retained for the sales audit."}), 409
        items = cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall()
        if order[0] != "Cancelled":
            for item in items:
                cursor.execute("UPDATE products SET stock=stock+? WHERE id=? AND stock_unlimited=0", (item["quantity"], item["product_id"]))
                if cursor.rowcount:
                    cursor.execute("INSERT INTO inventory_logs(product_id, quantity, action, remarks) VALUES (?, ?, 'DELETE', ?)",
                                   (item["product_id"], item["quantity"], f"Deleted order {order_id}"))
        cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
        cursor.execute("DELETE FROM payments WHERE order_id=?", (order_id,))
        cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        if order[2] is not None:
            active = cursor.execute("SELECT 1 FROM orders WHERE table_id=? AND status NOT IN ('Cancelled','Refunded','Completed') LIMIT 1", (order[2],)).fetchone()
            if not active:
                cursor.execute("UPDATE tables SET status='Available' WHERE id=?", (order[2],))
        conn.commit()
        return jsonify({"success": True, "message": "Unpaid order deleted and stock restored."})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not delete order %s", order_id)
        return jsonify({"success": False, "message": "Unable to delete this order."}), 500
    finally:
        conn.close()


# ==========================================================
# REFUND ORDER
# ==========================================================

@billing_bp.route("/refund/<int:order_id>", methods=["PUT", "POST"])
def refund_order(order_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Refund details are invalid."}), 400
    reason = str(data.get("reason", "")).strip()[:500]
    if not reason:
        return jsonify({"success": False, "message": "A refund reason is required."}), 400
    conn = get_connection()
    try:
        cursor = conn.cursor()
        order = cursor.execute("SELECT total, status, payment_status, payment_method FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404
        if order[1] not in ("Completed", "Served"):
            return jsonify({"success": False, "message": "Only completed or served orders can be refunded."}), 409
        if str(order[2] or "").lower() != "paid":
            return jsonify({"success": False, "message": "Only fully paid orders can be refunded."}), 409
        amount = float(order[0] or 0)
        cursor.execute("UPDATE orders SET status='Refunded', payment_status='Refunded', refund_reason=?, refunded_at=CURRENT_TIMESTAMP WHERE id=?", (reason, order_id))
        cursor.execute("INSERT INTO payments(order_id, payment_type, amount, payment_status) VALUES (?, ?, ?, 'Refunded')",
                       (order_id, order[3] or "Other", -amount))
        cursor.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                       (session.get("username", ""), "order_refunded", "order", str(order_id), json.dumps({"reason": reason, "amount": amount})))
        conn.commit()
        return jsonify({"success": True, "message": "Refund recorded.", "amount": amount})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not refund order %s", order_id)
        return jsonify({"success": False, "message": "Unable to record this refund."}), 500
    finally:
        conn.close()


# ==========================================================
# SALES REPORT
# ==========================================================

@billing_bp.route("/sales-report", methods=["GET"])
def sales_report():

    try:

        start = request.args.get("start")
        end = request.args.get("end")
        try:
            start_date = datetime.strptime(start or "", "%Y-%m-%d").date()
            end_date = datetime.strptime(end or "", "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "message": "Choose a valid start and end date."}), 400
        if start_date > end_date:
            return jsonify({"success": False, "message": "The start date must be on or before the end date."}), 400

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE DATE(created_at,'+5 hours','+30 minutes')

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

        if order is None:
            conn.close()
            return jsonify({"success": False, "message": "Order not found."}), 404

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


# Dashboard billing APIs. Keep their list and invoice shapes stable for the
# existing dashboard.js consumers.
@billing_bp.route("/recent", methods=["GET"])
def recent_bills():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT o.id, o.bill_no, COALESCE(c.name, 'Walk-in Customer') AS customer,
                   o.order_type, o.total, o.payment_method, o.payment_status,
                   o.status, o.created_at
            FROM orders o LEFT JOIN customers c ON c.id=o.customer_id
            ORDER BY o.id DESC LIMIT 50
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    except sqlite3.Error:
        current_app.logger.exception("Could not load recent bills")
        return jsonify({"success": False, "message": "Unable to load recent bills."}), 500
    finally:
        conn.close()


@billing_bp.route("/invoice/<int:order_id>", methods=["GET"])
def get_invoice(order_id):
    conn = get_connection()
    try:
        invoice = invoice_payload(conn, order_id)
        if invoice is None:
            return jsonify({"success": False, "message": "Invoice not found."}), 404
        return jsonify({"success": True, "invoice": invoice})
    except sqlite3.Error:
        current_app.logger.exception("Could not load invoice %s", order_id)
        return jsonify({"success": False, "message": "Unable to load this invoice."}), 500
    finally:
        conn.close()


@billing_bp.route("/print/<int:order_id>", methods=["GET"])
def print_invoice(order_id):
    conn = get_connection()
    try:
        invoice = invoice_payload(conn, order_id)
        if invoice is None:
            return jsonify({"success": False, "message": "Invoice not found."}), 404
        return render_template_string("""<!doctype html><html><head><meta charset='utf-8'><title>Invoice {{ invoice.bill_no }}</title>
        <style>body{font:14px Arial,sans-serif;max-width:720px;margin:32px auto;color:#222}header{text-align:center}table{width:100%;border-collapse:collapse;margin:20px 0}th,td{padding:8px;border-bottom:1px solid #ddd;text-align:left}td:last-child,th:last-child{text-align:right}.totals{margin-left:auto;width:260px}.totals div{display:flex;justify-content:space-between;padding:5px}@media print{button{display:none}body{margin:0}}</style></head><body>
        <header><h1>CafeSync</h1><p>Invoice</p></header><p><b>Bill:</b> {{ invoice.bill_no }} &nbsp; <b>Date:</b> {{ invoice.invoice_date }}</p>
        <p><b>Customer:</b> {{ invoice.customer.name }} &nbsp; <b>Phone:</b> {{ invoice.customer.phone }}</p><p><b>Order:</b> {{ invoice.order_type }}{% if invoice.table_name %} · {{ invoice.table_name }}{% endif %} &nbsp; <b>Payment:</b> {{ invoice.payment_method }}</p>
        <table><thead><tr><th>Item</th><th>Qty</th><th>Rate</th><th>Total</th></tr></thead><tbody>{% for item in invoice.items %}<tr><td>{{ item.name }}{% if item.chef_note %}<br><small>{{ item.chef_note }}</small>{% endif %}</td><td>{{ item.quantity }}</td><td>₹{{ '%.2f'|format(item.price) }}</td><td>₹{{ '%.2f'|format(item.total) }}</td></tr>{% endfor %}</tbody></table>
        <div class='totals'><div><span>Subtotal</span><span>₹{{ '%.2f'|format(invoice.summary.subtotal) }}</span></div><div><span>GST</span><span>₹{{ '%.2f'|format(invoice.summary.gst) }}</span></div><div><span>Discount</span><span>₹{{ '%.2f'|format(invoice.summary.discount) }}</span></div><div><b>Total</b><b>₹{{ '%.2f'|format(invoice.summary.grand_total) }}</b></div></div><button onclick='window.print()'>Print</button><script>window.addEventListener('load',()=>setTimeout(()=>window.print(),250))</script></body></html>""", invoice=invoice)
    finally:
        conn.close()


@billing_bp.route("/pdf/<int:order_id>", methods=["GET"])
def download_invoice_pdf(order_id):
    conn = get_connection()
    try:
        invoice = invoice_payload(conn, order_id)
        if invoice is None:
            return jsonify({"success": False, "message": "Invoice not found."}), 404
    finally:
        conn.close()
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from xml.sax.saxutils import escape
        output = BytesIO()
        document = SimpleDocTemplate(output, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=14*mm, bottomMargin=14*mm)
        styles = getSampleStyleSheet()
        story = [Paragraph("CafeSync · Tax Invoice", styles["Title"]),
                 Paragraph(f"Bill: {escape(str(invoice.get('bill_no') or ''))} &nbsp;&nbsp; Date: {escape(str(invoice.get('invoice_date') or ''))}", styles["Normal"]),
                 Paragraph(f"Customer: {escape(str(invoice['customer']['name']))} &nbsp;&nbsp; Phone: {escape(str(invoice['customer']['phone']))}", styles["Normal"]), Spacer(1, 8*mm)]
        rows = [["Item", "Qty", "Rate (INR)", "Total (INR)"]]
        rows.extend([[Paragraph(escape(str(item["name"])), styles["BodyText"]), str(item["quantity"]), f"{item['price']:.2f}", f"{item['total']:.2f}"] for item in invoice["items"]])
        table = Table(rows, colWidths=[95*mm, 18*mm, 32*mm, 32*mm], repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8f1eb")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#cad5ce")), ("ALIGN", (1,1), (-1,-1), "RIGHT"), ("VALIGN", (0,0), (-1,-1), "TOP"), ("PADDING", (0,0), (-1,-1), 6)]))
        story.extend([table, Spacer(1, 6*mm)])
        summary = invoice["summary"]
        totals = [["Subtotal", f"INR {summary['subtotal']:.2f}"], ["GST", f"INR {summary['gst']:.2f}"], ["Discount", f"INR {summary['discount']:.2f}"], ["Grand total", f"INR {summary['grand_total']:.2f}"]]
        totals_table = Table(totals, colWidths=[42*mm, 38*mm], hAlign="RIGHT")
        totals_table.setStyle(TableStyle([("ALIGN", (1,0), (1,-1), "RIGHT"), ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"), ("LINEABOVE", (0,-1), (-1,-1), .8, colors.HexColor("#26372d")), ("PADDING", (0,0), (-1,-1), 5)]))
        story.append(totals_table)
        document.build(story)
        output.seek(0)
        return send_file(output, mimetype="application/pdf", as_attachment=True, download_name=f"{invoice.get('bill_no') or 'invoice'}.pdf")
    except Exception:
        current_app.logger.exception("Could not create PDF for invoice %s", order_id)
        return jsonify({"success": False, "message": "Unable to create this invoice PDF."}), 500


@billing_bp.route("/payment-history/<int:order_id>", methods=["GET"])
def payment_history(order_id):
    conn = get_connection()
    try:
        if not conn.execute("SELECT 1 FROM orders WHERE id=?", (order_id,)).fetchone():
            return jsonify({"success": False, "message": "Order not found."}), 404
        rows = conn.execute("""
            SELECT payment_type AS payment_method, amount, payment_status AS status, created_at
            FROM payments WHERE order_id=? ORDER BY id
        """, (order_id,)).fetchall()
        history = [dict(row) for row in rows]
        if not history:
            legacy = conn.execute("""
                SELECT payment_method, total AS amount, payment_status AS status, created_at
                FROM orders WHERE id=? AND payment_status='Paid'
            """, (order_id,)).fetchone()
            if legacy:
                history.append(dict(legacy))
        return jsonify(history)
    except sqlite3.Error:
        current_app.logger.exception("Could not load payment history for order %s", order_id)
        return jsonify({"success": False, "message": "Unable to load payment history."}), 500
    finally:
        conn.close()


@billing_bp.route("/live-transactions", methods=["GET"])
def live_transactions():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT o.id, o.bill_no, COALESCE(c.name, 'Walk-in Customer') AS customer,
                   o.total, o.payment_method, o.payment_status, o.status, o.created_at
            FROM orders o LEFT JOIN customers c ON c.id=o.customer_id
            WHERE o.status NOT IN ('Cancelled','Refunded')
            ORDER BY o.id DESC LIMIT 30
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    except sqlite3.Error:
        current_app.logger.exception("Could not load live transactions")
        return jsonify({"success": False, "message": "Unable to load transactions."}), 500
    finally:
        conn.close()


@billing_bp.route("/payment-summary", methods=["GET"])
def payment_summary():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT payment_type, SUM(amount) AS amount FROM (
                SELECT p.payment_type, p.amount FROM payments p
                JOIN orders o ON o.id=p.order_id
                WHERE p.payment_status='Paid' AND o.status NOT IN ('Cancelled','Refunded')
                  AND DATE(p.created_at,'+5 hours','+30 minutes')=DATE('now','+5 hours','+30 minutes')
                UNION ALL
                SELECT COALESCE(o.payment_method,'Other'), o.total FROM orders o
                WHERE o.payment_status='Paid' AND o.status NOT IN ('Cancelled','Refunded')
                  AND DATE(o.created_at,'+5 hours','+30 minutes')=DATE('now','+5 hours','+30 minutes')
                  AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id=o.id)
            ) GROUP BY payment_type
        """).fetchall()
        summary = {"cash": 0.0, "upi": 0.0, "card": 0.0, "online": 0.0, "total": 0.0}
        for row in rows:
            method = str(row[0] or "Other").strip().lower()
            amount = float(row[1] or 0)
            if method == "cash": summary["cash"] += amount
            elif method == "upi": summary["upi"] += amount
            elif method == "card": summary["card"] += amount
            else: summary["online"] += amount
            summary["total"] += amount
        return jsonify({key: round(value, 2) for key, value in summary.items()})
    except sqlite3.Error:
        current_app.logger.exception("Could not calculate payment summary")
        return jsonify({"success": False, "message": "Unable to load payment summary."}), 500
    finally:
        conn.close()


@billing_bp.route("/recent-payments", methods=["GET"])
def recent_payments():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT bill_no, customer, payment_method, amount, created_at FROM (
                SELECT o.id AS sort_id, p.id AS payment_id, o.bill_no,
                       COALESCE(c.name, 'Walk-in Customer') AS customer,
                       p.payment_type AS payment_method, p.amount, p.created_at
                FROM payments p JOIN orders o ON o.id=p.order_id
                LEFT JOIN customers c ON c.id=o.customer_id
                WHERE p.payment_status='Paid' AND o.status NOT IN ('Cancelled','Refunded')
                UNION ALL
                SELECT o.id AS sort_id, o.id AS payment_id, o.bill_no,
                       COALESCE(c.name, 'Walk-in Customer') AS customer,
                       o.payment_method, o.total AS amount, o.created_at
                FROM orders o LEFT JOIN customers c ON c.id=o.customer_id
                WHERE o.payment_status='Paid' AND o.status NOT IN ('Cancelled','Refunded')
                  AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id=o.id)
            ) ORDER BY sort_id DESC, payment_id DESC LIMIT 30
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    except sqlite3.Error:
        current_app.logger.exception("Could not load recent payments")
        return jsonify({"success": False, "message": "Unable to load recent payments."}), 500
    finally:
        conn.close()


@billing_bp.route("/refunds", methods=["GET"])
def get_refunds():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT o.id, o.bill_no, COALESCE(c.name, 'Walk-in Customer') AS customer,
                   o.total AS amount, o.payment_method, o.refund_reason AS reason,
                   COALESCE(o.refunded_at, o.created_at) AS created_at
            FROM orders o LEFT JOIN customers c ON c.id=o.customer_id
            WHERE o.status='Refunded' OR o.payment_status='Refunded'
            ORDER BY COALESCE(o.refunded_at,o.created_at) DESC LIMIT 100
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    except sqlite3.Error:
        current_app.logger.exception("Could not load refunds")
        return jsonify({"success": False, "message": "Unable to load refund history."}), 500
    finally:
        conn.close()


@billing_bp.route("/refund-details/<int:order_id>", methods=["GET"])
def refund_details(order_id):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT o.id, o.bill_no, COALESCE(c.name, 'Walk-in Customer') AS customer,
                   o.total AS amount, o.payment_method, o.refund_reason AS reason,
                   COALESCE(o.refunded_at,o.created_at) AS created_at
            FROM orders o LEFT JOIN customers c ON c.id=o.customer_id
            WHERE o.id=? AND (o.status='Refunded' OR o.payment_status='Refunded')
        """, (order_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "Refund record not found."}), 404
        return jsonify(dict(row))
    except sqlite3.Error:
        current_app.logger.exception("Could not load refund details for order %s", order_id)
        return jsonify({"success": False, "message": "Unable to load refund details."}), 500
    finally:
        conn.close()


# ==========================================================
# KITCHEN ORDERS
# ==========================================================

@billing_bp.route("/kot", methods=["POST"])
@login_required
def create_kot():

    conn = None
    error_id = secrets.token_hex(4)

    try:
        data = request.get_json(silent=True)


        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "message": "No order data received"
            }), 400

        items = data.get("items", [])


        if not isinstance(items, list) or not items:
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
            try:
                table_id = int(table_id)
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": "Choose a valid table."}), 400
            if table_id <= 0:
                return jsonify({"success": False, "message": "Choose a valid table."}), 400

        order_type = data.get("order_type", "Dine In")
        if not isinstance(order_type, str) or order_type not in {"Dine In", "Parcel", "Delivery", "Take Away"}:
            return jsonify({"success": False, "message": "Choose a valid order type."}), 400
        order_source = data.get("order_source", "Cafe")
        if not isinstance(order_source, str) or order_source not in {"Cafe", "Swiggy", "Zomato"}:
            return jsonify({"success": False, "message": "Choose a valid order source."}), 400
        if order_source in {"Swiggy", "Zomato"} and order_type != "Delivery":
            return jsonify({"success": False, "message": "Swiggy and Zomato orders must use Delivery order type."}), 400
        kot_status = "Pending" if order_type == "Delivery" and order_source in {"Swiggy", "Zomato"} else "Completed"

        try:
            subtotal = float(data.get("subtotal", 0))
            gst = float(data.get("gst", 0))
            discount = float(data.get("discount", 0))
            total = float(data.get("total", 0))
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Bill totals must be valid amounts."}), 400
        if not all(math.isfinite(value) for value in (subtotal, gst, discount, total)) or min(subtotal, gst, discount, total) < 0:
            return jsonify({"success": False, "message": "Bill totals must be valid non-negative amounts."}), 400

        payment_method = data.get(
            "payment_method",
            "Pending"
        )
        if not isinstance(payment_method, str) or payment_method not in {"Pending", "Cash", "Card", "Other", "UPI", "Wallet", "Paytm EDC"}:
            return jsonify({"success": False, "message": "Choose a valid payment method."}), 400
        customer_name = data.get("customer_name", "")
        if customer_name is not None and not isinstance(customer_name, str):
            return jsonify({"success": False, "message": "Customer name or phone must be text."}), 400

        # ==============================
        # DATABASE
        # ==============================

        conn = get_connection()
        cursor = conn.cursor()

        if table_id is not None:
            selected_table = cursor.execute("SELECT status FROM tables WHERE id=?", (table_id,)).fetchone()
            if not selected_table:
                return jsonify({"success": False, "message": "The selected table no longer exists."}), 409
            if selected_table[0] not in ("Available", "Occupied"):
                return jsonify({"success": False, "message": "The selected table is not available for a new order."}), 409

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
            customer_id = get_or_create_customer(cursor, customer_name)

        ingredient_demand = {}
        for cart_item in items:
            try:
                recipe_product_id = int(cart_item.get("product_id"))
                recipe_quantity = int(cart_item.get("quantity", 1))
            except (TypeError, ValueError, AttributeError):
                conn.rollback()
                return jsonify({"success": False, "message": "An order item has invalid details."}), 400
            for recipe in cursor.execute("SELECT ingredient_id, quantity FROM recipes WHERE product_id=?", (recipe_product_id,)).fetchall():
                ingredient_demand[recipe[0]] = ingredient_demand.get(recipe[0], 0) + float(recipe[1]) * recipe_quantity
        for ingredient_id, required_quantity in ingredient_demand.items():
            available = cursor.execute("SELECT name, current_stock FROM ingredients WHERE id=? AND active=1", (ingredient_id,)).fetchone()
            if not available or float(available["current_stock"]) + 1e-9 < required_quantity:
                conn.rollback()
                label = available["name"] if available else "recipe ingredient"
                return jsonify({"success": False, "message": f"Insufficient ingredient stock: {label}."}), 409

        # ==============================
        # BILL NUMBER
        # ==============================

        bill_no = "KOT-" + datetime.now().strftime("%Y%m%d%H%M%S%f")


        # ==============================
        # CREATE ORDER
        # ==============================

        cursor.execute("""
            INSERT INTO orders (
                bill_no,
                table_id,
                customer_id,
                order_type,
                order_source,
                subtotal,
                gst,
                discount,
                total,
                payment_method,
                payment_status,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bill_no,
            table_id,
            customer_id,
            order_type,
            order_source,
            subtotal,
            gst,
            discount,
            total,
            payment_method,
            "Pending",
            kot_status
        ))

        order_id = cursor.lastrowid


        # ==============================
        # CREATE ORDER ITEMS
        # ==============================

        calculated_subtotal = 0.0

        for item in items:


            if not isinstance(item, dict):
                conn.rollback()
                return jsonify({"success": False, "message": "An order item is invalid."}), 400
            try:
                product_id = int(item["product_id"])
                quantity = int(item.get("quantity", 1))
                price = float(item.get("price", 0))
            except (KeyError, TypeError, ValueError):
                conn.rollback()
                return jsonify({"success": False, "message": "An order item has invalid details."}), 400
            if product_id <= 0 or not math.isfinite(price) or price < 0:
                conn.rollback()
                return jsonify({"success": False, "message": "An order item has invalid details."}), 400

            if quantity <= 0:
                conn.rollback()
                return jsonify({"success": False, "message": "Item quantity must be at least one."}), 400

            product = conn.execute(
                "SELECT stock, stock_unlimited, is_available, price FROM products WHERE id=?",
                (product_id,)
            ).fetchone()
            if not product:
                conn.rollback()
                return jsonify({"success": False, "message": "A selected menu item no longer exists."}), 409
            if not product["is_available"]:
                conn.rollback()
                return jsonify({"success": False, "message": "One of the selected items is no longer available."}), 409
            if not product["stock_unlimited"] and int(product["stock"] or 0) < quantity:
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

            if not product["stock_unlimited"]:
                cursor.execute("UPDATE products SET stock=stock-? WHERE id=?", (quantity, product_id))
                cursor.execute("""
                    INSERT INTO inventory_logs(product_id, quantity, action, remarks)
                    VALUES (?, ?, 'SALE', ?)
                """, (product_id, quantity, f"Kitchen ticket {bill_no}"))

            for recipe in cursor.execute("SELECT ingredient_id, quantity FROM recipes WHERE product_id=?", (product_id,)).fetchall():
                used = float(recipe["quantity"]) * quantity
                cursor.execute("UPDATE ingredients SET current_stock=current_stock-? WHERE id=?", (used, recipe["ingredient_id"]))
                cursor.execute("""
                    INSERT INTO ingredient_movements(ingredient_id,quantity_change,movement_type,reference,order_id,actor)
                    VALUES(?,?,'SALE',?,?,?)
                """, (recipe["ingredient_id"], -used, bill_no, order_id, session.get("username", "")))

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

        cursor.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                       (session.get("username", ""), "kitchen_order_created", "order", str(order_id), json.dumps({"bill_no": bill_no, "total": total})))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Kitchen Order Created",
            "data": {
                "order_id": order_id,
            "bill_no": bill_no,
            "order_type": order_type,
            "order_source": order_source,
            "status": order_status
            }
        }), 200

    except Exception:

        if conn:
            conn.rollback()

        current_app.logger.exception("Kitchen ticket creation failed (reference %s)", error_id)

        return jsonify({
            "success": False,
            "message": "Kitchen ticket could not be saved. Share the error reference with support if it happens again.",
            "error_id": error_id
        }), 500

    finally:

        if conn:
            conn.close()

print(" CREATE KOT ROUTE DEFINED ")

# ==========================================================
# UPDATE ORDER STATUS
# ==========================================================

@billing_bp.route("/status/<int:order_id>", methods=["PUT"])
def update_status(order_id):

    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "message": "Order status is invalid."}), 400
        status = data.get("status")
        allowed = {"Pending", "Hold", "Preparing", "Ready", "Served", "Completed"}
        if status not in allowed:
            return jsonify({"success": False, "message": "Choose a valid order status."}), 400
        conn = get_connection()
        try:
            cursor = conn.cursor()
            order = cursor.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
            if not order:
                return jsonify({"success": False, "message": "Order not found."}), 404
            if order[0] in ("Cancelled", "Refunded"):
                return jsonify({"success": False, "message": "This order is already closed."}), 409
            cursor.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
            cursor.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                           (session.get("username", ""), "order_status_changed", "order", str(order_id), json.dumps({"status": status})))
            conn.commit()
            return jsonify({"success": True, "message": "Status updated."})
        finally:
            conn.close()
    except sqlite3.Error:
        current_app.logger.exception("Could not update order status for %s", order_id)
        return jsonify({"success": False, "message": "Unable to update order status."}), 500

print(" BILLING.PY LOADED ")


