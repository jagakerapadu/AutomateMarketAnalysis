"""Sync Signal Status with Actual Positions"""
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

print("="*80)
print("SYNCING SIGNAL STATUS WITH POSITIONS")
print("="*80)

# Get all symbols with open positions
cursor.execute("""
    SELECT DISTINCT symbol FROM paper_positions
""")
open_symbols = [row[0] for row in cursor.fetchall()]

print(f"\nSymbols with open positions: {len(open_symbols)}")
print(", ".join(open_symbols))

# Update signals for these symbols from PENDING to ACTIVE
cursor.execute("""
    UPDATE signals
    SET status = 'ACTIVE'
    WHERE symbol = ANY(%s)
    AND status = 'PENDING'
    AND signal_type = 'BUY'
    RETURNING symbol, strategy, created_at
""", (open_symbols,))

updated = cursor.fetchall()
conn.commit()

print(f"\n✅ Updated {len(updated)} signals from PENDING → ACTIVE:")
print("-"*80)
for symbol, strategy, created in updated:
    print(f"  {symbol}: {strategy} ({created.strftime('%d %b, %I:%M %p')})")

# Show remaining pending signals
cursor.execute("""
    SELECT symbol, strategy, entry_price, confidence, created_at
    FROM signals
    WHERE status = 'PENDING'
    ORDER BY created_at DESC
""")

remaining_pending = cursor.fetchall()

print(f"\n\nREMAINING PENDING SIGNALS ({len(remaining_pending)}):")
print("-"*80)
if remaining_pending:
    for symbol, strategy, entry, conf, created in remaining_pending:
        print(f"  {symbol}: {strategy} @ ₹{entry:.2f} ({conf}%) - {created.strftime('%d %b %I:%M %p')}")
else:
    print("  None - all signals synchronized!")

# Show signal status breakdown
cursor.execute("""
    SELECT status, COUNT(*) 
    FROM signals 
    GROUP BY status
    ORDER BY COUNT(*) DESC
""")

status_counts = cursor.fetchall()

print("\n" + "="*80)
print("SIGNAL STATUS SUMMARY:")
print("-"*80)
for status, count in status_counts:
    print(f"  {status}: {count} signals")

cursor.close()
conn.close()

print("\n" + "="*80)
