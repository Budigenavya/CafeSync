"""
==========================================================
                CafeSync POS
                tables.py
                PART 1
==========================================================
"""

from flask import Blueprint, jsonify, request
from models import fetch_all, fetch_one, execute_query

tables_bp = Blueprint(
    "tables",
    __name__
)


# ==========================================================
# GET ALL TABLES
# ==========================================================

@tables_bp.route(
    "/tables",
    methods=["GET"]
)
def get_tables():

    rows = fetch_all("""

        SELECT *

        FROM tables

        ORDER BY table_name

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# AVAILABLE TABLES
# ==========================================================

@tables_bp.route(
    "/tables/available",
    methods=["GET"]
)
def available_tables():

    rows = fetch_all("""

        SELECT *

        FROM tables

        WHERE status='Available'

        ORDER BY table_name

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# GET TABLE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>",
    methods=["GET"]
)
def get_table(table_id):

    row = fetch_one("""

        SELECT *

        FROM tables

        WHERE id=?

    """,(table_id,))

    if not row:

        return jsonify({

            "success":False,

            "message":"Table not found"

        }),404

    return jsonify(dict(row))


# ==========================================================
# ADD TABLE
# ==========================================================

@tables_bp.route(
    "/tables",
    methods=["POST"]
)
def add_table():

    data = request.json

    execute_query("""

        INSERT INTO tables(

            table_name,

            capacity,

            status

        )

        VALUES(

            ?,?,?

        )

    """,(

        data.get("table_name"),

        data.get("capacity",4),

        "Available"

    ))

    return jsonify({

        "success":True,

        "message":"Table added"

    })
# ==========================================================
# UPDATE TABLE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>",
    methods=["PUT"]
)
def update_table(table_id):

    data = request.json

    table = fetch_one("""

        SELECT id

        FROM tables

        WHERE id=?

    """, (table_id,))

    if not table:

        return jsonify({

            "success": False,

            "message": "Table not found"

        }), 404

    execute_query("""

        UPDATE tables

        SET

            table_name=?,

            capacity=?

        WHERE id=?

    """, (

        data.get("table_name"),

        data.get("capacity", 4),

        table_id

    ))

    return jsonify({

        "success": True,

        "message": "Table updated"

    })


# ==========================================================
# DELETE TABLE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>",
    methods=["DELETE"]
)
def delete_table(table_id):

    table = fetch_one("""

        SELECT status

        FROM tables

        WHERE id=?

    """, (table_id,))

    if not table:

        return jsonify({

            "success": False,

            "message": "Table not found"

        }), 404

    if table["status"] == "Occupied":

        return jsonify({

            "success": False,

            "message": "Cannot delete an occupied table"

        }), 400

    execute_query("""

        DELETE FROM tables

        WHERE id=?

    """, (table_id,))

    return jsonify({

        "success": True,

        "message": "Table deleted"

    })


# ==========================================================
# CHANGE TABLE STATUS
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>/status",
    methods=["PUT"]
)
def change_table_status(table_id):

    data = request.json

    status = data.get("status")

    valid_status = [

        "Available",

        "Occupied",

        "Reserved",

        "Cleaning"

    ]

    if status not in valid_status:

        return jsonify({

            "success": False,

            "message": "Invalid table status"

        }), 400

    execute_query("""

        UPDATE tables

        SET status=?

        WHERE id=?

    """, (

        status,

        table_id

    ))

    return jsonify({

        "success": True,

        "message": "Table status updated"

    })


# ==========================================================
# TABLE SUMMARY
# ==========================================================

@tables_bp.route(
    "/tables/summary",
    methods=["GET"]
)
def table_summary():

    summary = fetch_one("""

        SELECT

            COUNT(*) AS total_tables,

            SUM(
                CASE
                    WHEN status='Available'
                    THEN 1
                    ELSE 0
                END
            ) AS available,

            SUM(
                CASE
                    WHEN status='Occupied'
                    THEN 1
                    ELSE 0
                END
            ) AS occupied,

            SUM(
                CASE
                    WHEN status='Reserved'
                    THEN 1
                    ELSE 0
                END
            ) AS reserved,

            SUM(
                CASE
                    WHEN status='Cleaning'
                    THEN 1
                    ELSE 0
                END
            ) AS cleaning

        FROM tables

    """)

    return jsonify(dict(summary))
# ==========================================================
# OCCUPY TABLE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>/occupy",
    methods=["PUT"]
)
def occupy_table(table_id):

    table = fetch_one("""

        SELECT *

        FROM tables

        WHERE id=?

    """,(table_id,))

    if not table:

        return jsonify({

            "success":False,

            "message":"Table not found"

        }),404

    if table["status"] == "Occupied":

        return jsonify({

            "success":False,

            "message":"Table already occupied"

        }),400

    execute_query("""

        UPDATE tables

        SET status='Occupied'

        WHERE id=?

    """,(table_id,))

    return jsonify({

        "success":True,

        "message":"Table occupied"

    })


# ==========================================================
# FREE TABLE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>/free",
    methods=["PUT"]
)
def free_table(table_id):

    table = fetch_one("""

        SELECT *

        FROM tables

        WHERE id=?

    """,(table_id,))

    if not table:

        return jsonify({

            "success":False,

            "message":"Table not found"

        }),404

    execute_query("""

        UPDATE tables

        SET status='Available'

        WHERE id=?

    """,(table_id,))

    return jsonify({

        "success":True,

        "message":"Table is now available"

    })


# ==========================================================
# CLEAN TABLE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>/clean",
    methods=["PUT"]
)
def clean_table(table_id):

    execute_query("""

        UPDATE tables

        SET status='Cleaning'

        WHERE id=?

    """,(table_id,))

    return jsonify({

        "success":True,

        "message":"Table marked for cleaning"

    })


# ==========================================================
# MARK CLEANING COMPLETE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>/cleaning-complete",
    methods=["PUT"]
)
def cleaning_complete(table_id):

    execute_query("""

        UPDATE tables

        SET status='Available'

        WHERE id=?

    """,(table_id,))

    return jsonify({

        "success":True,

        "message":"Cleaning completed"

    })


# ==========================================================
# RESERVE TABLE
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>/reserve",
    methods=["PUT"]
)
def reserve_table():

    table_id = request.view_args["table_id"]

    execute_query("""

        UPDATE tables

        SET status='Reserved'

        WHERE id=?

    """,(table_id,))

    return jsonify({

        "success":True,

        "message":"Table reserved"

    })


# ==========================================================
# CANCEL RESERVATION
# ==========================================================

@tables_bp.route(
    "/tables/<int:table_id>/cancel-reservation",
    methods=["PUT"]
)
def cancel_reservation(table_id):

    execute_query("""

        UPDATE tables

        SET status='Available'

        WHERE id=?

    """,(table_id,))

    return jsonify({

        "success":True,

        "message":"Reservation cancelled"

    })


# ==========================================================
# RESERVED TABLES
# ==========================================================

@tables_bp.route(
    "/tables/reserved",
    methods=["GET"]
)
def reserved_tables():

    rows = fetch_all("""

        SELECT *

        FROM tables

        WHERE status='Reserved'

        ORDER BY table_name

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])
# ==========================================================
# TABLE DASHBOARD
# ==========================================================

@tables_bp.route(
    "/tables/dashboard",
    methods=["GET"]
)
def table_dashboard():

    dashboard = fetch_one("""

        SELECT

            COUNT(*) AS total_tables,

            SUM(
                CASE
                    WHEN status='Available'
                    THEN 1 ELSE 0
                END
            ) AS available,

            SUM(
                CASE
                    WHEN status='Occupied'
                    THEN 1 ELSE 0
                END
            ) AS occupied,

            SUM(
                CASE
                    WHEN status='Reserved'
                    THEN 1 ELSE 0
                END
            ) AS reserved,

            SUM(
                CASE
                    WHEN status='Cleaning'
                    THEN 1 ELSE 0
                END
            ) AS cleaning

        FROM tables

    """)

    return jsonify({

        "success": True,

        "dashboard": dict(dashboard)

    })


# ==========================================================
# SEARCH TABLE
# ==========================================================

@tables_bp.route(
    "/tables/search",
    methods=["GET"]
)
def search_table():

    keyword = request.args.get(

        "q",

        ""

    )

    rows = fetch_all("""

        SELECT *

        FROM tables

        WHERE

            table_name LIKE ?

            OR

            status LIKE ?

        ORDER BY table_name

    """, (

        f"%{keyword}%",

        f"%{keyword}%"

    ))

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# TABLE STATISTICS
# ==========================================================

@tables_bp.route(
    "/tables/statistics",
    methods=["GET"]
)
def table_statistics():

    stats = {

        "total":

            fetch_one("""

                SELECT COUNT(*)

                AS total

                FROM tables

            """)["total"],

        "available":

            fetch_one("""

                SELECT COUNT(*)

                AS total

                FROM tables

                WHERE status='Available'

            """)["total"],

        "occupied":

            fetch_one("""

                SELECT COUNT(*)

                AS total

                FROM tables

                WHERE status='Occupied'

            """)["total"],

        "reserved":

            fetch_one("""

                SELECT COUNT(*)

                AS total

                FROM tables

                WHERE status='Reserved'

            """)["total"],

        "cleaning":

            fetch_one("""

                SELECT COUNT(*)

                AS total

                FROM tables

                WHERE status='Cleaning'

            """)["total"]

    }

    return jsonify({

        "success": True,

        "statistics": stats

    })


# ==========================================================
# TABLE CAPACITY REPORT
# ==========================================================

@tables_bp.route(
    "/tables/capacity",
    methods=["GET"]
)
def table_capacity():

    rows = fetch_all("""

        SELECT

            table_name,

            capacity,

            status

        FROM tables

        ORDER BY capacity DESC

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# OCCUPIED TABLES
# ==========================================================

@tables_bp.route(
    "/tables/occupied",
    methods=["GET"]
)
def occupied_tables():

    rows = fetch_all("""

        SELECT *

        FROM tables

        WHERE status='Occupied'

        ORDER BY table_name

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])


# ==========================================================
# CLEANING TABLES
# ==========================================================

@tables_bp.route(
    "/tables/cleaning",
    methods=["GET"]
)
def cleaning_tables():

    rows = fetch_all("""

        SELECT *

        FROM tables

        WHERE status='Cleaning'

        ORDER BY table_name

    """)

    return jsonify([

        dict(r)

        for r in rows

    ])
# ==========================================================
# TABLE STATUS
# ==========================================================

@tables_bp.route(
    "/tables/status",
    methods=["GET"]
)
def tables_status():

    return jsonify({

        "success": True,

        "module": "Tables",

        "status": "Running",

        "version": "1.0.0"

    })


# ==========================================================
# TABLE HEALTH
# ==========================================================

@tables_bp.route(
    "/tables/health",
    methods=["GET"]
)
def tables_health():

    total = fetch_one("""

        SELECT COUNT(*) AS total

        FROM tables

    """)

    return jsonify({

        "success": True,

        "database": "Connected",

        "tables":

            total["total"],

        "health": "Good"

    })


# ==========================================================
# TABLE INFO
# ==========================================================

@tables_bp.route(
    "/tables/info",
    methods=["GET"]
)
def tables_info():

    return jsonify({

        "application": "CafeSync POS",

        "module": "Tables",

        "supported_status": [

            "Available",

            "Occupied",

            "Reserved",

            "Cleaning"

        ]

    })


# ==========================================================
# PING
# ==========================================================

@tables_bp.route(
    "/tables/ping",
    methods=["GET"]
)
def tables_ping():

    return jsonify({

        "status": "OK"

    })


# ==========================================================
# RESET ALL TABLES
# ==========================================================

@tables_bp.route(
    "/tables/reset",
    methods=["PUT"]
)
def reset_tables():

    execute_query("""

        UPDATE tables

        SET status='Available'

    """)

    return jsonify({

        "success": True,

        "message": "All tables reset to Available"

    })


# ==========================================================
# BULK UPDATE TABLE STATUS
# ==========================================================

@tables_bp.route(
    "/tables/bulk-status",
    methods=["PUT"]
)
def bulk_update_status():

    data = request.json

    table_ids = data.get("table_ids", [])

    status = data.get("status")

    valid_status = [

        "Available",

        "Occupied",

        "Reserved",

        "Cleaning"

    ]

    if status not in valid_status:

        return jsonify({

            "success": False,

            "message": "Invalid status"

        }), 400

    if not table_ids:

        return jsonify({

            "success": False,

            "message": "No table IDs provided"

        }), 400

    placeholders = ",".join(["?"] * len(table_ids))

    query = f"""

        UPDATE tables

        SET status=?

        WHERE id IN ({placeholders})

    """

    execute_query(

        query,

        (status, *table_ids)

    )

    return jsonify({

        "success": True,

        "message": f"{len(table_ids)} table(s) updated"

    })


# ==========================================================
# END OF TABLES MODULE
# ==========================================================
