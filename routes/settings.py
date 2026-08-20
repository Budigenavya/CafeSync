"""
==========================================================
                CafeSync POS
                settings.py
                PART 1
==========================================================
"""

from flask import Blueprint, jsonify, request, render_template

from models import fetch_one, execute_query
from routes.auth import login_required

settings_bp = Blueprint(
    "settings",
    __name__
)

@settings_bp.route("/settings")
@login_required
def settings():

    return render_template("settings.html")


# ==========================================================
# GET SETTINGS
# ==========================================================

@settings_bp.route(
    "/settings",
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
    methods=["PUT"]
)
def update_cafe_information():

    data = request.json

    execute_query("""

        UPDATE settings

        SET

            cafe_name=?,

            address=?,

            phone=?,

            email=?,

            gst_number=?

        WHERE id=1

    """, (

        data.get("cafe_name"),

        data.get("address"),

        data.get("phone"),

        data.get("email"),

        data.get("gst_number")

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

settings_bp = Blueprint("settings",__name__)

@settings_bp.route("/settings")
def settings():

    return render_template("settings.html")


# ==========================================================
# END OF SETTINGS MODULE
# ==========================================================