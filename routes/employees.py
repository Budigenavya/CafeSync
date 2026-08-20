from flask import Blueprint, request, jsonify
from models import get_connection

employees_bp = Blueprint("employees", __name__)

# ---------------------------------
# GET ALL EMPLOYEES
# ---------------------------------
@employees_bp.route("/employees", methods=["GET"])
def get_employees():

    conn = get_connection()

    employees = conn.execute("""
    SELECT *
    FROM employees
    ORDER BY id
    """).fetchall()

    conn.close()

    return jsonify([
        dict(emp)
        for emp in employees
    ])


# ---------------------------------
# GET SINGLE EMPLOYEE
# ---------------------------------
@employees_bp.route("/employee/<int:employee_id>", methods=["GET"])
def get_employee(employee_id):

    conn = get_connection()

    employee = conn.execute("""
    SELECT *
    FROM employees
    WHERE id=?
    """, (employee_id,)).fetchone()

    conn.close()

    if employee:

        return jsonify(dict(employee))

    return jsonify({
        "success": False,
        "message": "Employee Not Found"
    }), 404


# ---------------------------------
# ADD EMPLOYEE
# ---------------------------------
@employees_bp.route("/add-employee", methods=["POST"])
def add_employee():

    data = request.json

    conn = get_connection()

    conn.execute("""
    INSERT INTO employees
    (
        name,
        role,
        phone,
        salary,
        joining_date
    )
    VALUES
    (
        ?,
        ?,
        ?,
        ?,
        ?
    )
    """,
    (
        data["name"],
        data["role"],
        data["phone"],
        data["salary"],
        data["joining_date"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Employee Added Successfully"
    })


# ---------------------------------
# UPDATE EMPLOYEE
# ---------------------------------
@employees_bp.route("/update-employee/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):

    data = request.json

    conn = get_connection()

    conn.execute("""
    UPDATE employees
    SET
        name=?,
        role=?,
        phone=?,
        salary=?,
        joining_date=?
    WHERE id=?
    """,
    (
        data["name"],
        data["role"],
        data["phone"],
        data["salary"],
        data["joining_date"],
        employee_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Employee Updated Successfully"
    })


# ---------------------------------
# DELETE EMPLOYEE
# ---------------------------------
@employees_bp.route("/delete-employee/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):

    conn = get_connection()

    conn.execute("""
    DELETE FROM employees
    WHERE id=?
    """, (employee_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Employee Deleted Successfully"
    })


# ---------------------------------
# SEARCH EMPLOYEE
# ---------------------------------
@employees_bp.route("/search-employee")
def search_employee():

    name = request.args.get("name", "")

    conn = get_connection()

    employees = conn.execute("""
    SELECT *
    FROM employees
    WHERE name LIKE ?
    ORDER BY name
    """, ('%' + name + '%',)).fetchall()

    conn.close()

    return jsonify([
        dict(emp)
        for emp in employees
    ])


# ---------------------------------
# EMPLOYEE COUNT
# ---------------------------------
@employees_bp.route("/employee-count")
def employee_count():

    conn = get_connection()

    total = conn.execute("""
    SELECT COUNT(*) AS total
    FROM employees
    """).fetchone()["total"]

    conn.close()

    return jsonify({
        "total_employees": total
    })


# ---------------------------------
# TOTAL MONTHLY SALARY
# ---------------------------------
@employees_bp.route("/salary-summary")
def salary_summary():

    conn = get_connection()

    total_salary = conn.execute("""
    SELECT IFNULL(SUM(salary),0) AS total
    FROM employees
    """).fetchone()["total"]

    conn.close()

    return jsonify({
        "monthly_salary": total_salary
    })