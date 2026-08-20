import sqlite3

conn = sqlite3.connect("database.db")
conn.row_factory = sqlite3.Row

orders = conn.execute("""
    SELECT *
    FROM orders
    ORDER BY id DESC
""").fetchall()

print("\n========== ORDERS ==========")

for order in orders:
    print(dict(order))

print("\n========== ORDER ITEMS ==========")

items = conn.execute("""
    SELECT *
    FROM order_items
    ORDER BY id DESC
""").fetchall()

for item in items:
    print(dict(item))

conn.close()