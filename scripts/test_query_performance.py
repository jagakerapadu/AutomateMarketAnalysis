"""
Test database query performance
Run before and after adding indexes to measure improvement
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
import time
from config.settings import get_settings

def test_query_performance():
    """Test common queries and measure execution time"""
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # Test queries (common patterns used by application)
    test_queries = [
        ("Get all positions", 
         "SELECT * FROM paper_positions ORDER BY symbol"),
        
        ("Get orders by symbol", 
         "SELECT * FROM paper_orders WHERE symbol = 'INFY' ORDER BY placed_at DESC"),
        
        ("Get recent orders", 
         "SELECT * FROM paper_orders ORDER BY placed_at DESC LIMIT 50"),
        
        ("Get PENDING signals", 
         "SELECT * FROM signals WHERE status = 'PENDING' ORDER BY created_at DESC"),
        
        ("Get order history with status", 
         "SELECT * FROM paper_orders WHERE status = 'COMPLETED' ORDER BY placed_at DESC LIMIT 20"),
        
        ("Get positions updated recently", 
         "SELECT * FROM paper_positions WHERE updated_at > NOW() - INTERVAL '1 hour'"),
        
        ("Get orders for specific signal", 
         "SELECT * FROM paper_orders WHERE signal_id IS NOT NULL ORDER BY placed_at DESC"),
        
        ("Get BUY orders for symbol", 
         "SELECT * FROM paper_orders WHERE order_type = 'BUY' AND symbol = 'RELIANCE' ORDER BY placed_at DESC"),
        
        ("Get signals by strategy", 
         "SELECT * FROM signals WHERE strategy = 'MOMENTUM_BREAKOUT' ORDER BY created_at DESC"),
        
        ("Get portfolio summary", 
         "SELECT * FROM paper_portfolio WHERE id = 1"),
    ]
    
    print("\n" + "="*100)
    print("QUERY PERFORMANCE TEST")
    print("="*100)
    print(f"{'Query':<45} | {'Avg Time':>10} | {'Min':>8} | {'Max':>8} | {'Rows':>6} | {'Status':>10}")
    print("-"*100)
    
    results = []
    
    for query_name, query in test_queries:
        # Run each query 5 times to get reliable average
        times = []
        row_count = 0
        
        for i in range(5):
            start = time.perf_counter()
            cursor.execute(query)
            rows = cursor.fetchall()
            duration = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(duration)
            row_count = len(rows)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Determine status
        if avg_time < 10:
            status = "✅ FAST"
        elif avg_time < 50:
            status = "⚠️ OK"
        else:
            status = "🔴 SLOW"
        
        results.append((query_name, avg_time, min_time, max_time, row_count, status))
        print(f"{query_name:<45} | {avg_time:>8.2f}ms | {min_time:>6.2f}ms | {max_time:>6.2f}ms | {row_count:>6} | {status:>10}")
    
    print("-"*100)
    
    # Summary statistics
    total_queries = len(results)
    fast_queries = len([r for r in results if r[5] == "✅ FAST"])
    ok_queries = len([r for r in results if r[5] == "⚠️ OK"])
    slow_queries = len([r for r in results if r[5] == "🔴 SLOW"])
    avg_all = sum(r[1] for r in results) / len(results)
    
    print(f"\nSUMMARY:")
    print(f"  Total queries tested: {total_queries}")
    print(f"  Fast (<10ms):         {fast_queries} ({fast_queries/total_queries*100:.0f}%)")
    print(f"  OK (10-50ms):         {ok_queries} ({ok_queries/total_queries*100:.0f}%)")
    print(f"  Slow (>50ms):         {slow_queries} ({slow_queries/total_queries*100:.0f}%)")
    print(f"  Average time:         {avg_all:.2f}ms")
    
    if slow_queries > 0:
        print(f"\n⚠️  {slow_queries} slow queries detected - consider adding indexes")
    else:
        print("\n✅ All queries performing well!")
    
    # Show EXPLAIN for slowest query
    if results:
        slowest = max(results, key=lambda x: x[1])
        slowest_query = [q for name, q in test_queries if name == slowest[0]][0]
        
        print("\n" + "="*100)
        print(f"EXPLAIN ANALYZE for slowest query: {slowest[0]} ({slowest[1]:.2f}ms)")
        print("="*100)
        
        cursor.execute(f"EXPLAIN ANALYZE {slowest_query}")
        for line in cursor.fetchall():
            print(f"  {line[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*100)
    print("PERFORMANCE TEST COMPLETE")
    print("="*100 + "\n")


def check_index_usage():
    """Check which indexes are actually being used"""
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    print("\n" + "="*100)
    print("INDEX USAGE STATISTICS")
    print("="*100)
    print(f"{'Table':<30} | {'Index':<45} | {'Scans':>10} | {'Rows Read':>12}")
    print("-"*100)
    
    cursor.execute("""
        SELECT
            tablename,
            indexname,
            idx_scan,
            idx_tup_read
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
          AND tablename LIKE 'paper_%' OR tablename = 'signals'
        ORDER BY tablename, idx_scan DESC
    """)
    
    for row in cursor.fetchall():
        usage = "⚠️ UNUSED" if row[2] == 0 else ""
        print(f"{row[0]:<30} | {row[1]:<45} | {row[2]:>10,} | {row[3]:>12,} {usage}")
    
    # Find unused indexes
    cursor.execute("""
        SELECT
            tablename,
            indexname
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
          AND idx_scan = 0
          AND indexname NOT LIKE '%_pkey'  -- Exclude primary keys
          AND (tablename LIKE 'paper_%' OR tablename = 'signals')
    """)
    
    unused = cursor.fetchall()
    
    if unused:
        print(f"\n⚠️  {len(unused)} unused indexes found:")
        for row in unused:
            print(f"  - {row[0]}.{row[1]}")
        print("\nNote: Run this test after 1 week of production use to identify truly unused indexes")
    else:
        print("\n✅ All indexes are being used!")
    
    cursor.close()
    conn.close()
    
    print("="*100 + "\n")


def check_table_bloat():
    """Check for table bloat (dead tuples) that need VACUUM"""
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    print("\n" + "="*100)
    print("TABLE BLOAT CHECK")
    print("="*100)
    print(f"{'Table':<30} | {'Size':>12} | {'Live':>8} | {'Dead':>8} | {'Dead %':>8} | {'Action':>15}")
    print("-"*100)
    
    cursor.execute("""
        SELECT
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            n_live_tup,
            n_dead_tup,
            ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
          AND (tablename LIKE 'paper_%' OR tablename = 'signals')
        ORDER BY n_dead_tup DESC
    """)
    
    needs_vacuum = []
    
    for row in cursor.fetchall():
        dead_pct = row[4] or 0
        
        if dead_pct > 20:
            action = "🔴 VACUUM NOW"
            needs_vacuum.append(row[0])
        elif dead_pct > 10:
            action = "⚠️ VACUUM SOON"
        else:
            action = "✅ Good"
        
        print(f"{row[0]:<30} | {row[1]:>12} | {row[2]:>8,} | {row[3]:>8,} | {dead_pct:>7.1f}% | {action:>15}")
    
    if needs_vacuum:
        print(f"\n⚠️  {len(needs_vacuum)} tables need VACUUM:")
        for table in needs_vacuum:
            print(f"  VACUUM ANALYZE {table};")
    else:
        print("\n✅ All tables healthy (no bloat)")
    
    cursor.close()
    conn.close()
    
    print("="*100 + "\n")


if __name__ == "__main__":
    print("\n" + "#"*100)
    print("#" + " "*98 + "#")
    print("#" + " "*30 + "DATABASE PERFORMANCE TEST" + " "*44 + "#")
    print("#" + " "*98 + "#")
    print("#"*100)
    
    # Run all checks
    test_query_performance()
    check_index_usage()
    check_table_bloat()
    
    print("\n" + "="*100)
    print("RECOMMENDED ACTIONS:")
    print("="*100)
    print("""
1. If queries show >50ms: Add indexes (scripts/sql/add_performance_indexes.sql)
2. If table bloat >20%: Run VACUUM ANALYZE
3. If >500 orders: Consider archival (scripts/archive_old_data.py)
4. Run this test weekly to monitor performance trends
    """)
    print("="*100 + "\n")
