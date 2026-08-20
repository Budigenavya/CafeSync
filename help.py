import sqlite3

db_path = r"C:\Users\navyabudige\OneDrive\Desktop\CafeSync\backend\database.db"

print("Using DB:", db_path)

conn = sqlite3.connect(db_path)

cursor = conn.cursor()

cursor.execute("""
SELECT name FROM sqlite_master 
WHERE type='table'
""")

print("\nTables:")

tables = cursor.fetchall()

for table in tables:
    print(table[0])


print("\nOrders table columns:")

cursor.execute("PRAGMA table_info(orders)")

columns = cursor.fetchall()

if not columns:
    print("orders table does not exist")
else:
    for col in columns:
        print(col)

conn.close()