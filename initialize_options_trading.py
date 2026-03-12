"""
Initialize Options Paper Trading System
Run this once to set up options trading tables
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
from config.settings import get_settings

settings = get_settings()

def initialize_options_tables():
    """Create all options trading tables"""
    print("=" * 70)
    print("INITIALIZING OPTIONS PAPER TRADING SYSTEM")
    print("=" * 70)
    
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # Read and execute SQL file
    sql_file = Path(__file__).parent / "scripts" / "sql" / "options_paper_trading.sql"
    
    print(f"\n📄 Reading SQL file: {sql_file}")
    
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    print("⚙️  Executing SQL commands...")
    
    try:
        cursor.execute(sql)
        conn.commit()
        print("✅ All tables created successfully!")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_name LIKE 'paper_options%' OR table_name LIKE 'options_%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        # Check initial capital
        cursor.execute("SELECT total_capital, available_cash FROM paper_options_portfolio LIMIT 1")
        portfolio = cursor.fetchone()
        
        if portfolio:
            print(f"\n💰 Portfolio initialized:")
            print(f"  Total Capital: ₹{portfolio[0]:,.2f}")
            print(f"  Available Cash: ₹{portfolio[1]:,.2f}")
        
        print("\n✅ Options paper trading system ready!")
        print("\nNext steps:")
        print("1. Run: py generate_options_signals.py   (to generate signals)")
        print("2. Run: py start_options_trading.py       (to start trading)")
        print("3. Run: py options_eod_report.py          (for end-of-day analytics)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    initialize_options_tables()
