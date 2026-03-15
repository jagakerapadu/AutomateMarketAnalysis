"""
Execute add_performance_indexes.sql via Python
Adds 8 critical indexes with zero downtime (CONCURRENTLY)
"""

import psycopg2
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import get_settings

def execute_indexes():
    """Execute index creation statements"""
    settings = get_settings()
    
    print("\n" + "="*80)
    print("ADDING PERFORMANCE INDEXES TO DATABASE")
    print("="*80)
    print(f"Database: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}")
    print("Creating indexes with CONCURRENTLY (zero downtime)...")
    print("="*80 + "\n")
    
    # Define all CREATE INDEX statements
    index_statements = [
        # paper_orders indexes (MOST CRITICAL)
        {
            'name': 'idx_paper_orders_symbol_time',
            'table': 'paper_orders',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_symbol_time 
                ON paper_orders (symbol, placed_at DESC)
            """
        },
        {
            'name': 'idx_paper_orders_status_time',
            'table': 'paper_orders',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_status_time 
                ON paper_orders (status, placed_at DESC)
            """
        },
        {
            'name': 'idx_paper_orders_signal_id',
            'table': 'paper_orders',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_signal_id 
                ON paper_orders (signal_id) 
                WHERE signal_id IS NOT NULL
            """
        },
        {
            'name': 'idx_paper_orders_type_symbol_time',
            'table': 'paper_orders',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_type_symbol_time 
                ON paper_orders (order_type, symbol, placed_at DESC)
            """
        },
        # paper_positions indexes
        {
            'name': 'idx_paper_positions_updated',
            'table': 'paper_positions',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_positions_updated 
                ON paper_positions (updated_at DESC)
            """
        },
        {
            'name': 'idx_paper_positions_pnl',
            'table': 'paper_positions',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_positions_pnl 
                ON paper_positions (pnl DESC NULLS LAST)
            """
        },
        # signals indexes
        {
            'name': 'idx_signals_strategy_status',
            'table': 'signals',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signals_strategy_status 
                ON signals (strategy, status, created_at DESC)
            """
        },
        {
            'name': 'idx_signals_active',
            'table': 'signals',
            'sql': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signals_active 
                ON signals (symbol, created_at DESC) 
                WHERE status IN ('PENDING', 'EXECUTED')
            """
        }
    ]
    
    # Connect to database
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    # Must use autocommit for CREATE INDEX CONCURRENTLY
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, idx_def in enumerate(index_statements, 1):
        try:
            start_time = time.time()
            print(f"[{i}/{len(index_statements)}] Creating {idx_def['name']} on {idx_def['table']}...", end=" ", flush=True)
            
            cur.execute(idx_def['sql'])
            
            elapsed = time.time() - start_time
            print(f"✅ {elapsed:.2f}s")
            success_count += 1
            
        except psycopg2.errors.DuplicateTable as e:
            print(f"⏭️ Already exists")
            skip_count += 1
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:80]}")
            error_count += 1
    
    # Get index sizes
    print("\n" + "-"*80)
    print("INDEX SIZES:")
    print("-"*80)
    
    cur.execute("""
        SELECT 
            t.relname as tablename,
            i.relname as indexname,
            pg_size_pretty(pg_relation_size(i.oid)) as size
        FROM pg_class i
        JOIN pg_index ix ON i.oid = ix.indexrelid
        JOIN pg_class t ON t.oid = ix.indrelid
        WHERE i.relname LIKE 'idx_paper_%' OR i.relname LIKE 'idx_signals_%'
        ORDER BY t.relname, i.relname
    """)
    
    indexes = cur.fetchall()
    current_table = None
    for table, index, size in indexes:
        if table != current_table:
            if current_table:
                print()
            print(f"\n{table}:")
            current_table = table
        print(f"  {index}: {size}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"✅ Successfully created: {success_count} indexes")
    print(f"⏭️ Skipped (exists):     {skip_count} indexes")
    print(f"❌ Errors:              {error_count} indexes")
    print(f"📊 Total processed:     {len(index_statements)} indexes")
    
    if error_count == 0:
        print("\n🎉 All indexes added successfully!")
        print("✅ Database ready for high-performance trading!")
        print("\nNext steps:")
        print("  1. Run: py scripts\\test_query_performance.py")
        print("  2. Compare performance before/after")
        print("  3. Monitor in production")
    else:
        print(f"\n⚠️ Some indexes failed. Check errors above.")
    
    print("="*80 + "\n")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    execute_indexes()
