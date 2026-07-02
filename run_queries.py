import db

conn = db.get_db()
cursor = conn.cursor()

with open('app_queries_15.sql', 'r') as f:
    sql_script = f.read()

# Split the script into individual queries
queries = sql_script.split(';')

success = 0
for q in queries:
    q = q.strip()
    if q:
        try:
            cursor.execute(q)
            # Just flush the output
            cursor.fetchall()
            success += 1
        except Exception as e:
            print(f"Error executing query: {q[:50]}... \n{e}")

print(f"Successfully executed {success} queries out of {len([q for q in queries if q.strip()])}.")

cursor.close()
conn.close()
