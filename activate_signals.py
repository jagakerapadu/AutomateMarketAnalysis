"""Activate trading signals for paper trading"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

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

print("\n" + "="*80)
print("ACTIVATING SIGNALS FOR PAPER TRADING")
print("="*80 + "\n")

#Update ACTIVE signals to PENDING
cursor.execute("UPDATE signals SET status='PENDING' WHERE status='ACTIVE' AND signal_type='BUY'")
updated = cursor.rowcount

conn.commit()

# Show updated signals
cursor.execute("""
    SELECT symbol, signal_type, confidence, entry_price, target_price, status
    FROM signals 
    WHERE status='PENDING'
    ORDER BY confidence DESC
""")

signals = cursor.fetchall()

print(f"✅ Updated {updated} signals to PENDING status\n")
print(f"{'Symbol':<12} {'Type':<6} {'Conf':<6} {'Entry':<12} {'Target':<12} {'Status'}")
print("-"*70)

for s in signals:
    symbol, signal_type, conf, entry, target, status = s
    print(f"{symbol:<12} {signal_type:<6} {conf:>5}% Rs.{entry:>10,.2f} Rs.{target:>10,.2f} {status}")

print(f"\n{'='*80}")
print(f"✅ {len(signals)} SIGNALS READY FOR PAPER TRADING")
print("="*80)
print("\n🚀 Now run: py start_paper_trading.py\n")

cursor.close()
conn.close()
