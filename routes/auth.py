"""
==========================================================
                CafeSync POS
                auth.py
                PART 1
==========================================================
"""

from functools import wraps
from flask import Blueprint, session, jsonify, redirect, url_for, request, render_template

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)
import hmac
import json
import sqlite3

from models import (
    fetch_one,
    execute_query
)

from database import get_connection

auth_bp = Blueprint(
    "auth",
    __name__
)

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("auth.login_page")
            )

        return func(*args, **kwargs)

    return wrapper

# ==========================================================
# LOGIN PAGE
# ==========================================================

@auth_bp.route("/login", methods=["GET"])
def login_page():

    return render_template("login.html")



# ==========================================================
# LOGIN
# ==========================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Enter your username and password."}), 400

    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    password_matches = False
    if user and password:
        stored_password = str(user["password"] or "")
        if stored_password.startswith(("scrypt:", "pbkdf2:")):
            try:
                password_matches = check_password_hash(stored_password, password)
            except ValueError:
                password_matches = False
        else:
            password_matches = hmac.compare_digest(stored_password, password)
            if password_matches:
                execute_query("UPDATE users SET password=? WHERE id=?", (generate_password_hash(password), user["id"]))

    if user and password_matches and user["is_active"]:

    	session["logged_in"] = True

    	session["user_id"] = user["id"]

    	session["username"] = user["username"]

    	session["role"] = user["role"]

    	return jsonify({

            "success": True,

            "message": "Login successful"

    	})

    return jsonify({
        "success": False,
        "message": "Invalid credentials"
    }),401


# ==========================================================
# LOGOUT
# ==========================================================

@auth_bp.route(
    "/logout",
    methods=["POST"]
)
def logout():

    session.clear()

    return jsonify({

        "success":True,

        "message":"Logged out"

    })


# ==========================================================
# LOGIN STATUS
# ==========================================================

@auth_bp.route(
    "/login-status",
    methods=["GET"]
)
def login_status():

    return jsonify({

        "logged_in":

            session.get(

                "logged_in",

                False

            ),

        "username":

            session.get(

                "username"

            )

    })


# ==========================================================
# CREATE DEFAULT ADMIN
# Run only once
# ==========================================================

@auth_bp.route(
    "/create-admin",
    methods=["POST"]
)
def create_admin():

    if session.get("role") not in {"Admin", "Owner"}:
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    return jsonify({"success": False, "message": "Use Staff Logins & Permissions to manage accounts."}), 410

    admin = fetch_one("""

        SELECT id

        FROM users

        WHERE username='admin'

    """)

    if admin:

        return jsonify({

            "success":False,

            "message":"Admin already exists"

        })

    password = generate_password_hash(

        "admin123"

    )

    execute_query("""

        INSERT INTO users(

            username,

            password,

            full_name

        )

        VALUES(

            ?,?,?

        )

    """,(

        "admin",

        password,

        "Administrator"

    ))

    return jsonify({

        "success":True,

        "message":"Admin created"

    })
# ==========================================================
# CURRENT USER
# ==========================================================

@auth_bp.route(
    "/me",
    methods=["GET"]
)
def current_user():

    if not session.get("logged_in"):

        return jsonify({

            "success": False,

            "message": "Not logged in"

        }), 401

    user = fetch_one("""

        SELECT

            id,

            username,

            full_name,

            created_at

        FROM users

        WHERE id=?

    """, (

        session["user_id"],

    ))

    if not user:

        session.clear()

        return jsonify({

            "success": False,

            "message": "User not found"

        }), 404

    return jsonify({

        "success": True,

        "user": dict(user)

    })


@auth_bp.route("/auth/users", methods=["GET", "POST"])
@login_required
def manage_users():
    if session.get("role") not in {"Admin", "Owner"}:
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    conn = get_connection()
    try:
        if request.method == "GET":
            rows = conn.execute("SELECT id,full_name,username,role,is_active,created_at FROM users ORDER BY full_name").fetchall()
            return jsonify({"success": True, "users": [dict(row) for row in rows]})
        data = request.get_json(silent=True) or {}
        full_name = str(data.get("full_name") or "").strip()[:100]
        username = str(data.get("username") or "").strip()[:60]
        password = str(data.get("password") or "")
        role = str(data.get("role") or "").strip()
        if not full_name or not username or len(password) < 10 or role not in {"Manager", "Cashier", "Kitchen"}:
            return jsonify({"success": False, "message": "Enter a name, username, password with at least 10 characters, and a valid staff role."}), 400
        cursor = conn.execute("INSERT INTO users(full_name,username,password,role) VALUES(?,?,?,?)",
                              (full_name, username, generate_password_hash(password), role))
        conn.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                     (session.get("username", ""), "staff_user_created", "user", str(cursor.lastrowid), json.dumps({"username": username, "role": role})))
        conn.commit()
        return jsonify({"success": True, "message": "Staff login created.", "id": cursor.lastrowid}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"success": False, "message": "That username is already in use."}), 409
    finally:
        conn.close()


@auth_bp.route("/auth/users/<int:user_id>", methods=["PUT"])
@login_required
def update_staff_user(user_id):
    if session.get("role") not in {"Admin", "Owner"}:
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    data = request.get_json(silent=True) or {}
    conn = get_connection()
    try:
        user = conn.execute("SELECT username,role,is_active FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return jsonify({"success": False, "message": "Staff login not found."}), 404
        if "is_active" in data:
            active = data["is_active"]
            if not isinstance(active, bool):
                return jsonify({"success": False, "message": "Active must be true or false."}), 400
            if user_id == session.get("user_id") and not active:
                return jsonify({"success": False, "message": "You cannot deactivate your own account."}), 409
            if user["role"] in {"Admin", "Owner"} and not active:
                other_admin = conn.execute("SELECT 1 FROM users WHERE id<>? AND role IN ('Admin','Owner') AND is_active=1 LIMIT 1", (user_id,)).fetchone()
                if not other_admin:
                    return jsonify({"success": False, "message": "Keep at least one active administrator account."}), 409
            conn.execute("UPDATE users SET is_active=? WHERE id=?", (int(active), user_id))
        if data.get("role"):
            role = str(data["role"])
            if role not in {"Manager", "Cashier", "Kitchen"}:
                return jsonify({"success": False, "message": "Choose Manager, Cashier, or Kitchen."}), 400
            if user["role"] in {"Admin", "Owner"}:
                return jsonify({"success": False, "message": "Administrator accounts cannot be downgraded here."}), 409
            conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
        if data.get("password"):
            password = str(data["password"])
            if len(password) < 10:
                return jsonify({"success": False, "message": "Passwords must have at least 10 characters."}), 400
            conn.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(password), user_id))
        conn.execute("INSERT INTO audit_log(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                     (session.get("username", ""), "staff_user_updated", "user", str(user_id), json.dumps({key: data[key] for key in ("role", "is_active") if key in data})))
        conn.commit()
        return jsonify({"success": True, "message": "Staff login updated."})
    finally:
        conn.close()


# ==========================================================
# VERIFY SESSION
# ==========================================================

@auth_bp.route("/verify-session", methods=["GET"])
def verify_session():
    if "user_id" in session:

        return jsonify({
            "success": True,
            "username": session["username"],
            "role": session["role"]
        })

    return jsonify({
        "success": False,
        "message": "Authentication required"
    }),401


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@auth_bp.route(
    "/change-password",
    methods=["PUT"]
)
def change_password():

    if not session.get("logged_in"):

        return jsonify({

            "success": False,

            "message": "Login required"

        }), 401

    data = request.json

    old_password = data.get(

        "old_password",

        ""

    )

    new_password = data.get(

        "new_password",

        ""

    )

    if len(new_password) < 10:

        return jsonify({

            "success": False,

            "message":
            "Password must be at least 10 characters"

        }), 400

    user = fetch_one("""

        SELECT *

        FROM users

        WHERE id=?

    """, (

        session["user_id"],

    ))

    if not check_password_hash(

        user["password"],

        old_password

    ):

        return jsonify({

            "success": False,

            "message": "Old password is incorrect"

        }), 400

    hashed = generate_password_hash(

        new_password

    )

    execute_query("""

        UPDATE users

        SET password=?

        WHERE id=?

    """, (

        hashed,

        user["id"]

    ))

    return jsonify({

        "success": True,

        "message":
        "Password changed successfully"

    })


# ==========================================================
# RESET ADMIN PASSWORD
# (Development only)
# ==========================================================

@auth_bp.route(
    "/reset-admin-password",
    methods=["POST"]
)
def reset_admin_password():
    if session.get("role") not in {"Admin", "Owner"}:
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    return jsonify({"success": False, "message": "Use Change Password to set a new password securely."}), 410
# ==========================================================
# GET ADMIN PROFILE
# ==========================================================

@auth_bp.route(
    "/profile",
    methods=["GET"]
)
def get_profile():

    if not session.get("logged_in"):

        return jsonify({

            "success":False,

            "message":"Login required"

        }),401

    user = fetch_one("""

        SELECT

            id,

            username,

            full_name,

            created_at

        FROM users

        WHERE id=?

    """,(

        session["user_id"],

    ))

    if not user:

        return jsonify({

            "success":False,

            "message":"User not found"

        }),404

    return jsonify({

        "success":True,

        "profile":dict(user)

    })


# ==========================================================
# UPDATE PROFILE
# ==========================================================

@auth_bp.route(
    "/profile",
    methods=["PUT"]
)
def update_profile():

    if not session.get("logged_in"):

        return jsonify({

            "success":False,

            "message":"Login required"

        }),401

    data = request.json

    full_name = data.get(

        "full_name",

        ""

    ).strip()

    execute_query("""

        UPDATE users

        SET full_name=?

        WHERE id=?

    """,(

        full_name,

        session["user_id"]

    ))

    return jsonify({

        "success":True,

        "message":"Profile updated"

    })


# ==========================================================
# ACCOUNT INFORMATION
# ==========================================================

@auth_bp.route(
    "/account",
    methods=["GET"]
)
def account_information():

    if not session.get("logged_in"):

        return jsonify({

            "success":False,

            "message":"Login required"

        }),401

    user = fetch_one("""

        SELECT

            username,

            full_name,

            created_at

        FROM users

        WHERE id=?

    """,(

        session["user_id"],

    ))

    return jsonify({

        "success":True,

        "account":dict(user)

    })


# ==========================================================
# SECURITY STATUS
# ==========================================================

@auth_bp.route(
    "/security",
    methods=["GET"]
)
def security_status():

    if not session.get("logged_in"):

        return jsonify({

            "success":False,

            "message":"Login required"

        }),401

    return jsonify({

        "success":True,

        "session_active":True,

        "username":

            session.get(

                "username"

            ),

        "authentication":

            "Session"

    })


# ==========================================================
# CHANGE USERNAME
# ==========================================================

@auth_bp.route(
    "/change-username",
    methods=["PUT"]
)
def change_username():

    if not session.get("logged_in"):

        return jsonify({

            "success":False,

            "message":"Login required"

        }),401

    data = request.json

    username = data.get(

        "username",

        ""

    ).strip()

    if username == "":

        return jsonify({

            "success":False,

            "message":"Username required"

        }),400

    existing = fetch_one("""

        SELECT id

        FROM users

        WHERE username=?

    """,(

        username,

    ))

    if existing:

        return jsonify({

            "success":False,

            "message":"Username already exists"

        }),400

    execute_query("""

        UPDATE users

        SET username=?

        WHERE id=?

    """,(

        username,

        session["user_id"]

    ))

    session["username"] = username

    return jsonify({

        "success":True,

        "message":"Username updated",

        "username":username

    })


# ==========================================================
# DELETE SESSION
# ==========================================================

@auth_bp.route(
    "/session",
    methods=["DELETE"]
)
def delete_session():

    session.clear()

    return jsonify({

        "success":True,

        "message":"Session ended"

    })
from functools import wraps


# ==========================================================
# LOGIN REQUIRED DECORATOR
# ==========================================================

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return jsonify({
                "success": False,
                "message": "Authentication required"
            }),401

        return func(*args, **kwargs)

    return wrapper


# ==========================================================
# AUTH HEALTH CHECK
# ==========================================================

@auth_bp.route(
    "/auth/status",
    methods=["GET"]
)
def auth_status():

    return jsonify({

        "service": "Authentication",

        "status": "Running",

        "authentication": "Session",

        "version": "1.0.0"

    })


# ==========================================================
# CHECK AUTHENTICATION
# ==========================================================

@auth_bp.route(
    "/auth/check",
    methods=["GET"]
)
@login_required
def auth_check():

    return jsonify({

        "success": True,

        "authenticated": True,

        "username":

            session.get(

                "username"

            )

    })


# ==========================================================
# REFRESH SESSION
# ==========================================================

@auth_bp.route(
    "/auth/refresh",
    methods=["POST"]
)
@login_required
def refresh_session():

    session.permanent = True

    return jsonify({

        "success": True,

        "message": "Session refreshed"

    })


# ==========================================================
# LOGOUT ALL
# (Single-admin version)
# ==========================================================

@auth_bp.route(
    "/logout-all",
    methods=["POST"]
)
@login_required
def logout_all():

    session.clear()

    return jsonify({

        "success": True,

        "message": "Logged out"

    })


# ==========================================================
# APPLICATION INFO
# ==========================================================

@auth_bp.route(
    "/auth/info",
    methods=["GET"]
)
def auth_info():

    return jsonify({

        "application": "CafeSync POS",

        "authentication": "Session Based",

        "roles": [

            "Admin"

        ],

        "multi_user": False

    })


# ==========================================================
# END OF AUTH MODULE
# ==========================================================
