import sqlite3
import os

db_path = 'ingles_pro.db'
if not os.path.exists(db_path):
    print(f'DB not found at {db_path}')
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("UPDATE users SET is_admin=1 WHERE username='mutley'")
conn.commit()
updated = cursor.rowcount
conn.close()

print(f'DONE. Rows updated: {updated}')
