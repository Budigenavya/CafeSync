from flask import Blueprint, request, jsonify
from models import get_connection

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# --------------------------------------
# Login
# --------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and Password are required."
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               username,
               role,
               full_name
        FROM users
        WHERE username = ?
        AND password = ?
    """, (username, password))

    user = cursor.fetchone()

    conn.close()

    if user:

        return jsonify({
            "success": True,
            "message": "Login Successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "name": user["full_name"],
                "role": user["role"]
            }
        })

    return jsonify({
        "success": False,
        "message": "Invalid Username or Password"
    }), 401


# --------------------------------------
# Logout
# --------------------------------------
@auth_bp.route("/logout", methods=["POST"])
def logout():

    return jsonify({
        "success": True,
        "message": "Logged Out Successfully"
    })


# --------------------------------------
# Change Password
# --------------------------------------
@auth_bp.route("/change-password", methods=["POST"])
def change_password():

    data = request.get_json()

    username = data.get("username")
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE username=?
        AND password=?
    """, (username, old_password))

    user = cursor.fetchone()

    if not user:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Old password is incorrect."
        }), 400

    cursor.execute("""
        UPDATE users
        SET password=?
        WHERE username=?
    """, (new_password, username))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Password Changed Successfully"
    })


# --------------------------------------
# User Profile
# --------------------------------------
@auth_bp.route("/profile/<int:user_id>", methods=["GET"])
def profile(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               username,
               full_name,
               role
        FROM users
        WHERE id=?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    return jsonify({
        "success": True,
        "user": dict(user)
    })


# --------------------------------------
# List Operators
# --------------------------------------
@auth_bp.route("/operators", methods=["GET"])
def operators():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            full_name,
            username,
            role
        FROM users
        ORDER BY full_name
    """)

    users = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(users)