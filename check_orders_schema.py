"""Check paper_orders schema"""
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
    WHERE table_name = 'paper_orders'
    ORDER BY ordinal_position
""")

print("\npaper_orders table columns:")
print("-" * 50)
for col, dtype in cursor.fetchall():
    print(f"  {col:25s} {dtype}")

conn.close()
