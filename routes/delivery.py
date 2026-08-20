"""
==========================================================
                CafeSync POS
                delivery.py
                PART 1
==========================================================
"""

from flask import Blueprint, jsonify, request, render_template
from database import get_connection
from routes.auth import login_required

# ==========================================================
# BLUEPRINT
# ==========================================================

delivery_bp = Blueprint(
    "delivery",
    __name__
)

@delivery_bp.route("/delivery")
@login_required
def delivery():

    return render_template("delivery.html")

# ==========================================================
# GET ALL DELIVERY ORDERS
# ==========================================================

@delivery_bp.route("/delivery/orders", methods=["GET"])
def get_delivery_orders():

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.order_number,
                o.customer_name,
                o.phone,
                o.address,
                o.total,
                o.status,
                o.payment_status,
                o.platform,
                o.created_at
            FROM orders o
            WHERE o.platform IN
            ('Swiggy','Zomato','Website','TakeAway')
            ORDER BY o.created_at DESC
        """)

        rows = cursor.fetchall()

        orders = []

        for row in rows:

            orders.append({

                "id": row["id"],

                "order_number": row["order_number"],

                "customer_name": row["customer_name"],

                "phone": row["phone"],

                "address": row["address"],

                "platform": row["platform"],

                "status": row["status"],

                "payment_status": row["payment_status"],

                "total": float(row["total"]),

                "time": row["created_at"]

            })

        conn.close()

        return jsonify(orders)

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# DELIVERY DASHBOARD SUMMARY
# ==========================================================

@delivery_bp.route("/delivery/dashboard", methods=["GET"])
def delivery_dashboard():

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT COUNT(*) AS total_orders

            FROM orders

            WHERE platform IN
            ('Swiggy','Zomato','Website','TakeAway')

        """)

        total_orders = cursor.fetchone()["total_orders"]

        cursor.execute("""

            SELECT IFNULL(SUM(total),0) AS revenue

            FROM orders

            WHERE platform IN
            ('Swiggy','Zomato','Website','TakeAway')

        """)

        revenue = cursor.fetchone()["revenue"]

        cursor.execute("""

            SELECT COUNT(*) AS pending

            FROM orders

            WHERE status='Pending'

        """)

        pending = cursor.fetchone()["pending"]

        conn.close()

        return jsonify({

            "success": True,

            "today_orders": total_orders,

            "today_revenue": revenue,

            "pending_orders": pending

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# TEST ROUTE
# ==========================================================

@delivery_bp.route("/delivery/test")
def delivery_test():

    return jsonify({

        "success": True,

        "message": "Delivery API Working"

    })
"""
==========================================================
                CafeSync POS
                delivery.py
                PART 2
        ORDER DETAILS • SEARCH • STATISTICS
==========================================================
"""

# ==========================================================
# GET SINGLE ORDER DETAILS
# ==========================================================

@delivery_bp.route("/delivery/order/<int:order_id>", methods=["GET"])
def get_delivery_order(order_id):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE id=?

        """,(order_id,))

        order = cursor.fetchone()

        if order is None:

            conn.close()

            return jsonify({

                "success":False,

                "message":"Order not found"

            }),404


        # --------------------------------------------------
        # ORDER ITEMS
        # --------------------------------------------------

        cursor.execute("""

            SELECT

                p.name,

                oi.quantity,

                oi.price

            FROM order_items oi

            JOIN products p

            ON oi.product_id=p.id

            WHERE oi.order_id=?

        """,(order_id,))

        items = cursor.fetchall()

        conn.close()

        return jsonify({

            "id":order["id"],

            "order_number":order["order_number"],

            "customer_name":order["customer_name"],

            "phone":order["phone"],

            "address":order["address"],

            "platform":order["platform"],

            "status":order["status"],

            "payment_status":order["payment_status"],

            "subtotal":order["subtotal"],

            "gst":order["gst"],

            "delivery_charge":order["delivery_charge"],

            "discount":order["discount"],

            "total":order["total"],

            "items":[

                {

                    "name":i["name"],

                    "quantity":i["quantity"],

                    "price":i["price"]

                }

                for i in items

            ]

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# SEARCH DELIVERY ORDERS
# ==========================================================

@delivery_bp.route("/delivery/search", methods=["GET"])
def search_delivery_orders():

    keyword = request.args.get("q","")

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM orders

            WHERE

                order_number LIKE ?

                OR customer_name LIKE ?
                OR phone LIKE ?
                OR address LIKE ?

            ORDER BY created_at DESC

        """,(

            f"%{keyword}%",

            f"%{keyword}%",

            f"%{keyword}%",

            f"%{keyword}%"

        ))

        rows = cursor.fetchall()

        conn.close()

        return jsonify([dict(r) for r in rows])

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# PLATFORM STATISTICS
# ==========================================================

@delivery_bp.route("/delivery/platform-summary", methods=["GET"])
def platform_summary():

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                platform,

                COUNT(*) total_orders,

                IFNULL(SUM(total),0) revenue

            FROM orders

            WHERE platform IN
            ('Swiggy','Zomato','Website','TakeAway')

            GROUP BY platform

        """)

        rows = cursor.fetchall()

        conn.close()

        return jsonify([

            {

                "platform":r["platform"],

                "orders":r["total_orders"],

                "revenue":r["revenue"]

            }

            for r in rows

        ])

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# TODAY DELIVERY STATISTICS
# ==========================================================

@delivery_bp.route("/delivery/today-summary", methods=["GET"])
def today_summary():

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) total,

                IFNULL(SUM(total),0) revenue

            FROM orders

            WHERE DATE(created_at)=DATE('now')

            AND platform IN
            ('Swiggy','Zomato','Website','TakeAway')

        """)

        summary = cursor.fetchone()

        cursor.execute("""

            SELECT COUNT(*) preparing

            FROM orders

            WHERE status='Preparing'

        """)

        preparing = cursor.fetchone()["preparing"]

        cursor.execute("""

            SELECT COUNT(*) ready_orders

            FROM orders

            WHERE status='Ready'

        """)

        ready = cursor.fetchone()["ready_orders"]

        cursor.execute("""

            SELECT COUNT(*) delivered

            FROM orders

            WHERE status='Delivered'

        """)

        delivered = cursor.fetchone()["delivered"]

        conn.close()

        return jsonify({

            "success":True,

            "orders":summary["total"],

            "revenue":summary["revenue"],

            "preparing":preparing,

            "ready":ready,

            "delivered":delivered

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500
"""
==========================================================
                CafeSync POS
                delivery.py
                PART 3
        UPDATE ORDER STATUS
==========================================================
"""

# ==========================================================
# UPDATE ORDER STATUS
# ==========================================================

@delivery_bp.route("/delivery/update-status/<int:order_id>", methods=["PUT"])
def update_order_status(order_id):

    try:

        data = request.get_json()

        new_status = data.get("status")

        valid_status = [

            "Pending",

            "Accepted",

            "Preparing",

            "Ready",

            "Out For Delivery",

            "Delivered",

            "Cancelled"

        ]

        if new_status not in valid_status:

            return jsonify({

                "success": False,

                "message": "Invalid Status"

            }),400

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status=?

            WHERE id=?

        """,(new_status,order_id))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Order status updated"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# ACCEPT ORDER
# ==========================================================

@delivery_bp.route("/delivery/accept/<int:order_id>", methods=["PUT"])
def accept_order(order_id):

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Accepted'

            WHERE id=?

        """,(order_id,))

        conn.commit()
        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Accepted"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# START PREPARING
# ==========================================================

@delivery_bp.route("/delivery/preparing/<int:order_id>", methods=["PUT"])
def preparing_order(order_id):

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Preparing'

            WHERE id=?

        """,(order_id,))

        conn.commit()
        conn.close()

        return jsonify({

            "success":True,

            "message":"Kitchen Started Preparing"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# READY FOR PICKUP
# ==========================================================

@delivery_bp.route("/delivery/ready/<int:order_id>", methods=["PUT"])
def ready_order(order_id):

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Ready'

            WHERE id=?

        """,(order_id,))

        conn.commit()
        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Ready"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# OUT FOR DELIVERY
# ==========================================================

@delivery_bp.route("/delivery/out-for-delivery/<int:order_id>", methods=["PUT"])
def out_for_delivery(order_id):

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Out For Delivery'

            WHERE id=?

        """,(order_id,))

        conn.commit()
        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Sent For Delivery"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# DELIVERED
# ==========================================================

@delivery_bp.route("/delivery/delivered/<int:order_id>", methods=["PUT"])
def delivered_order(order_id):

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Delivered'

            WHERE id=?

        """,(order_id,))

        conn.commit()
        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Delivered"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# CANCEL ORDER
# ==========================================================

@delivery_bp.route("/delivery/cancel/<int:order_id>", methods=["PUT"])
def cancel_order(order_id):

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET status='Cancelled'

            WHERE id=?

        """,(order_id,))

        conn.commit()
        conn.close()

        return jsonify({

            "success":True,

            "message":"Order Cancelled"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500
"""
==========================================================
                CafeSync POS
                delivery.py
                PART 4
        RIDER MANAGEMENT
==========================================================
"""

# ==========================================================
# GET ALL RIDERS
# ==========================================================

@delivery_bp.route("/delivery/riders", methods=["GET"])
def get_riders():

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM riders

            ORDER BY name

        """)

        rows = cursor.fetchall()

        conn.close()

        return jsonify([

            {

                "id":r["id"],

                "name":r["name"],

                "phone":r["phone"],

                "vehicle":r["vehicle"],

                "vehicle_number":r["vehicle_number"],

                "status":r["status"],

                "current_location":r["current_location"]

            }

            for r in rows

        ])

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# ADD RIDER
# ==========================================================

@delivery_bp.route("/delivery/riders", methods=["POST"])
def add_rider():

    try:

        data=request.get_json()

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            INSERT INTO riders(

                name,

                phone,

                vehicle,

                vehicle_number,

                status,

                current_location

            )

            VALUES(?,?,?,?,?,?)

        """,(

            data["name"],

            data["phone"],

            data["vehicle"],

            data["vehicle_number"],

            "Available",

            ""

        ))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Rider Added"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# ASSIGN RIDER
# ==========================================================

@delivery_bp.route("/delivery/assign-rider", methods=["POST"])
def assign_rider():

    try:

        data=request.get_json()

        order_id=data["order_id"]

        rider_id=data["rider_id"]

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE orders

            SET

                rider_id=?,

                status='Out For Delivery'

            WHERE id=?

        """,(rider_id,order_id))

        cursor.execute("""

            UPDATE riders

            SET status='Busy'

            WHERE id=?

        """,(rider_id,))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Rider Assigned"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# UPDATE RIDER LOCATION
# ==========================================================

@delivery_bp.route("/delivery/update-location/<int:rider_id>",methods=["PUT"])
def update_location(rider_id):

    try:

        data=request.get_json()

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            UPDATE riders

            SET current_location=?

            WHERE id=?

        """,(

            data["location"],

            rider_id

        ))

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Location Updated"

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# DELIVERY TRACKING
# ==========================================================

@delivery_bp.route("/delivery/tracking/<int:order_id>")
def tracking(order_id):

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            SELECT

                o.order_number,

                o.status,

                o.address,

                r.name rider_name,

                r.phone rider_phone,

                r.current_location

            FROM orders o

            LEFT JOIN riders r

            ON o.rider_id=r.id

            WHERE o.id=?

        """,(order_id,))

        tracking=cursor.fetchone()

        conn.close()

        if tracking is None:

            return jsonify({

                "success":False,

                "message":"Order not found"

            }),404

        return jsonify({

            "success":True,

            "order_number":tracking["order_number"],

            "status":tracking["status"],

            "address":tracking["address"],

            "rider":tracking["rider_name"],

            "phone":tracking["rider_phone"],

            "location":tracking["current_location"]

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# AVAILABLE RIDERS
# ==========================================================

@delivery_bp.route("/delivery/available-riders")
def available_riders():

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            SELECT *

            FROM riders

            WHERE status='Available'

        """)

        rows=cursor.fetchall()

        conn.close()

        return jsonify([dict(r) for r in rows])

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500
"""
==========================================================
                CafeSync POS
                delivery.py
                PART 5
        REPORTS • ANALYTICS • EXPORT
==========================================================
"""

from datetime import datetime
import csv
from io import StringIO
from flask import Response


# ==========================================================
# DELIVERY ANALYTICS
# ==========================================================

@delivery_bp.route("/delivery/analytics", methods=["GET"])
def delivery_analytics():

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) total_orders,

                SUM(total) revenue,

                AVG(total) average_bill

            FROM orders

            WHERE platform IN
            ('Swiggy','Zomato','Website','TakeAway')

        """)

        analytics = cursor.fetchone()

        cursor.execute("""

            SELECT

                platform,

                COUNT(*) total

            FROM orders

            GROUP BY platform

        """)

        platform_stats = cursor.fetchall()

        conn.close()

        return jsonify({

            "success":True,

            "total_orders":
                analytics["total_orders"] or 0,

            "revenue":
                analytics["revenue"] or 0,

            "average_bill":
                round(analytics["average_bill"] or 0,2),

            "platforms":[

                {

                    "platform":row["platform"],

                    "orders":row["total"]

                }

                for row in platform_stats

            ]

        })

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# MONTHLY REPORT
# ==========================================================

@delivery_bp.route("/delivery/monthly-report")
def monthly_report():

    try:

        conn=get_connection()
        cursor=conn.cursor()

        cursor.execute("""

            SELECT

                strftime('%Y-%m',created_at) month,

                COUNT(*) orders,

                SUM(total) revenue

            FROM orders

            GROUP BY month

            ORDER BY month DESC

        """)

        rows=cursor.fetchall()

        conn.close()

        return jsonify([

            {

                "month":r["month"],

                "orders":r["orders"],

                "revenue":r["revenue"]

            }

            for r in rows

        ])

    except Exception as e:

        return jsonify({

            "success":False,

            "message":str(e)

        }),500


# ==========================================================
# TODAY'S DELIVERIES
# ==========================================================

@delivery_bp.route("/delivery/today")
def today_deliveries():

    today=datetime.now().strftime("%Y-%m-%d")

    conn=get_connection()

    cursor=conn.cursor()

    cursor.execute("""

        SELECT *

        FROM orders

        WHERE DATE(created_at)=?

    """,(today,))

    rows=cursor.fetchall()

    conn.close()

    return jsonify([dict(r) for r in rows])


# ==========================================================
# EXPORT CSV
# ==========================================================

@delivery_bp.route("/delivery/export")
def export_delivery_report():

    conn=get_connection()

    cursor=conn.cursor()

    cursor.execute("""

        SELECT

            order_number,

            customer_name,

            platform,

            total,

            payment_status,

            status,

            created_at

        FROM orders

        ORDER BY created_at DESC

    """)

    rows=cursor.fetchall()

    conn.close()

    output=StringIO()

    writer=csv.writer(output)

    writer.writerow([

        "Order No",

        "Customer",

        "Platform",

        "Amount",

        "Payment",

        "Status",

        "Date"

    ])

    for row in rows:

        writer.writerow([

            row["order_number"],

            row["customer_name"],

            row["platform"],

            row["total"],

            row["payment_status"],

            row["status"],

            row["created_at"]

        ])

    output.seek(0)

    return Response(

        output,

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=delivery_report.csv"

        }

    )


# ==========================================================
# DELIVERY NOTIFICATIONS
# ==========================================================

@delivery_bp.route("/delivery/notifications")
def delivery_notifications():

    conn=get_connection()

    cursor=conn.cursor()

    cursor.execute("""

        SELECT

            order_number,

            status,

            created_at

        FROM orders

        ORDER BY created_at DESC

        LIMIT 10

    """)

    rows=cursor.fetchall()

    conn.close()

    return jsonify([

        {

            "title":

            f"Order {r['order_number']}",

            "message":

            f"Status : {r['status']}",

            "time":

            r["created_at"]

        }

        for r in rows

    ])


# ==========================================================
# PLATFORM REVENUE
# ==========================================================

@delivery_bp.route("/delivery/platform-revenue")
def platform_revenue():

    conn=get_connection()

    cursor=conn.cursor()

    cursor.execute("""

        SELECT

            platform,

            SUM(total) revenue

        FROM orders

        GROUP BY platform

    """)

    rows=cursor.fetchall()

    conn.close()

    return jsonify([

        {

            "platform":r["platform"],

            "revenue":r["revenue"]

        }

        for r in rows

    ])


# ==========================================================
# DELIVERY HEALTH CHECK
# ==========================================================

@delivery_bp.route("/delivery/health")
def delivery_health():

    return jsonify({

        "success":True,

        "service":"CafeSync Delivery",

        "status":"Running",

        "version":"1.0"

    })