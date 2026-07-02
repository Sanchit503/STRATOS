import db

conn = db.get_db()
cursor = conn.cursor(dictionary=True)

with open('app_queries_15.sql', 'r') as f:
    sql_script = f.read()

# Split the script into individual queries
queries = sql_script.split(';')

print("\n" + "="*80)
print("EXECUTING 15 RELATIONAL ALGEBRA QUERIES ON STRATOS_DB")
print("="*80 + "\n")

success = 0
for i, q in enumerate(queries):
    q = q.strip()
    if q:
        try:
            print(f"--- QUERY {success + 1} ---")
            
            # Extract the conceptual comment for the query if it exists
            comment = ""
            lines = [l.strip() for l in q.split('\n') if l.strip()]
            for l in lines:
                if l.startswith('--'):
                    comment += l + "\n"
                
            if comment:
                print(comment.strip())
            
            # Print a succinct version of the query itself
            sql_clean = "\n".join([l for l in lines if not l.startswith('--')])
            print(f"SQL: {sql_clean[:100]}...\n")
            
            cursor.execute(q)
            results = cursor.fetchall()
            success += 1
            
            # Print results safely
            if not results:
                print(">> [Result: 0 rows returned]")
            else:
                print(f">> [Result: {len(results)} rows returned]")
                for idx, row in enumerate(results[:3]):  # Limit print to 3 rows
                    print(f"Row {idx+1}: {row}")
                if len(results) > 3:
                     print(f"... and {len(results)-3} more rows")
            
            print("\n" + "-"*80 + "\n")
        except Exception as e:
            print(f"Error executing query: {q[:100]} \nException: {e}\n")

print(f"\nSUCCESSFULLY EXECUTED {success} QUERIES OUT OF 15.")

cursor.close()
conn.close()
