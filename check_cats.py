import db

conn = db.get_db()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT DISTINCT category, role FROM Vehicle_Type;")
rows = cursor.fetchall()

print("--- CATEGORIES & ROLES ---")
for r in rows:
    print(f"Category: '{r['category']}'  |  Role: '{r['role']}'")

cursor.close()
conn.close()
