"""Test Combined Portfolio and Main Dashboard APIs"""
import requests
import psycopg2
from config.settings import get_settings

API_URL = "http://localhost:8000"

def get_db_connection():
    settings = get_settings()
    return psycopg2.connect(
        host=settings.DB_HOST, port=settings.DB_PORT,
        database=settings.DB_NAME, user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )

print("\n" + "="*80)
print("MAIN DASHBOARD DATA VERIFICATION")
print("="*80)

# ============================================================================
# 1. COMBINED PORTFOLIO (Main Dashboard)
# ============================================================================
print("\n1. COMBINED PORTFOLIO (Stocks + Options):")
print("-" * 80)

conn = get_db_connection()
cursor = conn.cursor()

# Database values
cursor.execute("SELECT total_capital, available_cash, invested_amount, total_pnl FROM paper_portfolio WHERE id = 1")
stock_vals = cursor.fetchone()

cursor.execute("SELECT total_capital, available_cash, invested_amount, total_pnl FROM paper_options_portfolio WHERE id = 1")
opt_vals = cursor.fetchone()

db_combined_capital = float(stock_vals[0]) + float(opt_vals[0])
db_combined_available = float(stock_vals[1]) + float(opt_vals[1])
db_combined_invested = float(stock_vals[2]) + float(opt_vals[2])
db_combined_pnl = float(stock_vals[3]) + float(opt_vals[3])

print(f"DATABASE (Combined):")
print(f"  Total Capital:    ₹{db_combined_capital:,.2f}")
print(f"  Available Cash:   ₹{db_combined_available:,.2f}")
print(f"  Invested Amount:  ₹{db_combined_invested:,.2f}")
print(f"  Total P&L:        ₹{db_combined_pnl:,.2f}")
print(f"    - Stocks P&L:   ₹{float(stock_vals[3]):,.2f}")
print(f"    - Options P&L:  ₹{float(opt_vals[3]):,.2f}")

# API values
try:
    response = requests.get(f"{API_URL}/api/portfolio/combined-summary", timeout=10)
    if response.status_code == 200:
        api_data = response.json()
        print(f"\nAPI (Combined Endpoint):")
        print(f"  Total Capital:    ₹{api_data.get('total_capital', 0):,.2f}  {'✅' if abs(api_data.get('total_capital', 0) - db_combined_capital) < 0.01 else '❌'}")
        print(f"  Available Cash:   ₹{api_data.get('available', 0):,.2f}  {'✅' if abs(api_data.get('available', 0) - db_combined_available) < 0.01 else '❌'}")
        print(f"  Invested Amount:  ₹{api_data.get('invested', 0):,.2f}  {'✅' if abs(api_data.get('invested', 0) - db_combined_invested) < 0.01 else '❌'}")
        print(f"  Total P&L:        ₹{api_data.get('total_pnl', 0):,.2f}  {'✅' if abs(api_data.get('total_pnl', 0) - db_combined_pnl) < 0.01 else '❌'}")
        print(f"    - Stocks P&L:   ₹{api_data.get('stocks_pnl', 0):,.2f}")
        print(f"    - Options P&L:  ₹{api_data.get('options_pnl', 0):,.2f}")
        print(f"  Open Positions:   {api_data.get('open_positions', 0)}")
    else:
        print(f"\n❌ API Error: Status {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"\n❌ API Error: {e}")

# ============================================================================
# 2. MARKET OVERVIEW
# ============================================================================
print("\n2. MARKET OVERVIEW:")
print("-" * 80)

cursor.execute("""
    SELECT close, open, timestamp
    FROM market_ohlc
    WHERE symbol LIKE 'NIFTY%'
    ORDER BY timestamp DESC
    LIMIT 1
""")
nifty_data = cursor.fetchone()

if nifty_data:
    nifty_price = float(nifty_data[0])
    nifty_open = float(nifty_data[1])
    nifty_change = ((nifty_price - nifty_open) / nifty_open) * 100
    
    print(f"DATABASE (market_ohlc):")
    print(f"  NIFTY 50:      ₹{nifty_price:,.2f}")
    print(f"  Change:        {nifty_change:+.2f}%")
    print(f"  Last Updated:  {nifty_data[2]}")

try:
    response = requests.get(f"{API_URL}/api/market/overview", timeout=10)
    if response.status_code == 200:
        api_market = response.json()
        print(f"\nAPI (Market Overview):")
        print(f"  NIFTY 50:      ₹{api_market.get('nifty_price', 0):,.2f}  {'✅' if abs(api_market.get('nifty_price', 0) - nifty_price) < 0.01 else '❌'}")
        print(f"  Change:        {api_market.get('nifty_change', 0):+.2f}%  {'✅' if abs(api_market.get('nifty_change', 0) - nifty_change) < 0.01 else '❌'}")
        print(f"  BANK NIFTY:    ₹{api_market.get('banknifty_price', 0):,.2f}")
        print(f"  INDIA VIX:     {api_market.get('india_vix', 0)}")
    else:
        print(f"\n❌ API Error: Status {response.status_code}")
except Exception as e:
    print(f"\n❌ API Error: {e}")

# ============================================================================
# 3. TRADE STATISTICS
# ============================================================================
print("\n3. TRADE STATISTICS (30 Days):")
print("-" * 80)

cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN pnl > 0 THEN 1 END) as winners,
        COUNT(CASE WHEN pnl < 0 THEN 1 END) as losers,
        AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
        AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss
    FROM (
        SELECT pnl FROM paper_orders WHERE status = 'EXECUTED' AND pnl IS NOT NULL
        UNION ALL
        SELECT pnl FROM paper_options_orders WHERE status = 'EXECUTED' AND pnl IS NOT NULL
    ) combined_orders
""")
trade_stats = cursor.fetchone()

total_trades = trade_stats[0] or 0
winners = trade_stats[1] or 0
losers = trade_stats[2] or 0
avg_win = float(trade_stats[3]) if trade_stats[3] else 0
avg_loss = float(trade_stats[4]) if trade_stats[4] else 0
win_rate = (winners / total_trades * 100) if total_trades > 0 else 0

print(f"DATABASE (Combined Orders):")
print(f"  Total Trades:  {total_trades}")
print(f"  Win Rate:      {win_rate:.1f}%")
print(f"  Avg Win:       ₹{avg_win:,.0f}")
print(f"  Avg Loss:      ₹{avg_loss:,.0f}")

try:
    response = requests.get(f"{API_URL}/api/trades/stats?days=30", timeout=10)
    if response.status_code == 200:
        api_stats = response.json()
        print(f"\nAPI (Trade Stats):")
        print(f"  Total Trades:  {api_stats.get('total_trades', 0)}  {'✅' if api_stats.get('total_trades', 0) == total_trades else '❌'}")
        print(f"  Win Rate:      {api_stats.get('win_rate', 0):.1f}%  {'✅' if abs(api_stats.get('win_rate', 0) - win_rate) < 0.1 else '❌'}")
        print(f"  Avg Win:       ₹{api_stats.get('avg_win', 0):,.0f}  {'✅' if abs(api_stats.get('avg_win', 0) - avg_win) < 1 else '❌'}")
        print(f"  Avg Loss:      ₹{api_stats.get('avg_loss', 0):,.0f}  {'✅' if abs(api_stats.get('avg_loss', 0) - avg_loss) < 1 else '❌'}")
    else:
        print(f"\n❌ API Error: Status {response.status_code}")
except Exception as e:
    print(f"\n❌ API Error: {e}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ MAIN DASHBOARD VERIFICATION COMPLETE!")
print("="*80)
print("\n📝 Summary:")
print("   - Combined Portfolio shows stocks + options P&L")
print("   - Market Overview shows real NIFTY prices")
print("   - Trade Stats combines stock + options orders")
print("\n💡 What to check on dashboard:")
print(f"   1. Portfolio P&L should show: ₹{db_combined_pnl:,.2f}")
print(f"   2. NIFTY 50 should show: ₹{nifty_price:,.2f}")
print(f"   3. Total Trades should show: {total_trades}")
print(f"   4. Win Rate should show: {win_rate:.1f}%")
print("\n")
