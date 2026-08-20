import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT DEFAULT 'Walk-in Customer'")
except:
    pass

try:
    cur.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT DEFAULT ''")
except:
    pass

try:
    cur.execute("ALTER TABLE orders ADD COLUMN subtotal REAL DEFAULT 0")
except:
    pass

conn.commit()
conn.close()

print("Orders table updated successfully.")