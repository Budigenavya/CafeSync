# ==========================================================
# IMPORTS
# ==========================================================

from flask import Blueprint
from flask import request
from flask import jsonify, render_template

from routes.auth import login_required

from database import get_connection

import sqlite3


# ==========================================================
# BLUEPRINT
# ==========================================================

inventory_bp = Blueprint(

    "inventory",

    __name__

)

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

    try:

        conn = get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.name,
                p.price,
                p.stock,
                p.barcode,
                p.category_id,
                c.name AS category_name
            FROM products p
            LEFT JOIN categories c
            ON p.category_id = c.id
            ORDER BY p.name
        """)

        products = [
            dict(row)
            for row in cursor.fetchall()
        ]

        conn.close()

        return success(
            "Products Loaded",
            products
        )

    except Exception as e:

        print(e)

        return jsonify({
            "success":False,
            "message":"Unable To Load Products"
        }),500

# ==========================================================
# ERROR RESPONSE
# ==========================================================

def error(message,status=400):

    return jsonify({

        "success":False,

        "message":message

    }),status

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

        data = request.get_json()

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

        data = request.get_json()

        name = data.get("name", "").strip()
        category_id = data.get("category_id")
        barcode = data.get("barcode", "").strip()
        price = data.get("price", 0)
        stock = data.get("stock", 0)

        if not name:

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

                return error(

                    "Barcode Already Exists"

                )

        cursor.execute("""

            INSERT INTO products(

                category_id,

                name,

                price,

                stock,

                barcode

            )

            VALUES(?,?,?,?,?)

        """,

        (

            category_id,

            name,

            price,

            stock,

            barcode

        ))

        conn.commit()

        conn.close()

        return success(

            "Product Added Successfully"

        )

    except Exception as e:

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

        data = request.get_json()

        name = data.get("name", "").strip()
        category_id = data.get("category_id")
        barcode = data.get("barcode", "").strip()
        price = data.get("price", 0)
        stock = data.get("stock", 0)

        conn = get_connection()

        cursor = conn.cursor()

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

                barcode=?

            WHERE id=?

        """,

        (

            category_id,

            name,

            price,

            stock,

            barcode,

            product_id

        ))

        conn.commit()

        conn.close()

        return success(

            "Product Updated Successfully"

        )

    except Exception as e:

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

        return success(

            "Product Deleted Successfully"

        )

    except Exception as e:

        print(e)

        return error(

            "Unable To Delete Product",

            500

        )
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

    print(error_obj)

    return jsonify({

        "success":False,

        "message":"Internal Server Error",

        "error":str(error_obj)

    }),500



# ==========================================================
# END OF FILE
# ==========================================================