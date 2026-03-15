"""Quick Fix: Update Portfolio P&L from Actual Positions"""
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
print("QUICK FIX: UPDATING PORTFOLIO P&L FROM POSITIONS")
print("=" * 80)

# ============================================================================
# FIX 1: Stock Portfolio P&L
# ============================================================================
print("\n1. FIXING STOCK PORTFOLIO P&L...")
print("-" * 80)

# Calculate from positions
cursor.execute("""
    SELECT 
        COALESCE(SUM(pnl), 0) as total_pnl,
        COALESCE(SUM(invested_value), 0) as invested,
        COALESCE(SUM(current_value), 0) as current_val,
        COUNT(*) as position_count
    FROM paper_positions
""")

result = cursor.fetchone()
total_pnl, invested, current_val, position_count = result

print(f"Calculated from {position_count} positions:")
print(f"  Total P&L:        ₹{total_pnl:,.2f}")
print(f"  Invested:         ₹{invested:,.2f}")
print(f"  Current Value:    ₹{current_val or 0:,.2f}")

# Get total capital
cursor.execute("SELECT total_capital FROM paper_portfolio WHERE id = 1")
total_capital = cursor.fetchone()[0]

available_cash = float(total_capital) - float(invested)

print(f"\nUpdating paper_portfolio table...")
cursor.execute("""
    UPDATE paper_portfolio
    SET total_pnl = %s,
        invested_amount = %s,
        available_cash = %s,
        today_pnl = %s,
        updated_at = NOW()
    WHERE id = 1
""", (total_pnl, invested, available_cash, total_pnl))

conn.commit()
print(f"✅ Stock portfolio updated!")
print(f"   Total P&L:     ₹{total_pnl:,.2f}")
print(f"   Invested:      ₹{invested:,.2f}")
print(f"   Available:     ₹{available_cash:,.2f}")

# ============================================================================
# FIX 2: Options Portfolio P&L
# ============================================================================
print("\n2. FIXING OPTIONS PORTFOLIO P&L...")
print("-" * 80)

# Calculate from options positions
cursor.execute("""
    SELECT 
        COALESCE(SUM(pnl), 0) as total_pnl,
        COALESCE(SUM(invested_value), 0) as invested,
        COALESCE(SUM(current_value), 0) as current_val,
        COUNT(*) as position_count
    FROM paper_options_positions
""")

result = cursor.fetchone()
opt_pnl, opt_invested, opt_current_val, opt_count = result

print(f"Calculated from {opt_count} options positions:")
print(f"  Total P&L:        ₹{opt_pnl:,.2f}")
print(f"  Invested:         ₹{opt_invested:,.2f}")
print(f"  Current Value:    ₹{opt_current_val or 0:,.2f}")

if opt_count > 0:
    # Get total capital
    cursor.execute("SELECT total_capital FROM paper_options_portfolio WHERE id = 1")
    opt_total_capital = cursor.fetchone()[0]
    
    opt_available_cash = float(opt_total_capital) - float(opt_invested)
    
    print(f"\nUpdating paper_options_portfolio table...")
    cursor.execute("""
        UPDATE paper_options_portfolio
        SET total_pnl = %s,
            invested_amount = %s,
            available_cash = %s,
            today_pnl = %s,
            updated_at = NOW()
        WHERE id = 1
    """, (opt_pnl, opt_invested, opt_available_cash, opt_pnl))
    
    conn.commit()
    print(f"✅ Options portfolio updated!")
    print(f"   Total P&L:     ₹{opt_pnl:,.2f}")
    print(f"   Invested:      ₹{opt_invested:,.2f}")
    print(f"   Available:     ₹{opt_available_cash:,.2f}")
else:
    print("ℹ️  No options positions to update")

# ============================================================================
# VERIFICATION
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICATION - PORTFOLIO VALUES AFTER FIX")
print("=" * 80)

print("\nStock Portfolio:")
cursor.execute("""
    SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl
    FROM paper_portfolio WHERE id = 1
""")
row = cursor.fetchone()
print(f"  Total Capital:    ₹{row[0]:,.2f}")
print(f"  Available Cash:   ₹{row[1]:,.2f}")
print(f"  Invested Amount:  ₹{row[2]:,.2f}")
print(f"  Total P&L:        ₹{row[3]:,.2f}  {'📉 LOSS' if row[3] < 0 else '📈 PROFIT'}")
print(f"  Today P&L:        ₹{row[4]:,.2f}")

print("\nOptions Portfolio:")
cursor.execute("""
    SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl
    FROM paper_options_portfolio WHERE id = 1
""")
row = cursor.fetchone()
print(f"  Total Capital:    ₹{row[0]:,.2f}")
print(f"  Available Cash:   ₹{row[1]:,.2f}")
print(f"  Invested Amount:  ₹{row[2]:,.2f}")  
print(f"  Total P&L:        ₹{row[3]:,.2f}  {'📉 LOSS' if row[3] < 0 else '📈 PROFIT'}")
print(f"  Today P&L:        ₹{row[4]:,.2f}")

print("\n" + "=" *80)
print("✅ PORTFOLIO P&L FIXED!")
print("=" * 80)
print("\nNEXT STEPS:")
print("1. Restart API server (if running): CTRL+C then py start_api.py")
print("2. Refresh dashboard: Press F5 in browser")
print("3. Dashboard should now show correct P&L values")
print("=" * 80 + "\n")

cursor.close()
conn.close()
