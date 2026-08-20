from flask import Flask, jsonify, render_template, send_from_directory, session, request, redirect
from flask_cors import CORS
import os


# ==========================
# DATABASE
# ==========================

from database import create_tables


# ==========================
# BLUEPRINTS
# ==========================

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.inventory import inventory_bp
from routes.billing import billing_bp
from routes.kitchen import kitchen_bp
print("🔥 KITCHEN IMPORTED INTO APP")
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


# ==========================
# CONFIGURATION
# ==========================

app.config["SECRET_KEY"] = "cafesync_secret_key"

app.config["UPLOAD_FOLDER"] = "uploads"

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# Enable CORS with sessions
CORS(
    app,
    supports_credentials=True
)



# ==========================
# DATABASE INITIALIZATION
# ==========================

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
        "/verify-session"
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


print("🔥 ABOUT TO REGISTER BILLING")

app.register_blueprint(billing_bp)

print("🔥 BILLING BLUEPRINT REGISTERED")

print("\n========== BILLING ROUTES ==========")

for rule in app.url_map.iter_rules():
    if rule.endpoint.startswith("billing."):
        print(rule, "->", rule.endpoint, rule.methods)


print("🔥 ABOUT TO REGISTER KITCHEN")

app.register_blueprint(kitchen_bp)

print("\n========== ALL KITCHEN ROUTES ==========")

for rule in app.url_map.iter_rules():
    if "kitchen" in str(rule):
        print(rule, "->", rule.endpoint)
print("🔥 REGISTERED KITCHEN BLUEPRINT")


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