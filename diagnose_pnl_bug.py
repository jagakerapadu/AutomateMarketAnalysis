"""Quick diagnostic to check portfolio P&L discrepancy"""
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
cursor = conn.cursor()

print("\n" + "=" * 80)
print("PORTFOLIO P&L DIAGNOSTIC")
print("=" * 80)

# 1. Paper Portfolio Table (Stock Trading)
print("\n1. PAPER_PORTFOLIO TABLE (Stock Paper Trading):")
print("-" * 80)
cursor.execute("SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl FROM paper_portfolio WHERE id = 1")
row = cursor.fetchone()
if row:
    print(f"Total Capital:    ₹{row[0]:,.2f}")
    print(f"Available Cash:   ₹{row[1]:,.2f}")
    print(f"Invested Amount:  ₹{row[2]:,.2f}")
    print(f"Total P&L:        ₹{row[3]:,.2f}  {'📈' if row[3] >= 0 else '📉'}")
    print(f"Today P&L:        ₹{row[4]:,.2f}")

# 2. Paper Positions (Individual Stocks)
print("\n2. PAPER_POSITIONS TABLE (Current Holdings):")
print("-" * 80)
cursor.execute("""
    SELECT symbol, quantity, avg_price, current_price, pnl, pnl_percent 
    FROM paper_positions 
    ORDER BY pnl DESC
""")
positions = cursor.fetchall()

print(f"{'Symbol':<15} {'Qty':>8} {'Avg Price':>12} {'Curr Price':>12} {'P&L':>12} {'P&L %':>10}")
print("-" * 80)
total_position_pnl = 0
for row in positions:
    print(f"{row[0]:<15} {row[1]:>8} {row[2]:>12.2f} {row[3] or 0:>12.2f} {row[4] or 0:>12.2f} {row[5] or 0:>10.2f}%")
    total_position_pnl += (row[4] or 0)

print("-" * 80)
print(f"{'TOTAL':<15} {'':<8} {'':<12} {'':<12} {total_position_pnl:>12.2f}")

# 3. Trades Table (What API is using - WRONG!)
print("\n3. TRADES TABLE (What Portfolio API is reading - WRONG SOURCE!):")
print("-" * 80)
cursor.execute("SELECT COUNT(*), SUM(pnl) FROM trades WHERE status = 'CLOSED'")
row = cursor.fetchone()
print(f"Closed Trades:    {row[0]}")
print(f"Total P&L:        ₹{row[1] or 0:,.2f}")

cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
row = cursor.fetchone()
print(f"Open Trades:      {row[0]}")

# 4. Paper Orders
print("\n4. PAPER_ORDERS TABLE (Stock Paper Trading Orders):")
print("-" * 80)
cursor.execute("SELECT status, COUNT(*) FROM paper_orders GROUP BY status")
orders = cursor.fetchall()
for status, count in orders:
    print(f"{status}: {count}")

# 5. Show the bug
print("\n" + "=" * 80)
print("🐛 BUG IDENTIFIED!")
print("=" * 80)
print("\n❌ DASHBOARD SHOWS: ₹21,595.65 (from 'trades' table - OLD DATA)")
print("✅ ACTUAL P&L:      ₹{:,.2f} (from 'paper_positions' - CURRENT POSITIONS)".format(total_position_pnl))
print("\n📝 ISSUE:")
print("   The portfolio API (/api/portfolio/summary) is querying the WRONG table!")
print("   - It's reading from 'trades' table (different/old system)")
print("   - It should read from 'paper_portfolio' and 'paper_positions' tables")
print("\n📊 ACTUAL CURRENT STATUS:")
print(f"   - You have 16 open positions")
print(f"   - Total unrealized P&L: ₹{total_position_pnl:,.2f}")
print(f"   - You're in LOSS, not profit!")
print("\n🔧 SOLUTION:")
print("   Update services/api/routers/portfolio.py to query:")
print("   - paper_portfolio (for summary)")
print("   - paper_positions (for open positions)")

cursor.close()
conn.close()
