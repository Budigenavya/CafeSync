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

    print("LOGIN DATA:", data)

    username = data.get("username")
    password = data.get("password")

    print("USERNAME:", username)
    print("PASSWORD:", password)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    print("DATABASE USER:", user)

    conn.close()

    if user:
        print("DB PASSWORD:", user["password"])

    if user and user["password"] == password:

    	session["logged_in"] = True

    	session["user_id"] = user["id"]

    	session["username"] = user["username"]

    	session["role"] = user["role"]

    	print("SESSION CREATED:", dict(session))

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


# ==========================================================
# VERIFY SESSION
# ==========================================================

@auth_bp.route("/verify-session", methods=["GET"])
def verify_session():

    print("CURRENT SESSION:", dict(session))

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

    if len(new_password) < 6:

        return jsonify({

            "success": False,

            "message":
            "Password must be at least 6 characters"

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

    password = generate_password_hash(

        "admin123"

    )

    execute_query("""

        UPDATE users

        SET password=?

        WHERE username='admin'

    """, (

        password,

    ))

    return jsonify({

        "success": True,

        "message":
        "Admin password reset to admin123"

    })
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