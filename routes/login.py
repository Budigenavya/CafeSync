from flask import Blueprint, request, jsonify
from models import get_connection

login_bp = Blueprint(
    "login",
    __name__,
    url_prefix="/login"
)


@login_bp.route("/", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            full_name,
            username,
            role
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
                "name": user["full_name"],
                "username": user["username"],
                "role": user["role"]
            }
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password."
    }), 401