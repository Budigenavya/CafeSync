# ==========================================================
# IMPORTS
# ==========================================================

from flask import Blueprint
from flask import request
from flask import jsonify, render_template, current_app, send_from_directory, url_for, session

from routes.auth import login_required

from database import get_connection

import sqlite3
import os
import uuid
import json
import math
from werkzeug.utils import secure_filename
from config import PRODUCT_IMAGE_FOLDER


# ==========================================================
# BLUEPRINT
# ==========================================================

inventory_bp = Blueprint(

    "inventory",

    __name__

)

ALLOWED_PRODUCT_IMAGE_TYPES = {
    "image/jpeg": ("jpg", b"\xff\xd8\xff"),
    "image/png": ("png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": ("webp", b"RIFF"),
}


def _save_product_image(upload):
    if not upload or not upload.filename:
        return None
    if upload.mimetype not in ALLOWED_PRODUCT_IMAGE_TYPES:
        raise ValueError("Choose a JPG, PNG, or WebP photo.")
    payload = upload.read(5 * 1024 * 1024 + 1)
    upload.stream.seek(0)
    if not payload or len(payload) > 5 * 1024 * 1024:
        raise ValueError("Product photos must be smaller than 5 MB.")
    extension, signature = ALLOWED_PRODUCT_IMAGE_TYPES[upload.mimetype]
    if not payload.startswith(signature) or (extension == "webp" and payload[8:12] != b"WEBP"):
        raise ValueError("The selected file is not a valid JPG, PNG, or WebP image.")
    os.makedirs(PRODUCT_IMAGE_FOLDER, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{extension}"
    upload.save(os.path.join(PRODUCT_IMAGE_FOLDER, secure_filename(filename)))
    return filename


def _remove_product_image(filename):
    if not filename:
        return
    safe_name = os.path.basename(filename)
    try:
        os.remove(os.path.join(PRODUCT_IMAGE_FOLDER, safe_name))
    except (FileNotFoundError, OSError):
        pass


@inventory_bp.route("/inventory/product-images/<path:filename>")
def product_image(filename):
    return send_from_directory(PRODUCT_IMAGE_FOLDER, filename)

@inventory_bp.route("/inventory")
@login_required
def inventory():

    return render_template("inventory.html")

# ==========================================================
# SUCCESS RESPONSE
# ==========================================================

def success(message,data=None):

    return jsonify({

        "success":True,

        "message":message,

        "data":data

    })

# ==========================================================
# GET CATEGORIES
# ==========================================================

@inventory_bp.route(
    "/inventory/categories",
    methods=["GET"]
)
def get_categories():

    try:

        conn = get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                name
            FROM categories
            ORDER BY name
        """)

        categories = [
            dict(row)
            for row in cursor.fetchall()
        ]

        conn.close()

        return success(
            "Categories Loaded",
            categories
        )

    except Exception as e:

        print(e)

        return jsonify({
            "success": False,
            "message": "Unable To Load Categories"
        }),500



# ==========================================================
# GET PRODUCTS
# ==========================================================

@inventory_bp.route(
    "/inventory/products",
    methods=["GET"]
)
def get_products():
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        product_columns = {row[1] for row in cursor.execute("PRAGMA table_info(products)").fetchall()}
        category_columns = {row[1] for row in cursor.execute("PRAGMA table_info(categories)").fetchall()}
        if not {"id", "name", "price"}.issubset(product_columns):
            raise sqlite3.OperationalError("The products table is missing its required id, name, or price columns.")

        stock_expr = "p.stock" if "stock" in product_columns else "0"
        availability_expr = "p.is_available" if "is_available" in product_columns else "1"
        barcode_expr = "p.barcode" if "barcode" in product_columns else "NULL"
        category_id_expr = "p.category_id" if "category_id" in product_columns else "NULL"
        image_expr = "p.image" if "image" in product_columns else "NULL"
        category_join = (
            "LEFT JOIN categories c ON p.category_id=c.id"
            if "category_id" in product_columns and {"id", "name"}.issubset(category_columns)
            else ""
        )
        category_name_expr = "c.name" if category_join else "NULL"
        cursor.execute(f"""
            SELECT p.id, p.name, p.price,
                   {stock_expr} AS stock,
                   {availability_expr} AS is_available,
                   {barcode_expr} AS barcode,
                   {category_id_expr} AS category_id,
                   {category_name_expr} AS category_name,
                   {image_expr} AS image
            FROM products p
            {category_join}
            ORDER BY p.name COLLATE NOCASE
        """)
        products = [dict(row) for row in cursor.fetchall()]
        for product in products:
            product["image_url"] = url_for("inventory.product_image", filename=product["image"]) if product.get("image") else None
        return success("Products Loaded", products)
    except Exception as e:
        print("Unable To Load Products:", repr(e))
        return jsonify({"success": False, "message": "Unable To Load Products"}), 500
    finally:
        if conn is not None:
            conn.close()


@inventory_bp.route(
    "/inventory/products/<int:product_id>/availability",
    methods=["PUT"]
)
def set_product_availability(product_id):
    data = request.get_json(silent=True) or {}
    value = data.get("is_available")
    if value not in (True, False, 0, 1):
        return error("Availability must be on or off.", 400)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET is_available=? WHERE id=?",
        (int(bool(value)), product_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        return error("Menu item not found.", 404)
    conn.commit()
    conn.close()
    return success("Menu item availability updated.", {"id": product_id, "is_available": int(bool(value))})

# ==========================================================
# ERROR RESPONSE
# ==========================================================

def error(message,status=400):

    return jsonify({

        "success":False,

        "message":message

    }),status


@inventory_bp.route("/inventory/products/<int:product_id>/addons", methods=["GET"])
def get_product_addons(product_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, product_id, name, price, is_available FROM product_addons WHERE product_id=? ORDER BY name",
        (product_id,)
    ).fetchall()
    conn.close()
    return success("Product add-ons loaded", [dict(row) for row in rows])


@inventory_bp.route("/inventory/products/<int:product_id>/addons", methods=["POST"])
def add_product_addon(product_id):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()[:80]
    try:
        price = float(data.get("price", 0))
    except (TypeError, ValueError):
        return error("Enter a valid add-on price.")
    if not name:
        return error("Add-on name is required.")
    if price < 0 or price > 100000:
        return error("Add-on price must be between ₹0 and ₹100,000.")
    conn = get_connection()
    cursor = conn.cursor()
    if not cursor.execute("SELECT 1 FROM products WHERE id=?", (product_id,)).fetchone():
        conn.close()
        return error("Menu item not found.", 404)
    cursor.execute(
        "INSERT INTO product_addons(product_id, name, price) VALUES (?, ?, ?)",
        (product_id, name, price)
    )
    addon_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return success("Add-on added.", {"id": addon_id, "product_id": product_id, "name": name, "price": price})


@inventory_bp.route("/inventory/addons/<int:addon_id>", methods=["DELETE"])
def delete_product_addon(addon_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_addons WHERE id=?", (addon_id,))
    if cursor.rowcount == 0:
        conn.close()
        return error("Add-on not found.", 404)
    conn.commit()
    conn.close()
    return success("Add-on deleted.")

# ==========================================================
# INVENTORY DASHBOARD
# ==========================================================

@inventory_bp.route(

    "/inventory/dashboard",

    methods=["GET"]

)

def inventory_dashboard():

    try:

        conn=get_connection()

        conn.row_factory=sqlite3.Row

        cursor=conn.cursor()

        # -----------------------------
        # Total Products
        # -----------------------------

        cursor.execute("""

            SELECT COUNT(*) total

            FROM products

        """)

        total_products=cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM products WHERE price IS NULL OR TRIM(CAST(price AS TEXT))=''")
        unpriced_products = cursor.fetchone()["total"]

        # -----------------------------
        # Categories
        # -----------------------------

        cursor.execute("""

            SELECT COUNT(*) total

            FROM categories

        """)

        total_categories=cursor.fetchone()["total"]

        # -----------------------------
        # Inventory Value
        # -----------------------------

        cursor.execute("""

            SELECT

                IFNULL(

                    SUM(price*stock),

                    0

                ) value

            FROM products

        """)

        inventory_value=cursor.fetchone()["value"]

        # -----------------------------
        # Low Stock
        # -----------------------------

        cursor.execute("""

            SELECT COUNT(*) total

            FROM products

            WHERE stock<=10

        """)

        low_stock=cursor.fetchone()["total"]

        conn.close()

        return success(

            "Dashboard Loaded",

            {

                "total_products":total_products,

                "unpriced_products":unpriced_products,

                "total_categories":total_categories,

                "inventory_value":inventory_value,

                "low_stock":low_stock

            }

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Load Dashboard",

            500

        )

# ==========================================================
# GET CATEGORIES
# ======================================================
# ==========================================================
# ADD CATEGORY
# ==========================================================

@inventory_bp.route(

    "/inventory/categories",

    methods=["POST"]

)

def add_category():

    try:

        data = request.get_json(silent=True) or {}

        name = data.get("name", "").strip()

        if not name:

            return error(

                "Category Name Is Required"

            )

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT id

            FROM categories

            WHERE LOWER(name)=LOWER(?)

        """,

        (name,))

        if cursor.fetchone():

            conn.close()

            return error(

                "Category Already Exists"

            )

        cursor.execute("""

            INSERT INTO categories(

                name

            )

            VALUES(?)

        """,

        (name,))

        conn.commit()

        conn.close()

        return success(

            "Category Added Successfully"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Add Category",

            500

        )
# ==========================================================
# ADD PRODUCT
# ==========================================================

@inventory_bp.route(

    "/inventory/products",

    methods=["POST"]

)

def add_product():

    try:

        data = request.form if request.files else (request.get_json(silent=True) or {})

        name = data.get("name", "").strip()
        category_id = data.get("category_id")
        barcode = data.get("barcode", "").strip()
        price = data.get("price", 0)
        stock = data.get("stock", 0)
        try:
            price = float(price)
            stock = int(stock)
            if not math.isfinite(price) or price < 0 or stock < 0:
                raise ValueError
        except (TypeError, ValueError):
            return error("Enter a valid non-negative price and whole-number stock.")
        category_id = category_id or None
        image_filename = _save_product_image(request.files.get("image"))

        if not name:

            _remove_product_image(image_filename)

            return error(

                "Product Name Is Required"

            )

        conn = get_connection()

        cursor = conn.cursor()

        if barcode:

            cursor.execute("""

                SELECT id

                FROM products

                WHERE barcode=?

            """,

            (barcode,))

            if cursor.fetchone():

                conn.close()
                _remove_product_image(image_filename)

                return error(

                    "Barcode Already Exists"

                )

        cursor.execute("""

            INSERT INTO products(

                category_id,

                name,

                price,

                stock,

                barcode,
                image

            )

            VALUES(?,?,?,?,?,?)

        """,

        (

            category_id,

            name,

            price,

            stock,

            barcode,
            image_filename

        ))

        conn.commit()

        conn.close()

        return success(

            "Product Added Successfully"

        )

    except ValueError as e:
        if 'image_filename' in locals():
            _remove_product_image(image_filename)
        return error(str(e), 400)
    except Exception as e:

        if 'image_filename' in locals():
            _remove_product_image(image_filename)

        print(e)

        return error(

            "Unable To Add Product",

            500

        )

# ==========================================================
# UPDATE PRODUCT
# ==========================================================

@inventory_bp.route(

    "/inventory/products/<int:product_id>",

    methods=["PUT"]

)

def update_product(product_id):

    try:

        data = request.form if request.files else (request.get_json(silent=True) or {})

        name = data.get("name", "").strip()
        category_id = data.get("category_id")
        barcode = data.get("barcode", "").strip()
        price = data.get("price", 0)
        stock = data.get("stock", 0)
        try:
            price = float(price)
            stock = int(stock)
            if not math.isfinite(price) or price < 0 or stock < 0:
                raise ValueError
        except (TypeError, ValueError):
            return error("Enter a valid non-negative price and whole-number stock.")
        category_id = category_id or None
        image_filename = _save_product_image(request.files.get("image"))

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("SELECT image FROM products WHERE id=?", (product_id,))
        existing_product = cursor.fetchone()
        if not existing_product:
            conn.close()
            _remove_product_image(image_filename)
            return error("Product Not Found", 404)
        old_image = existing_product[0]

        if barcode:

            cursor.execute("""

                SELECT id

                FROM products

                WHERE barcode=?

                AND id<>?

            """,

            (

                barcode,

                product_id

            ))

            if cursor.fetchone():

                conn.close()
                _remove_product_image(image_filename)

                return error(

                    "Barcode Already Exists"

                )

        cursor.execute("""

            UPDATE products

            SET

                category_id=?,

                name=?,

                price=?,

                stock=?,

                barcode=?,
                image=COALESCE(?, image)

            WHERE id=?

        """,

        (

            category_id,

            name,

            price,

            stock,

            barcode,

            image_filename,

            product_id

        ))

        conn.commit()

        conn.close()

        if image_filename:
            _remove_product_image(old_image)

        return success(

            "Product Updated Successfully"

        )

    except ValueError as e:
        if 'image_filename' in locals():
            _remove_product_image(image_filename)
        return error(str(e), 400)
    except Exception as e:

        if 'image_filename' in locals():
            _remove_product_image(image_filename)

        print(e)

        return error(

            "Unable To Update Product",

            500

        )

# ==========================================================
# DELETE PRODUCT
# ==========================================================

@inventory_bp.route(

    "/inventory/products/<int:product_id>",

    methods=["DELETE"]

)

def delete_product(product_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("SELECT image FROM products WHERE id=?", (product_id,))
        product_row = cursor.fetchone()
        if not product_row:
            conn.close()
            return error("Product Not Found", 404)
        image_filename = product_row[0]

        cursor.execute("DELETE FROM product_addons WHERE product_id=?", (product_id,))

        cursor.execute("""

            DELETE

            FROM products

            WHERE id=?

        """,

        (

            product_id,

        ))

        if cursor.rowcount == 0:

            conn.close()

            return error(

                "Product Not Found",

                404

            )

        conn.commit()

        conn.close()

        _remove_product_image(image_filename)

        return success(

            "Product Deleted Successfully"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Delete Product",

            500

        )


@inventory_bp.route("/inventory/ingredients", methods=["GET", "POST"])
def ingredients_api():
    if request.method == "GET":
        conn = get_connection()
        try:
            rows = conn.execute("SELECT * FROM ingredients ORDER BY name COLLATE NOCASE").fetchall()
            return success("Ingredients loaded", [dict(row) for row in rows])
        finally:
            conn.close()
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()[:100]
    unit = str(data.get("unit") or "g").strip()[:20]
    try:
        stock = float(data.get("current_stock", 0))
        threshold = float(data.get("low_stock_threshold", 0))
        cost = float(data.get("unit_cost", 0))
        if not name or not unit or any(not math.isfinite(value) or value < 0 for value in (stock, threshold, cost)):
            raise ValueError
    except (TypeError, ValueError):
        return error("Enter a name, unit, and valid non-negative stock, threshold, and unit cost.")
    conn = get_connection()
    try:
        cursor = conn.execute("INSERT INTO ingredients(name,unit,current_stock,low_stock_threshold,unit_cost) VALUES(?,?,?,?,?)",
                              (name, unit, stock, threshold, cost))
        if stock:
            conn.execute("INSERT INTO ingredient_movements(ingredient_id,quantity_change,movement_type,actor) VALUES(?,?,'Opening',?)",
                         (cursor.lastrowid, stock, session.get("username", "")))
        conn.commit()
        return success("Ingredient added", {"id": cursor.lastrowid})
    except sqlite3.IntegrityError:
        conn.rollback()
        return error("An ingredient with that name already exists.", 409)
    finally:
        conn.close()


@inventory_bp.route("/inventory/ingredients/<int:ingredient_id>/movement", methods=["POST"])
def ingredient_movement(ingredient_id):
    data = request.get_json(silent=True) or {}
    movement_type = str(data.get("type") or "").strip().title()
    if movement_type not in {"Purchase", "Waste", "Adjustment"}:
        return error("Choose Purchase, Waste, or Adjustment.")
    try:
        change = float(data.get("quantity_change"))
        if not math.isfinite(change) or change == 0 or (movement_type == "Purchase" and change < 0) or (movement_type == "Waste" and change > 0):
            raise ValueError
    except (TypeError, ValueError):
        return error("Enter a non-zero quantity change with the correct sign (purchase +, waste -).")
    conn = get_connection()
    try:
        row = conn.execute("SELECT current_stock FROM ingredients WHERE id=?", (ingredient_id,)).fetchone()
        if not row:
            return error("Ingredient not found.", 404)
        new_stock = float(row[0]) + change
        if new_stock < -1e-9:
            return error("This movement would make ingredient stock negative.", 409)
        conn.execute("UPDATE ingredients SET current_stock=? WHERE id=?", (max(0, new_stock), ingredient_id))
        conn.execute("INSERT INTO ingredient_movements(ingredient_id,quantity_change,movement_type,notes,actor) VALUES(?,?,?,?,?)",
                     (ingredient_id, change, movement_type, str(data.get("notes") or "").strip()[:250], session.get("username", "")))
        conn.commit()
        return success("Stock movement saved", {"current_stock": max(0, new_stock)})
    finally:
        conn.close()


@inventory_bp.route("/inventory/products/<int:product_id>/recipe", methods=["GET", "PUT"])
def product_recipe(product_id):
    conn = get_connection()
    try:
        if not conn.execute("SELECT 1 FROM products WHERE id=?", (product_id,)).fetchone():
            return error("Menu item not found.", 404)
        if request.method == "GET":
            rows = conn.execute("""SELECT r.ingredient_id, r.quantity, i.name, i.unit, i.current_stock, i.unit_cost
                                   FROM recipes r JOIN ingredients i ON i.id=r.ingredient_id
                                   WHERE r.product_id=? ORDER BY i.name""", (product_id,)).fetchall()
            recipe = [dict(row) for row in rows]
            cost = sum(float(row["quantity"]) * float(row["unit_cost"]) for row in recipe)
            return success("Recipe loaded", {"items": recipe, "estimated_cost": round(cost, 2)})
        data = request.get_json(silent=True) or {}
        items = data.get("items")
        if not isinstance(items, list) or len(items) > 100:
            return error("Recipe items must be a list of up to 100 ingredients.")
        normalized = []
        seen = set()
        for item in items:
            try:
                ingredient_id = int(item["ingredient_id"])
                quantity = float(item["quantity"])
            except (KeyError, TypeError, ValueError):
                return error("Each recipe row needs an ingredient and quantity.")
            if ingredient_id in seen or quantity <= 0 or not math.isfinite(quantity) or not conn.execute("SELECT 1 FROM ingredients WHERE id=? AND active=1", (ingredient_id,)).fetchone():
                return error("Recipe contains an invalid or repeated ingredient.")
            seen.add(ingredient_id)
            normalized.append((product_id, ingredient_id, quantity))
        conn.execute("DELETE FROM recipes WHERE product_id=?", (product_id,))
        conn.executemany("INSERT INTO recipes(product_id,ingredient_id,quantity) VALUES(?,?,?)", normalized)
        conn.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                     (session.get("username", ""), "recipe_updated", "product", str(product_id), json.dumps(normalized)))
        conn.commit()
        return success("Recipe saved", {"ingredient_count": len(normalized)})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not save recipe for product %s", product_id)
        return error("Could not save the recipe.", 500)
    finally:
        conn.close()


@inventory_bp.route("/inventory/receipts", methods=["GET", "POST"])
def stock_receipts():
    conn = get_connection()
    try:
        if request.method == "GET":
            rows = conn.execute("""SELECT r.*, s.name AS supplier_name FROM stock_receipts r
                                   LEFT JOIN suppliers s ON s.id=r.supplier_id
                                   ORDER BY r.id DESC LIMIT 100""").fetchall()
            return success("Purchase receipts loaded", [dict(row) for row in rows])
        data = request.get_json(silent=True) or {}
        items = data.get("items")
        supplier_id = data.get("supplier_id")
        if not isinstance(items, list) or not items:
            return error("Add at least one ingredient to the purchase receipt.")
        normalized = []
        total = 0.0
        for item in items:
            try:
                ingredient_id = int(item["ingredient_id"])
                quantity = float(item["quantity"])
                unit_cost = float(item.get("unit_cost", 0))
            except (KeyError, TypeError, ValueError):
                return error("Receipt line is invalid.")
            if quantity <= 0 or unit_cost < 0 or not math.isfinite(quantity + unit_cost) or not conn.execute("SELECT 1 FROM ingredients WHERE id=? AND active=1", (ingredient_id,)).fetchone():
                return error("Receipt contains an invalid ingredient, quantity, or cost.")
            normalized.append((ingredient_id, quantity, unit_cost))
            total += quantity * unit_cost
        if supplier_id not in (None, "") and not conn.execute("SELECT 1 FROM suppliers WHERE id=? AND active=1", (supplier_id,)).fetchone():
            return error("Supplier not found.", 404)
        cursor = conn.execute("INSERT INTO stock_receipts(supplier_id,reference,total_cost,received_by,notes) VALUES(?,?,?,?,?)",
                              (supplier_id or None, str(data.get("reference") or "").strip()[:80], total, session.get("username", ""), str(data.get("notes") or "").strip()[:250]))
        receipt_id = cursor.lastrowid
        for ingredient_id, quantity, unit_cost in normalized:
            conn.execute("INSERT INTO stock_receipt_items(receipt_id,ingredient_id,quantity,unit_cost) VALUES(?,?,?,?)", (receipt_id, ingredient_id, quantity, unit_cost))
            conn.execute("UPDATE ingredients SET current_stock=current_stock+?, unit_cost=? WHERE id=?", (quantity, unit_cost, ingredient_id))
            conn.execute("INSERT INTO ingredient_movements(ingredient_id,quantity_change,movement_type,reference,actor) VALUES(?,?,'Purchase',?,?)",
                         (ingredient_id, quantity, f"Receipt {receipt_id}", session.get("username", "")))
        conn.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                     (session.get("username", ""), "stock_received", "receipt", str(receipt_id), json.dumps({"total_cost": total, "lines": len(normalized)})))
        conn.commit()
        return success("Purchase received and stock updated", {"receipt_id": receipt_id, "total_cost": total})
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("Could not record stock receipt")
        return error("Could not record the purchase receipt.", 500)
    finally:
        conn.close()


@inventory_bp.route("/inventory/suppliers", methods=["GET", "POST"])
def suppliers_api():
    conn = get_connection()
    try:
        if request.method == "GET":
            rows = conn.execute("SELECT id,name,phone,email FROM suppliers WHERE active=1 ORDER BY name").fetchall()
            return success("Suppliers loaded", [dict(row) for row in rows])
        data = request.get_json(silent=True) or {}
        name = str(data.get("name") or "").strip()[:120]
        if not name:
            return error("Supplier name is required.")
        conn.execute("INSERT OR IGNORE INTO suppliers(name,phone,email) VALUES(?,?,?)",
                     (name, str(data.get("phone") or "").strip()[:40], str(data.get("email") or "").strip()[:120]))
        row = conn.execute("SELECT id,name FROM suppliers WHERE name=? COLLATE NOCASE", (name,)).fetchone()
        conn.commit()
        return success("Supplier saved", dict(row))
    except sqlite3.Error:
        conn.rollback()
        return error("Could not save supplier.", 500)
    finally:
        conn.close()


@inventory_bp.route("/inventory/movements", methods=["GET"])
def ingredient_movements_api():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT m.id, i.name AS ingredient_name, i.unit, m.quantity_change,
                   m.movement_type, m.reference, m.notes, m.actor, m.created_at
            FROM ingredient_movements m JOIN ingredients i ON i.id=m.ingredient_id
            ORDER BY m.id DESC LIMIT 100
        """).fetchall()
        return success("Ingredient movement history loaded", [dict(row) for row in rows])
    finally:
        conn.close()
# ==========================================================
# IMPORTS (Add at the top if not already present)
# ==========================================================

import os
from datetime import datetime
from flask import send_file

from openpyxl import Workbook

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph
)

# ==========================================================
# EXPORT EXCEL
# ==========================================================

@inventory_bp.route(

    "/inventory/export/excel",

    methods=["GET"]

)

def export_inventory_excel():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                p.barcode,

                p.name,

                c.name AS category,

                p.price,

                p.stock

            FROM products p

            LEFT JOIN categories c

            ON p.category_id = c.id

            ORDER BY p.name

        """)

        products = cursor.fetchall()

        conn.close()

        wb = Workbook()

        ws = wb.active

        ws.title = "Inventory"

        ws.append([
            "Barcode",
            "Product",
            "Category",
            "Price",
            "Stock"
        ])

        for product in products:

            ws.append([

                product["barcode"],

                product["name"],

                product["category"],

                product["price"],

                product["stock"]

            ])

        filename = f"Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        wb.save(filename)

        return send_file(

            filename,

            as_attachment=True,

            download_name=filename

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Export Excel",

            500

        )

# ==========================================================
# EXPORT PDF
# ==========================================================

@inventory_bp.route(

    "/inventory/export/pdf",

    methods=["GET"]

)

def export_inventory_pdf():

    try:

        conn = get_connection()

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                p.barcode,

                p.name,

                c.name AS category,

                p.price,

                p.stock

            FROM products p

            LEFT JOIN categories c

            ON p.category_id = c.id

            ORDER BY p.name

        """)

        products = cursor.fetchall()

        conn.close()

        filename = f"Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        pdf = SimpleDocTemplate(filename)

        styles = getSampleStyleSheet()

        elements = []

        elements.append(

            Paragraph(

                "<b>CafeSync Inventory Report</b>",

                styles["Title"]

            )

        )

        table_data = [[

            "Barcode",

            "Product",

            "Category",

            "Price",

            "Stock"

        ]]

        for product in products:

            table_data.append([

                product["barcode"] or "",

                product["name"],

                product["category"],

                f"₹{product['price']:.2f}",

                product["stock"]

            ])

        table = Table(table_data)

        table.setStyle(

            TableStyle([

                ("BACKGROUND",(0,0),(-1,0),colors.darkblue),

                ("TEXTCOLOR",(0,0),(-1,0),colors.white),

                ("GRID",(0,0),(-1,-1),1,colors.black),

                ("BACKGROUND",(0,1),(-1,-1),colors.beige),

                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

                ("BOTTOMPADDING",(0,0),(-1,0),10),

            ])

        )

        elements.append(table)

        pdf.build(elements)

        return send_file(

            filename,

            as_attachment=True,

            download_name=filename

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Export PDF",

            500

        )
# ==========================================================
# VALIDATION HELPERS
# ==========================================================

def validate_product(data):

    if not data.get("name", "").strip():
        return "Product Name Is Required"

    if not data.get("category_id"):
        return "Category Is Required"

    try:
        price = float(data.get("price", 0))
        if price < 0:
            return "Price Cannot Be Negative"
    except:
        return "Invalid Price"

    try:
        stock = int(data.get("stock", 0))
        if stock < 0:
            return "Stock Cannot Be Negative"
    except:
        return "Invalid Stock"

    return None


# ==========================================================
# CHECK PRODUCT EXISTS
# ==========================================================

def product_exists(product_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM products WHERE id=?",
        (product_id,)
    )

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


# ==========================================================
# CHECK CATEGORY EXISTS
# ==========================================================

def category_exists(category_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        "SELECT id FROM categories WHERE id=?",

        (category_id,)

    )

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


# ==========================================================
# BARCODE EXISTS
# ==========================================================

def barcode_exists(barcode, product_id=None):

    if barcode == "":
        return False

    conn = get_connection()

    cursor = conn.cursor()

    if product_id:

        cursor.execute("""

            SELECT id

            FROM products

            WHERE barcode=?

            AND id<>?

        """,

        (

            barcode,

            product_id

        ))

    else:

        cursor.execute("""

            SELECT id

            FROM products

            WHERE barcode=?

        """,

        (

            barcode,

        ))

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


# ==========================================================
# INVENTORY HEALTH CHECK
# ==========================================================

@inventory_bp.route(

    "/inventory/health",

    methods=["GET"]

)

def inventory_health():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(

            "SELECT COUNT(*) FROM products"

        )

        conn.close()

        return success(

            "Inventory Module Running",

            {

                "module":"Inventory",

                "status":"OK"

            }

        )

    except Exception as e:

        print(e)

        return error(

            "Inventory Module Failed",

            500

        )


# ==========================================================
# GLOBAL ERROR HANDLER
# ==========================================================

@inventory_bp.errorhandler(Exception)

def inventory_exception(error_obj):

    current_app.logger.exception("Inventory request failed", exc_info=error_obj)

    return jsonify({

        "success":False,

        "message":"Inventory request failed. Please retry or contact a manager."

    }),500

# ==========================================================
# TEMPORARY MENU IMPORT
# ==========================================================

@inventory_bp.route("/import-menu", methods=["POST"])
@login_required
def import_menu():
    # The old endpoint executed a bundled SQL dump after deleting the live
    # catalog. Keep the route retired so a stale client cannot erase products.
    return jsonify({
        "success": False,
        "message": "Legacy menu import is disabled because it could overwrite your current catalog. Manage products from Inventory."
    }), 410

# ==========================================================
# END OF FILE
# ==========================================================
