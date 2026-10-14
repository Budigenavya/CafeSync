from flask import Flask, jsonify, render_template, send_from_directory, session, request, redirect
from flask_cors import CORS
import os


# ==========================
# DATABASE
# ==========================

from database import create_tables, get_connection
from config import SECRET_KEY, UPLOAD_FOLDER, DEBUG, USE_POSTGRES


# ==========================
# BLUEPRINTS
# ==========================

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.inventory import inventory_bp
from routes.billing import billing_bp
from routes.kitchen import kitchen_bp
print(" KITCHEN IMPORTED INTO APP")
from routes.orders import orders_bp
from routes.employees import employees_bp
from routes.reports import reports_bp
from routes.settings import settings_bp
from routes.tables import tables_bp
from routes.delivery import delivery_bp



# ==========================
# FLASK APP
# ==========================

app = Flask(__name__)


@app.route("/manifest.webmanifest")
def pwa_manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")


@app.route("/service-worker.js")
def pwa_service_worker():
    response = send_from_directory(app.static_folder, "js/service-worker.js", mimetype="application/javascript")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/offline")
def pwa_offline_page():
    return render_template("offline.html")


# ==========================
# CONFIGURATION
# ==========================

app.config["SECRET_KEY"] = SECRET_KEY
app.config["DEBUG"] = DEBUG
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RENDER", "").lower() == "true"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024

if os.environ.get("RENDER") and not os.environ.get("CAFESYNC_DATA_DIR"):
    app.logger.critical(
        "CAFESYNC_DATA_DIR is not configured. Render's local filesystem is ephemeral; "
        "attach a persistent disk and set CAFESYNC_DATA_DIR to its mount path or cafe data can be lost on deploy."
    )


# Enable CORS with sessions
CORS(
    app,
    supports_credentials=True
)



# ==========================
# DATABASE INITIALIZATION
# ==========================

if USE_POSTGRES:
    app.logger.warning(
        "PostgreSQL mode is enabled; skipping automatic database initialization. "
        "Verify PostgreSQL compatibility before serving requests."
    )
else:
    create_tables()



# ==========================
# AUTHENTICATION CHECK
# ==========================

@app.before_request
def check_auth():

    # Allow static files
    if request.path.startswith("/static"):
        return


    # Public routes
    public_routes = [
        "/",
        "/login",
        "/verify-session",
        "/manifest.webmanifest",
        "/service-worker.js",
        "/offline"
    ]


    if request.path in public_routes:
        return


    # Allow favicon
    if request.path == "/favicon.ico":
        return


    # Check session
    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Authentication required"
        }), 401

    auth_conn = get_connection()
    try:
        active_user = auth_conn.execute("SELECT is_active FROM users WHERE id=?", (session["user_id"],)).fetchone()
    finally:
        auth_conn.close()
    if not active_user or not active_user[0]:
        session.clear()
        return jsonify({"success": False, "message": "This staff account is disabled. Contact a manager."}), 401

    role = str(session.get("role") or "").strip().lower()
    path = request.path
    method = request.method.upper()
    safe_methods = {"GET", "HEAD", "OPTIONS"}
    managers = {"admin", "owner", "manager"}
    if path.startswith(("/employees", "/employee", "/add-employee", "/update-employee", "/delete-employee")) and role not in managers:
        return jsonify({"success": False, "message": "Manager access is required for employee records."}), 403
    if path.startswith("/settings") and role not in managers:
        return jsonify({"success": False, "message": "Manager access is required for cafe settings."}), 403
    if path.startswith("/reports") and role not in managers:
        return jsonify({"success": False, "message": "Manager access is required for reports."}), 403
    if path.startswith("/inventory") and not safe_methods and role not in managers:
        return jsonify({"success": False, "message": "Manager access is required to change the menu or stock."}), 403
    if path.startswith("/orders/day-close") and role not in managers:
        return jsonify({"success": False, "message": "Manager access is required to close the business day."}), 403
    if method not in safe_methods and (
        path.startswith(("/billing/cancel/", "/billing/refund/", "/billing/delete/", "/orders/refund/", "/orders/cancel/"))
        or (path.startswith("/orders/") and method == "DELETE")
    ) and role not in managers:
        return jsonify({"success": False, "message": "Manager approval is required for cancellation, refunds, or deletion."}), 403
    if path in {"/auth/create-admin", "/create-admin", "/reset-admin-password"} and role not in {"admin", "owner"}:
        return jsonify({"success": False, "message": "Administrator access is required."}), 403



# ==========================
# REGISTER BLUEPRINTS
# ==========================

app.register_blueprint(
    auth_bp
)


app.register_blueprint(
    dashboard_bp
)


app.register_blueprint(
    inventory_bp
)


print(" ABOUT TO REGISTER BILLING")

app.register_blueprint(billing_bp)

print(" BILLING BLUEPRINT REGISTERED")

print("\n========== BILLING ROUTES ==========")

for rule in app.url_map.iter_rules():
    if rule.endpoint.startswith("billing."):
        print(rule, "->", rule.endpoint, rule.methods)


print(" ABOUT TO REGISTER KITCHEN")

app.register_blueprint(kitchen_bp)

print("\n========== ALL KITCHEN ROUTES ==========")

for rule in app.url_map.iter_rules():
    if "kitchen" in str(rule):
        print(rule, "->", rule.endpoint)
print(" REGISTERED KITCHEN BLUEPRINT")


app.register_blueprint(
    employees_bp
)


app.register_blueprint(
    reports_bp,
    url_prefix="/reports"
)


app.register_blueprint(
    settings_bp
)
app.register_blueprint(
    orders_bp
)


app.register_blueprint(
    tables_bp
)


app.register_blueprint(
    delivery_bp
)



# ==========================
# HOME PAGE
# ==========================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


# ==========================
# UPLOAD FILES
# ==========================

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )



# ==========================
# ERROR HANDLERS
# ==========================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "Page not found"
    }),404



@app.errorhandler(500)
def internal_error(error):

    return jsonify({
        "success": False,
        "message": "Internal server error"
    }),500



# ==========================
# START SERVER
# ==========================

print("\n========== ROUTES ==========")

for rule in app.url_map.iter_rules():
    print(rule)

print("============================")

if __name__ == "__main__":
    print(app.url_map)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
