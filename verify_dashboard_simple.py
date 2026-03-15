"""Simple Dashboard Verification - Test API vs Database"""
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
print("DASHBOARD VERIFICATION - API vs DATABASE")
print("="*80)

# Test 1: Stock Portfolio
print("\n1. STOCK PORTFOLIO:")
print("-" * 80)
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT total_capital, available_cash, invested_amount, total_pnl FROM paper_portfolio WHERE id = 1")
db_vals = cursor.fetchone()

try:
    response = requests.get(f"{API_URL}/api/portfolio/summary", timeout=5)
    api_data = response.json() if response.status_code == 200 else {}
    
    print(f"Total Capital:    DB = ₹{db_vals[0]:,.2f}  |  API = ₹{api_data.get('total_capital', 0):,.2f}  |  {'✅' if abs(float(db_vals[0]) - float(api_data.get('total_capital', 0))) < 0.01 else '❌'}")
    print(f"Available Cash:   DB = ₹{db_vals[1]:,.2f}  |  API = ₹{api_data.get('available_cash', 0):,.2f}  |  {'✅' if abs(float(db_vals[1]) - float(api_data.get('available_cash', 0))) < 0.01 else '❌'}")
    print(f"Invested Amount:  DB = ₹{db_vals[2]:,.2f}  |  API = ₹{api_data.get('invested_amount', 0):,.2f}  |  {'✅' if abs(float(db_vals[2]) - float(api_data.get('invested_amount', 0))) < 0.01 else '❌'}")
    print(f"Total P&L:        DB = ₹{db_vals[3]:,.2f}  |  API = ₹{api_data.get('total_pnl', 0):,.2f}  |  {'✅' if abs(float(db_vals[3]) - float(api_data.get('total_pnl', 0))) < 0.01 else '❌'}")
except Exception as e:
    print(f"❌ API Error: {e}")

# Test 2: Stock Positions Count
print("\n2. STOCK POSITIONS:")
print("-" * 80)
cursor.execute("SELECT COUNT(*) FROM paper_positions WHERE quantity > 0")
db_count = cursor.fetchone()[0]

try:
    response = requests.get(f"{API_URL}/api/portfolio/positions", timeout=5)
    api_count = len(response.json()) if response.status_code == 200 else 0
    print(f"Position Count:   DB = {db_count}  |  API = {api_count}  |  {'✅' if db_count == api_count else '❌'}")
except Exception as e:
    print(f"❌ API Error: {e}")

# Test 3: Options Portfolio
print("\n3. OPTIONS PORTFOLIO:")
print("-" * 80)
cursor.execute("SELECT total_capital, available_cash, invested_amount, total_pnl FROM paper_options_portfolio WHERE id = 1")
opt_vals = cursor.fetchone()

try:
    response = requests.get(f"{API_URL}/api/options-trading/portfolio", timeout=5)
    api_data = response.json() if response.status_code == 200 else {}
    
    print(f"Total Capital:    DB = ₹{opt_vals[0]:,.2f}  |  API = ₹{api_data.get('total_capital', 0):,.2f}  |  {'✅' if abs(float(opt_vals[0]) - float(api_data.get('total_capital', 0))) < 0.01 else '❌'}")
    print(f"Available Cash:   DB = ₹{opt_vals[1]:,.2f}  |  API = ₹{api_data.get('available_cash', 0):,.2f}  |  {'✅' if abs(float(opt_vals[1]) - float(api_data.get('available_cash', 0))) < 0.01 else '❌'}")
    print(f"Invested Amount:  DB = ₹{opt_vals[2]:,.2f}  |  API = ₹{api_data.get('invested_amount', 0):,.2f}  |  {'✅' if abs(float(opt_vals[2]) - float(api_data.get('invested_amount', 0))) < 0.01 else '❌'}")
    print(f"Total P&L:        DB = ₹{opt_vals[3]:,.2f}  |  API = ₹{api_data.get('total_pnl', 0):,.2f}  |  {'✅' if abs(float(opt_vals[3]) - float(api_data.get('total_pnl', 0))) < 0.01 else '❌'}")
except Exception as e:
    print(f"❌ API Error: {e}")

# Test 4: Options Positions Count
print("\n4. OPTIONS POSITIONS:")
print("-" * 80)
cursor.execute("SELECT COUNT(*) FROM paper_options_positions WHERE quantity > 0")
opt_count = cursor.fetchone()[0]

try:
    response = requests.get(f"{API_URL}/api/options-trading/positions", timeout=5)
    api_opt_count = len(response.json()) if response.status_code == 200 else 0
    print(f"Position Count:   DB = {opt_count}  |  API = {api_opt_count}  |  {'✅' if opt_count == api_opt_count else '❌'}")
except Exception as e:
    print(f"❌ API Error: {e}")

# Test 5: Market Data
print("\n5. MARKET DATA (NIFTY):")
print("-" * 80)
cursor.execute("SELECT close, timestamp FROM market_ohlc WHERE symbol LIKE 'NIFTY%' ORDER BY timestamp DESC LIMIT 1")
market_data = cursor.fetchone()
if market_data:
    print(f"NIFTY Price:      ₹{market_data[0]:,.2f}  (Updated: {market_data[1]})")
else:
    print("❌ No NIFTY data in market_ohlc table")

# Test 6: Signals
print("\n6. SIGNALS:")
print("-" * 80)
cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'ACTIVE'")
stock_signals = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM options_signals WHERE status = 'ACTIVE'")
options_signals = cursor.fetchone()[0]

print(f"Stock Signals:    DB = {stock_signals}")
print(f"Options Signals:  DB = {options_signals}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ VERIFICATION COMPLETE!")
print("="*80)
print("\nIf all values match (✅), dashboard is accurate.")
print("Refresh dashboard (F5) to see latest data.\n")
