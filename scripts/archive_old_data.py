"""
Archive old orders and signals to keep main tables fast
Run this monthly to move data older than 6 months to archive tables
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from datetime import datetime, timedelta
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("archival")

def create_archive_tables():
    """Create archive tables if they don't exist"""
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # Create archive table for orders (same structure as paper_orders)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_orders_archive (
            LIKE paper_orders INCLUDING ALL
        )
    """)
    
    # Create archive table for signals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals_archive (
            LIKE signals INCLUDING ALL
        )
    """)
    
    # Add indexes to archive tables
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_archive_orders_placed 
            ON paper_orders_archive (placed_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_archive_orders_symbol 
            ON paper_orders_archive (symbol, placed_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_archive_signals_created 
            ON signals_archive (created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_archive_signals_symbol 
            ON signals_archive (symbol, created_at DESC)
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info("Archive tables verified/created")


def archive_old_orders(days_to_keep: int = 180):
    """
    Archive orders older than specified days
    
    Args:
        days_to_keep: Keep orders from last X days in main table (default: 180 = 6 months)
    """
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    print("\n" + "="*80)
    print("ARCHIVING OLD ORDERS")
    print("="*80)
    print(f"Cutoff Date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Keeping: Orders from last {days_to_keep} days")
    print(f"Archiving: Orders before {cutoff_date.strftime('%Y-%m-%d')}")
    print("="*80 + "\n")
    
    try:
        # Count orders to archive
        cursor.execute("""
            SELECT COUNT(*) FROM paper_orders WHERE placed_at < %s
        """, (cutoff_date,))
        
        count_to_archive = cursor.fetchone()[0]
        
        if count_to_archive == 0:
            print("✓ No orders to archive (all orders are recent)")
            return
        
        print(f"Found {count_to_archive} orders to archive")
        
        # Move to archive (INSERT then DELETE for safety)
        cursor.execute("""
            INSERT INTO paper_orders_archive
            SELECT * FROM paper_orders
            WHERE placed_at < %s
            ON CONFLICT (order_id) DO NOTHING
        """, (cutoff_date,))
        
        archived_count = cursor.rowcount
        print(f"  ✓ Copied {archived_count} orders to paper_orders_archive")
        
        # Delete from main table
        cursor.execute("""
            DELETE FROM paper_orders
            WHERE placed_at < %s
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        print(f"  ✓ Deleted {deleted_count} orders from paper_orders")
        
        # Verify counts match
        if archived_count != deleted_count:
            print(f"  ⚠️  WARNING: Archived {archived_count} but deleted {deleted_count}")
            conn.rollback()
            raise Exception("Archive count mismatch - rolled back")
        
        conn.commit()
        
        # Show remaining counts
        cursor.execute("SELECT COUNT(*) FROM paper_orders")
        remaining = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paper_orders_archive")
        total_archived = cursor.fetchone()[0]
        
        print("\n" + "-"*80)
        print(f"Main table (paper_orders):        {remaining:>6} orders (last {days_to_keep} days)")
        print(f"Archive table:                    {total_archived:>6} orders (historical)")
        print(f"Total:                            {remaining + total_archived:>6} orders")
        print("-"*80)
        
        logger.info(f"Archived {archived_count} orders successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Archive failed: {e}")
        print(f"\n❌ ERROR: {e}")
        raise
    
    finally:
        cursor.close()
        conn.close()


def archive_old_signals(days_to_keep: int = 180):
    """
    Archive signals older than specified days
    
    Args:
        days_to_keep: Keep signals from last X days in main table (default: 180 = 6 months)
    """
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    print("\n" + "="*80)
    print("ARCHIVING OLD SIGNALS")
    print("="*80)
    print(f"Cutoff Date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    try:
        # Only archive CLOSED signals (keep PENDING/ACTIVE)
        cursor.execute("""
            SELECT COUNT(*) FROM signals 
            WHERE created_at < %s AND status = 'CLOSED'
        """, (cutoff_date,))
        
        count_to_archive = cursor.fetchone()[0]
        
        if count_to_archive == 0:
            print("✓ No signals to archive (all signals are recent or active)")
            return
        
        print(f"Found {count_to_archive} CLOSED signals to archive")
        
        # Move to archive
        cursor.execute("""
            INSERT INTO signals_archive
            SELECT * FROM signals
            WHERE created_at < %s AND status = 'CLOSED'
            ON CONFLICT (id) DO NOTHING
        """, (cutoff_date,))
        
        archived_count = cursor.rowcount
        print(f"  ✓ Copied {archived_count} signals to signals_archive")
        
        # Delete from main table
        cursor.execute("""
            DELETE FROM signals
            WHERE created_at < %s AND status = 'CLOSED'
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        print(f"  ✓ Deleted {deleted_count} signals from signals table")
        
        conn.commit()
        
        # Show remaining counts
        cursor.execute("SELECT COUNT(*), status FROM signals GROUP BY status")
        print("\nMain table (signals):")
        for row in cursor.fetchall():
            print(f"  {row[1]:10} {row[0]:>6} signals")
        
        cursor.execute("SELECT COUNT(*) FROM signals_archive")
        total_archived = cursor.fetchone()[0]
        print(f"\nArchive table:   {total_archived:>6} signals (historical)")
        
        logger.info(f"Archived {archived_count} signals successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Signal archive failed: {e}")
        print(f"\n❌ ERROR: {e}")
        raise
    
    finally:
        cursor.close()
        conn.close()


def cleanup_stale_positions():
    """Remove positions with quantity = 0 older than 7 days"""
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("CLEANING UP STALE POSITIONS")
    print("="*80)
    
    cutoff_date = datetime.now() - timedelta(days=7)
    
    cursor.execute("""
        DELETE FROM paper_positions
        WHERE quantity = 0 
          AND updated_at < %s
    """, (cutoff_date,))
    
    deleted = cursor.rowcount
    conn.commit()
    
    if deleted > 0:
        print(f"  ✓ Deleted {deleted} closed positions (quantity=0, older than 7 days)")
        logger.info(f"Cleaned up {deleted} stale positions")
    else:
        print("  ✓ No stale positions found")
    
    cursor.close()
    conn.close()


def show_archive_summary():
    """Show summary of archived vs active data"""
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("ARCHIVE SUMMARY")
    print("="*80)
    
    # Get table sizes
    cursor.execute("""
        SELECT 
            'paper_orders' AS table_name,
            COUNT(*) AS row_count,
            pg_size_pretty(pg_total_relation_size('paper_orders')) AS table_size
        FROM paper_orders
        UNION ALL
        SELECT 
            'paper_orders_archive',
            COUNT(*),
            pg_size_pretty(pg_total_relation_size('paper_orders_archive'))
        FROM paper_orders_archive
        UNION ALL
        SELECT 
            'signals',
            COUNT(*),
            pg_size_pretty(pg_total_relation_size('signals'))
        FROM signals
        UNION ALL
        SELECT 
            'signals_archive',
            COUNT(*),
            pg_size_pretty(pg_total_relation_size('signals_archive'))
        FROM signals_archive
    """)
    
    print(f"\n{'Table':<30} {'Rows':>10} {'Size':>12}")
    print("-"*80)
    for row in cursor.fetchall():
        print(f"{row[0]:<30} {row[1]:>10,} {row[2]:>12}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MONTHLY DATABASE ARCHIVAL SCRIPT")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # Step 1: Create archive tables if needed
        print("\n[1/4] Creating archive tables...")
        create_archive_tables()
        print("  ✓ Archive tables ready")
        
        # Step 2: Archive old orders (6 months)
        print("\n[2/4] Archiving old orders...")
        archive_old_orders(days_to_keep=180)
        
        # Step 3: Archive old signals (6 months, only CLOSED)
        print("\n[3/4] Archiving old signals...")
        archive_old_signals(days_to_keep=180)
        
        # Step 4: Cleanup stale positions
        print("\n[4/4] Cleaning up stale positions...")
        cleanup_stale_positions()
        
        # Show summary
        show_archive_summary()
        
        print("\n" + "="*80)
        print("✅ ARCHIVAL COMPLETE!")
        print("="*80)
        print("\nRecommendations:")
        print("  • Run this script on 1st of every month")
        print("  • Monitor table sizes: py analyze_database_schema.py")
        print("  • Keep archive tables backed up separately")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ARCHIVAL FAILED: {e}")
        logger.error(f"Archival failed: {e}")
        sys.exit(1)
