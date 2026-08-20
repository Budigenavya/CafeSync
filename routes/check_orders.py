import sqlite3
import os

DB = r"C:\Users\navyabudige\OneDrive\Desktop\CafeSync\backend\database.db"

print("Database being checked:")
print(DB)

print("\nDatabase exists:", os.path.exists(DB))

conn = sqlite3.connect(DB)
cursor = conn.cursor()

# Show all tables
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
""")

tables = cursor.fetchall()

print("\n========== ALL TABLES ==========")

for table in tables:
    print(table[0])

# Check orders
cursor.execute("PRAGMA table_info(orders)")
columns = cursor.fetchall()

print("\n========== ORDERS TABLE ==========")

if not columns:
    print("❌ ORDERS TABLE NOT FOUND")
else:
    for column in columns:
        print(column)

# Check order_items
cursor.execute("PRAGMA table_info(order_items)")
columns = cursor.fetchall()

print("\n========== ORDER ITEMS TABLE ==========")

if not columns:
    print("❌ ORDER_ITEMS TABLE NOT FOUND")
else:
    for column in columns:
        print(column)

conn.close()