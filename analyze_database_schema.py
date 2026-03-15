"""Analyze database schema and table statistics"""
import psycopg2
from config.settings import get_settings

settings = get_settings()

def analyze_database():
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # Get all tables
    print("\n" + "="*80)
    print("DATABASE TABLES")
    print("="*80)
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    for i, table in enumerate(tables, 1):
        print(f"{i:2}. {table}")
    
    # Get row counts for each table
    print("\n" + "="*80)
    print("TABLE ROW COUNTS")
    print("="*80)
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:40} {count:>10,} rows")
        except:
            print(f"{table:40} {'ERROR':>10}")
    
    # Get table sizes
    print("\n" + "="*80)
    print("TABLE SIZES")
    print("="*80)
    cursor.execute("""
        SELECT 
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            pg_total_relation_size(schemaname||'.'||tablename) AS bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)
    for row in cursor.fetchall():
        print(f"{row[0]:40} {row[1]:>12}")
    
    # Get indexes
    print("\n" + "="*80)
    print("TABLE INDEXES")
    print("="*80)
    cursor.execute("""
        SELECT 
            t.tablename,
            i.indexname,
            i.indexdef
        FROM pg_indexes i
        JOIN pg_tables t ON i.tablename = t.tablename
        WHERE t.schemaname = 'public'
        ORDER BY t.tablename, i.indexname
    """)
    
    current_table = None
    for row in cursor.fetchall():
        if current_table != row[0]:
            current_table = row[0]
            print(f"\n{current_table}:")
        print(f"  - {row[1]}")
    
    # Get foreign keys
    print("\n" + "="*80)
    print("FOREIGN KEY CONSTRAINTS")
    print("="*80)
    cursor.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name
    """)
    
    fks = cursor.fetchall()
    if fks:
        for row in fks:
            print(f"{row[0]}.{row[1]} → {row[2]}.{row[3]}")
    else:
        print("⚠️  NO FOREIGN KEY CONSTRAINTS FOUND")
    
    # Check for missing indexes on frequently queried columns
    print("\n" + "="*80)
    print("COLUMNS WITHOUT INDEXES (Potential Performance Issues)")
    print("="*80)
    
    # Check paper_orders
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'paper_orders' 
          AND column_name IN ('symbol', 'status', 'placed_at', 'signal_id')
    """)
    paper_order_cols = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.statistics 
        WHERE table_name = 'paper_orders'
    """)
    indexed_cols = [row[0] for row in cursor.fetchall()]
    
    missing_indexes = set(paper_order_cols) - set(indexed_cols)
    if missing_indexes:
        print(f"paper_orders: {', '.join(missing_indexes)}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_database()
