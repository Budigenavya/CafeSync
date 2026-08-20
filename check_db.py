import sqlite3
import os
from config import DATABASE

print("Database path:", DATABASE)
print("Absolute path:", os.path.abspath(DATABASE))
print("File exists:", os.path.exists(DATABASE))

try:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
    """)

    tables = cursor.fetchall()

    print("Tables:", tables)

    conn.close()

except Exception as e:
    print("Error:", e)