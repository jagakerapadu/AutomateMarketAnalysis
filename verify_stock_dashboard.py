"""
Verify Stock Trading Dashboard Values
Checks both API endpoints and database to ensure consistency
"""
import requests
from datetime import datetime

print("=" * 80)
print("STOCK TRADING DASHBOARD VERIFICATION")
print("=" * 80)

# 1. Check the Paper Trading API (used by Stock Trading dashboard)
print("\n1. PAPER TRADING API (/api/paper-trading/portfolio)")
print("-" * 80)
try:
    response = requests.get('http://localhost:8000/api/paper-trading/portfolio')
    data = response.json()
    
    print(f'✓ Total Capital:     ₹{data["total_capital"]:,.0f}')
    print(f'✓ Available Cash:    ₹{data["available_cash"]:,.0f}')
    print(f'✓ Invested Amount:   ₹{data["invested_amount"]:,.0f}')
    print(f'✓ Total P&L:         ₹{data["total_pnl"]:,.0f}')
    print(f'✓ Today P&L:         ₹{data["today_pnl"]:,.0f}')
    print(f'✓ Positions Count:   {data["positions_count"]}')
    
    # Format the timestamp
    updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
    day = updated_at.day
    month = updated_at.strftime('%b')
    time_str = updated_at.strftime('%I:%M %p').lstrip('0').lower()
    print(f'✓ Last Updated:      {day} {month}, {time_str}')
    
    # Store for comparison
    api_pnl = data["total_pnl"]
    api_updated = data["updated_at"]
    
except requests.exceptions.ConnectionError:
    print("❌ API Server not running! Please start with: py start_api.py")
    api_pnl = None
    api_updated = None
except Exception as e:
    print(f"❌ Error: {e}")
    api_pnl = None
    api_updated = None

# 2. Check database directly
print("\n2. DATABASE CHECK (paper_portfolio table)")
print("-" * 80)
try:
    import psycopg2
    from config.settings import get_settings
    
    settings = get_settings()
    
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT total_capital, available_cash, invested_amount, 
               total_pnl, today_pnl, updated_at
        FROM paper_portfolio
        WHERE id = 1
    """)
    row = cur.fetchone()
    
    print(f'✓ Total Capital:     ₹{row[0]:,.0f}')
    print(f'✓ Available Cash:    ₹{row[1]:,.0f}')
    print(f'✓ Invested Amount:   ₹{row[2]:,.0f}')
    print(f'✓ Total P&L:         ₹{row[3]:,.0f}')
    print(f'✓ Today P&L:         ₹{row[4]:,.0f}')
    
    db_updated = row[5]
    day = db_updated.day
    month = db_updated.strftime('%b')
    time_str = db_updated.strftime('%I:%M %p').lstrip('0').lower()
    print(f'✓ Updated At:        {day} {month}, {time_str}')
    
    # Check position count
    cur.execute("SELECT COUNT(*) FROM paper_positions WHERE quantity > 0")
    pos_count = cur.fetchone()[0]
    print(f'✓ Active Positions:  {pos_count}')
    
    db_pnl = float(row[3])
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error connecting to database: {e}")
    db_pnl = None

# 3. Verification summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

if api_pnl is not None and db_pnl is not None:
    if abs(api_pnl - db_pnl) < 0.01:
        print("✅ API and Database are IN SYNC!")
        print(f"   Both showing Total P&L: ₹{api_pnl:,.0f}")
    else:
        print("⚠️  MISMATCH DETECTED!")
        print(f"   API P&L:      ₹{api_pnl:,.0f}")
        print(f"   Database P&L: ₹{db_pnl:,.0f}")
        print(f"   Difference:   ₹{abs(api_pnl - db_pnl):,.0f}")
        print("\n   ACTION REQUIRED: Restart API server")
        print("   1. Stop API server (CTRL+C in the API terminal)")
        print("   2. Start API server: py start_api.py")
        print("   3. Refresh browser (F5)")

print("\n" + "=" * 80)
print("EXPECTED VALUES (after sync):")
print("-" * 80)
print("Total P&L:     ₹-9,237")
print("Available Cash: ₹298,630")
print("Invested:      ₹701,370")
print("Positions:     16")
print("=" * 80)
