"""
==========================================================
                CafeSync POS
                settings.py
                PART 1
==========================================================
"""

from flask import Blueprint, jsonify, request, render_template, send_file, session

from models import fetch_one, execute_query
from database import get_connection
from database import create_tables
from routes.auth import login_required
from config import DATABASE, ENABLE_SWIGGY, ENABLE_ZOMATO, SWIGGY_API_KEY, ZOMATO_API_KEY, PERSISTENT_DATA_DIR, USE_POSTGRES
import os
import sqlite3
import tempfile
from datetime import datetime

settings_bp = Blueprint(
    "settings",
    __name__
)


@settings_bp.route("/settings/integrations", methods=["GET"])
@login_required
def integration_status():
    if session.get("role") not in {"Admin", "Owner", "Manager"}:
        return jsonify({"success": False, "message": "Manager access is required."}), 403
    return jsonify({"success": True, "integrations": [
        {"name": "Swiggy", "enabled": ENABLE_SWIGGY, "credentials_configured": bool(SWIGGY_API_KEY), "connector_implemented": False, "status": "Provider connector and approved partner credentials required"},
        {"name": "Zomato", "enabled": ENABLE_ZOMATO, "credentials_configured": bool(ZOMATO_API_KEY), "connector_implemented": False, "status": "Provider connector and approved partner credentials required"},
        {"name": "Payment terminal", "enabled": False, "credentials_configured": False, "status": "Payment provider SDK and merchant credentials required"},
        {"name": "Online / QR ordering", "enabled": False, "credentials_configured": False, "status": "Customer ordering workflow and payment provider required"},
    ], "persistent_storage": bool(PERSISTENT_DATA_DIR)})


@settings_bp.route("/settings/backup", methods=["GET"])
@login_required
def download_database_backup():
    if USE_POSTGRES:
        return jsonify({"success": False, "message": "Use Supabase's database backup/export tools while PostgreSQL mode is enabled."}), 501
    temporary = tempfile.NamedTemporaryFile(prefix="cafesync-backup-", suffix=".db", delete=False)
    backup_path = temporary.name
    temporary.close()
    source = None
    target = None
    try:
        source = sqlite3.connect(DATABASE)
        target = sqlite3.connect(backup_path)
        source.backup(target)
        target.close()
        target = None
        source.close()
        source = None
        response = send_file(backup_path, as_attachment=True,
                             download_name=f"CafeSync_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                             mimetype="application/vnd.sqlite3")
        response.call_on_close(lambda: os.path.exists(backup_path) and os.remove(backup_path))
        return response
    except sqlite3.Error:
        if target:
            target.close()
        if source:
            source.close()
        try:
            os.remove(backup_path)
        except OSError:
            pass
        return jsonify({"success": False, "message": "Could not create a database backup."}), 500


@settings_bp.route("/settings/audit-log", methods=["GET"])
@login_required
def audit_log_api():
    if session.get("role") not in {"Admin", "Owner", "Manager"}:
        return jsonify({"success": False, "message": "Manager access is required."}), 403
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id,actor,action,entity_type,entity_id,details,created_at FROM audit_log ORDER BY id DESC LIMIT 250").fetchall()
        return jsonify({"success": True, "entries": [dict(row) for row in rows]})
    finally:
        conn.close()


@settings_bp.route("/settings/restore", methods=["POST"])
@login_required
def restore_database_backup():
    if USE_POSTGRES:
        return jsonify({"success": False, "message": "SQLite backup files cannot be restored into PostgreSQL. Use a PostgreSQL-format export and migration instead."}), 501
    if session.get("role") not in {"Admin", "Owner"}:
        return jsonify({"success": False, "message": "Only an administrator can restore a database."}), 403
    if str(request.form.get("confirm", "")).lower() != "true":
        return jsonify({"success": False, "message": "Confirm database replacement before restoring."}), 400
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"success": False, "message": "Choose a SQLite backup file."}), 400
    restore_path = None
    source = None
    target = None
    try:
        with tempfile.NamedTemporaryFile(prefix="cafesync-restore-", suffix=".db", delete=False) as temp:
            restore_path = temp.name
            upload.save(temp)
        source = sqlite3.connect(f"file:{restore_path}?mode=ro", uri=True)
        integrity = source.execute("PRAGMA quick_check").fetchone()
        required = {"users", "products", "orders", "order_items", "settings"}
        available = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not integrity or integrity[0] != "ok" or not required.issubset(available):
            return jsonify({"success": False, "message": "This file is not a valid CafeSync database backup."}), 400
        target = sqlite3.connect(DATABASE)
        source.backup(target)
        target.close()
        target = None
        source.close()
        source = None
        create_tables()
        return jsonify({"success": True, "message": "CafeSync database restored. Reload the app to use the restored data."})
    except (sqlite3.Error, OSError):
        return jsonify({"success": False, "message": "Could not restore this database backup."}), 500
    finally:
        if target:
            target.close()
        if source:
            source.close()
        if restore_path:
            try:
                os.remove(restore_path)
            except OSError:
                pass


@settings_bp.route("/settings/billing-preferences", methods=["GET", "PUT"])
def billing_preferences():
    if request.method == "GET":
        row = fetch_one("""
            SELECT tax_percentage, default_discount, maximum_discount,
                   allow_manual_discount, show_gst_on_receipt
            FROM settings WHERE id=1
        """)
        if not row:
            return jsonify({"success": False, "message": "Settings not found"}), 404
        return jsonify({"success": True, "settings": dict(row)})

    data = request.get_json(silent=True) or {}
    try:
        tax = float(data.get("tax_percentage", 5))
        default_discount = float(data.get("default_discount", 0))
        maximum_discount = float(data.get("maximum_discount", 30))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Enter valid percentages."}), 400
    if not all(0 <= value <= 100 for value in (tax, default_discount, maximum_discount)):
        return jsonify({"success": False, "message": "Percentages must be between 0 and 100."}), 400
    if default_discount > maximum_discount:
        return jsonify({"success": False, "message": "Default discount cannot exceed the maximum."}), 400

    execute_query("""
        UPDATE settings SET tax_percentage=?, default_discount=?, maximum_discount=?,
            allow_manual_discount=?, show_gst_on_receipt=? WHERE id=1
    """, (tax, default_discount, maximum_discount,
          1 if data.get("allow_manual_discount") else 0,
          1 if data.get("show_gst_on_receipt", True) else 0))
    return jsonify({"success": True, "message": "Billing preferences saved."})

@settings_bp.route("/settings")
@login_required
def settings():

    return render_template("settings.html")


# ==========================================================
# GET SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/data",
    methods=["GET"]
)
def get_settings():

    settings = fetch_one("""

        SELECT *

        FROM settings

        LIMIT 1

    """)

    if not settings:

        return jsonify({

            "success": False,

            "message": "Settings not found"

        }), 404

    return jsonify({

        "success": True,

        "settings": dict(settings)

    })


# ==========================================================
# UPDATE CAFE INFORMATION
# ==========================================================

@settings_bp.route(
    "/settings/cafe",
    methods=["GET", "PUT"]
)
def update_cafe_information():

    if request.method == "GET":
        settings = fetch_one("SELECT cafe_name,owner_name,address,phone,email,website,gst_number,receipt_header,receipt_footer FROM settings WHERE id=1")
        return jsonify({"success": bool(settings), "settings": dict(settings) if settings else {}})

    data = request.get_json(silent=True) or {}

    execute_query("""

        UPDATE settings

        SET

            cafe_name=?,

            address=?,

            phone=?,

            email=?,

            gst_number=?,

            owner_name=?,

            website=?

        WHERE id=1

    """, (

        data.get("cafe_name"),

        data.get("address"),

        data.get("phone"),

        data.get("email"),

        data.get("gst_number"),

        data.get("owner_name"),

        data.get("website")

    ))

    return jsonify({

        "success": True,

        "message": "Cafe information updated"

    })


# ==========================================================
# UPDATE TAX
# ==========================================================

@settings_bp.route(
    "/settings/tax",
    methods=["PUT"]
)
def update_tax():

    data = request.json

    execute_query("""

        UPDATE settings

        SET tax_percentage=?

        WHERE id=1

    """, (

        data.get("tax_percentage", 5),

    ))

    return jsonify({

        "success": True,

        "message": "Tax updated"

    })


# ==========================================================
# UPDATE CURRENCY
# ==========================================================

@settings_bp.route(
    "/settings/currency",
    methods=["PUT"]
)
def update_currency():

    data = request.json

    execute_query("""

        UPDATE settings

        SET currency_symbol=?

        WHERE id=1

    """, (

        data.get("currency_symbol", "₹"),

    ))

    return jsonify({

        "success": True,

        "message": "Currency updated"

    })
# ==========================================================
# UPDATE RECEIPT SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/receipt",
    methods=["PUT"]
)
def update_receipt():

    data = request.json

    execute_query("""

        UPDATE settings

        SET

            receipt_header=?,

            receipt_footer=?

        WHERE id=1

    """, (

        data.get("receipt_header", ""),

        data.get("receipt_footer", "")

    ))

    return jsonify({

        "success": True,

        "message": "Receipt settings updated"

    })


# ==========================================================
# UPDATE BUSINESS HOURS
# ==========================================================

@settings_bp.route(
    "/settings/business-hours",
    methods=["PUT"]
)
def update_business_hours():

    data = request.json

    execute_query("""

        UPDATE settings

        SET

            opening_time=?,

            closing_time=?

        WHERE id=1

    """, (

        data.get("opening_time"),

        data.get("closing_time")

    ))

    return jsonify({

        "success": True,

        "message": "Business hours updated"

    })


# ==========================================================
# UPDATE THEME
# ==========================================================

@settings_bp.route(
    "/settings/theme",
    methods=["PUT"]
)
def update_theme():

    data = request.json

    theme = data.get("theme", "light")

    if theme not in ["light", "dark"]:

        return jsonify({

            "success": False,

            "message": "Theme must be 'light' or 'dark'"

        }), 400

    execute_query("""

        UPDATE settings

        SET theme=?

        WHERE id=1

    """, (

        theme,

    ))

    return jsonify({

        "success": True,

        "message": "Theme updated"

    })


# ==========================================================
# UPDATE POS SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/pos",
    methods=["PUT"]
)
def update_pos_settings():

    data = request.json

    execute_query("""

        UPDATE settings

        SET

            default_payment_method=?,

            default_order_type=?

        WHERE id=1

    """, (

        data.get("default_payment_method", "Cash"),

        data.get("default_order_type", "Take Away")

    ))

    return jsonify({

        "success": True,

        "message": "POS settings updated"

    })


# ==========================================================
# GET BUSINESS HOURS
# ==========================================================

@settings_bp.route(
    "/settings/business-hours",
    methods=["GET"]
)
def get_business_hours():

    result = fetch_one("""

        SELECT

            opening_time,

            closing_time

        FROM settings

        WHERE id=1

    """)

    return jsonify(dict(result))


# ==========================================================
# GET RECEIPT SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/receipt",
    methods=["GET"]
)
def get_receipt_settings():

    result = fetch_one("""

        SELECT

            receipt_header,

            receipt_footer

        FROM settings

        WHERE id=1

    """)

    return jsonify(dict(result))
# ==========================================================
# UPDATE DASHBOARD SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/dashboard",
    methods=["PUT"]
)
def update_dashboard_settings():

    data = request.json

    execute_query("""

        UPDATE settings

        SET

            dashboard_refresh=?,

            dashboard_chart_days=?

        WHERE id=1

    """, (

        data.get("dashboard_refresh", 30),

        data.get("dashboard_chart_days", 7)

    ))

    return jsonify({

        "success": True,

        "message": "Dashboard settings updated"

    })


# ==========================================================
# UPDATE NOTIFICATION SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/notifications",
    methods=["PUT"]
)
def update_notifications():

    data = request.json

    execute_query("""

        UPDATE settings

        SET

            low_stock_alert=?,

            order_notification=?

        WHERE id=1

    """, (

        int(data.get("low_stock_alert", True)),

        int(data.get("order_notification", True))

    ))

    return jsonify({

        "success": True,

        "message": "Notification settings updated"

    })


# ==========================================================
# GET DASHBOARD SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/dashboard",
    methods=["GET"]
)
def get_dashboard_settings():

    settings = fetch_one("""

        SELECT

            dashboard_refresh,

            dashboard_chart_days

        FROM settings

        WHERE id=1

    """)

    return jsonify(dict(settings))


# ==========================================================
# GET NOTIFICATION SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/notifications",
    methods=["GET"]
)
def get_notification_settings():

    settings = fetch_one("""

        SELECT

            low_stock_alert,

            order_notification

        FROM settings

        WHERE id=1

    """)

    return jsonify(dict(settings))


# ==========================================================
# SYSTEM SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/system",
    methods=["GET"]
)
def system_settings():

    settings = fetch_one("""

        SELECT

            cafe_name,

            theme,

            currency_symbol,

            tax_percentage,

            opening_time,

            closing_time

        FROM settings

        WHERE id=1

    """)

    return jsonify({

        "success": True,

        "system": dict(settings)

    })


# ==========================================================
# DISPLAY SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/display",
    methods=["GET"]
)
def display_settings():

    settings = fetch_one("""

        SELECT

            theme,

            currency_symbol

        FROM settings

        WHERE id=1

    """)

    return jsonify({

        "success": True,

        "display": dict(settings)

    })
# ==========================================================
# SETTINGS SUMMARY
# ==========================================================

@settings_bp.route(
    "/settings/summary",
    methods=["GET"]
)
def settings_summary():

    settings = fetch_one("""

        SELECT

            cafe_name,

            phone,

            email,

            gst_number,

            tax_percentage,

            currency_symbol,

            theme,

            opening_time,

            closing_time

        FROM settings

        WHERE id=1

    """)

    return jsonify({

        "success": True,

        "summary": dict(settings)

    })


# ==========================================================
# VALIDATE SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/validate",
    methods=["GET"]
)
def validate_settings():

    settings = fetch_one("""

        SELECT *

        FROM settings

        WHERE id=1

    """)

    errors = []

    if not settings["cafe_name"]:
        errors.append("Cafe name is missing")

    if not settings["phone"]:
        errors.append("Phone number is missing")

    if not settings["currency_symbol"]:
        errors.append("Currency symbol is missing")

    if settings["tax_percentage"] is None:
        errors.append("Tax percentage is missing")

    return jsonify({

        "success": len(errors) == 0,

        "errors": errors

    })


# ==========================================================
# RESET APPEARANCE
# ==========================================================

@settings_bp.route(
    "/settings/reset-theme",
    methods=["PUT"]
)
def reset_theme():

    execute_query("""

        UPDATE settings

        SET

            theme='light'

        WHERE id=1

    """)

    return jsonify({

        "success": True,

        "message": "Theme reset successfully"

    })


# ==========================================================
# RESET SETTINGS TO DEFAULT
# ==========================================================

@settings_bp.route(
    "/settings/reset",
    methods=["PUT"]
)
def reset_settings():

    execute_query("""

        UPDATE settings

        SET

            tax_percentage=5,

            currency_symbol='₹',

            theme='light',

            opening_time='09:00',

            closing_time='22:00',

            dashboard_refresh=30,

            dashboard_chart_days=7,

            low_stock_alert=1,

            order_notification=1,

            default_payment_method='Cash',

            default_order_type='Take Away'

        WHERE id=1

    """)

    return jsonify({

        "success": True,

        "message": "Settings restored to default"

    })


# ==========================================================
# DEFAULT CONFIGURATION
# ==========================================================

@settings_bp.route(
    "/settings/defaults",
    methods=["GET"]
)
def default_configuration():

    return jsonify({

        "theme": "light",

        "currency_symbol": "₹",

        "tax_percentage": 5,

        "opening_time": "09:00",

        "closing_time": "22:00",

        "dashboard_refresh": 30,

        "dashboard_chart_days": 7,

        "default_payment_method": "Cash",

        "default_order_type": "Take Away"

    })


# ==========================================================
# SETTINGS VERSION
# ==========================================================

@settings_bp.route(
    "/settings/version",
    methods=["GET"]
)
def settings_version():

    return jsonify({

        "module": "Settings",

        "version": "1.0.0"

    })
# ==========================================================
# SETTINGS STATUS
# ==========================================================

@settings_bp.route(
    "/settings/status",
    methods=["GET"]
)
def settings_status():

    return jsonify({

        "success": True,

        "module": "Settings",

        "status": "Running",

        "version": "1.0.0"

    })


# ==========================================================
# SETTINGS HEALTH
# ==========================================================

@settings_bp.route(
    "/settings/health",
    methods=["GET"]
)
def settings_health():

    settings = fetch_one("""

        SELECT COUNT(*) AS total

        FROM settings

    """)

    return jsonify({

        "success": True,

        "database": "Connected",

        "settings_records":

            settings["total"],

        "health": "Good"

    })


# ==========================================================
# SETTINGS INFORMATION
# ==========================================================

@settings_bp.route(
    "/settings/info",
    methods=["GET"]
)
def settings_info():

    return jsonify({

        "application": "CafeSync POS",

        "module": "Settings",

        "description":

            "Manages cafe configuration and POS preferences.",

        "features": [

            "Cafe Information",

            "Tax Settings",

            "Currency",

            "Receipt",

            "Business Hours",

            "Theme",

            "Dashboard",

            "Notifications"

        ]

    })


# ==========================================================
# PING
# ==========================================================

@settings_bp.route(
    "/settings/ping",
    methods=["GET"]
)
def settings_ping():

    return jsonify({

        "status": "OK"

    })


# ==========================================================
# EXPORT SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/export",
    methods=["GET"]
)
def export_settings():

    settings = fetch_one("""

        SELECT *

        FROM settings

        WHERE id=1

    """)

    return jsonify({

        "success": True,

        "settings": dict(settings)

    })


# ==========================================================
# IMPORT SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings/import",
    methods=["POST"]
)
def import_settings():

    data = request.json

    execute_query("""

        UPDATE settings

        SET

            cafe_name=?,

            address=?,

            phone=?,

            email=?,

            gst_number=?,

            tax_percentage=?,

            currency_symbol=?,

            receipt_header=?,

            receipt_footer=?,

            opening_time=?,

            closing_time=?,

            theme=?

        WHERE id=1

    """, (

        data.get("cafe_name"),

        data.get("address"),

        data.get("phone"),

        data.get("email"),

        data.get("gst_number"),

        data.get("tax_percentage"),

        data.get("currency_symbol"),

        data.get("receipt_header"),

        data.get("receipt_footer"),

        data.get("opening_time"),

        data.get("closing_time"),

        data.get("theme")

    ))

    return jsonify({

        "success": True,

        "message": "Settings imported successfully"

    })




# ==========================================================
# END OF SETTINGS MODULE
# ==========================================================
