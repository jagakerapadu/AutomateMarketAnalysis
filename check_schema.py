"""Quick check of paper_positions schema"""
import psycopg2
from config.settings import get_settings

settings = get_settings()
conn = psycopg2.connect(
    host=settings.DB_HOST, port=settings.DB_PORT, 
    database=settings.DB_NAME, user=settings.DB_USER, password=settings.DB_PASSWORD
)
cursor = conn.cursor()

cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'paper_positions'
    ORDER BY ordinal_position
""")

print("\npaper_positions table columns:")
print("-" * 50)
for col, dtype in cursor.fetchall():
    print(f"  {col:20s} {dtype}")

cursor.execute("SELECT * FROM paper_positions LIMIT 1")
print("\nSample row:")
if cursor.description:
    colnames = [desc[0] for desc in cursor.description]
    print(f"  {', '.join(colnames)}")

conn.close()
