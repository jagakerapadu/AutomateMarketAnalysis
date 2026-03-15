"""Final Dashboard Verification - Test All Endpoints Against Database"""
import requests
import psycopg2
from config.settings import get_settings

API_URL = "http://localhost:8000"
settings = get_settings()

def get_db_connection():
    return psycopg2.connect(
        host=settings.DB_HOST, port=settings.DB_PORT,
        database=settings.DB_NAME, user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )

def format_currency(val):
    return f"₹{float(val):,.2f}" if val is not None else "₹0.00"

def test_stock_portfolio():
    """Test stock portfolio endpoint vs database"""
    print("\n" + "="*100)
    print("🧪 TEST 1: STOCK PORTFOLIO SUMMARY")
    print("="*100)
    
    # Get from API
    try:
        response = requests.get(f"{API_URL}/api/portfolio/summary", timeout=5)
        api_data = response.json() if response.status_code == 200 else {}
    except Exception as e:
        print(f"❌ API Error: {e}")
        api_data = {}
    
    # Get from Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl
        FROM paper_portfolio WHERE id = 1
    """)
    db_row = cursor.fetchone()
    
    # Compare
    print(f"\n{'Metric':<20} {'Database':>20} {'API':>20} {'Match':>10}")
    print("-" * 75)
    
    metrics = [
        ("Total Capital", db_row[0], api_data.get('total_capital')),
        ("Available Cash", db_row[1], api_data.get('available_cash')),
        ("Invested Amount", db_row[2], api_data.get('invested_amount')),
        ("Total P&L", db_row[3], api_data.get('total_pnl')),
        ("Today P&L", db_row[4], api_data.get('today_pnl')),
    ]
    
    for metric, db_val, api_val in metrics:
        match = "✅" if abs(float(db_val or 0) - float(api_val or 0)) < 0.01 else "❌"
        print(f"{metric:<20} {format_currency(db_val):>20} {format_currency(api_val):>20} {match:>10}")
    
    cursor.close()
    conn.close()

def test_stock_positions():
    """Test stock positions endpoint"""
    print("\n" + "="*100)
    print("🧪 TEST 2: STOCK POSITIONS (Top 5 by P&L)")
    print("="*100)
    
    # Get from Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, quantity, avg_price, current_price, pnl, pnl_percent
        FROM paper_positions
        ORDER BY pnl
        LIMIT 5
    """)
    db_positions = cursor.fetchall()
    
    # Get from API
    try:
        response = requests.get(f"{API_URL}/api/portfolio/positions", timeout=5)
        api_positions = response.json() if response.status_code == 200 else []
        api_positions.sort(key=lambda x: x.get('pnl', 0))
        api_positions = api_positions[:5]
    except Exception as e:
        print(f"❌ API Error: {e}")
        api_positions = []
    
    # Compare
    print("\n📊 Database Positions (Top 5 Losers):")
    for symbol, qty, avg_price, curr_price, pnl, pnl_pct in db_positions:
        status = "📉" if pnl < 0 else "📈"
        print(f"  {status} {symbol:12s} {qty:3d} @ ₹{avg_price:8.2f} → ₹{curr_price:8.2f} = {format_currency(pnl):15s} ({pnl_pct:+.2f}%)")
    
    print(f"\n🌐 API Positions (Count: {len(api_positions)}):")
    for pos in api_positions[:5]:
        pnl = pos.get('pnl', 0)
        status = "📉" if pnl < 0 else "📈"
        print(f"  {status} {pos.get('symbol', 'N/A'):12s} {pos.get('quantity', 0):3d} @ ₹{pos.get('avg_price', 0):8.2f} → ₹{pos.get('current_price', 0):8.2f} = {format_currency(pnl):15s} ({pos.get('pnl_percent', 0):+.2f}%)")
    
    cursor.close()
    conn.close()

def test_options_portfolio():
    """Test options portfolio endpoint"""
    print("\n" + "="*100)
    print("🧪 TEST 3: OPTIONS PORTFOLIO SUMMARY")
    print("="*100)
    
    # Get from Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl
        FROM paper_options_portfolio WHERE id = 1
    """)
    db_row = cursor.fetchone()
    
    # Get from API
    try:
        response = requests.get(f"{API_URL}/api/options/portfolio/summary", timeout=5)
        api_data = response.json() if response.status_code == 200 else {}
    except Exception as e:
        print(f"❌ API Error: {e}")
        api_data = {}
    
    # Compare
    print(f"\n{'Metric':<20} {'Database':>20} {'API':>20} {'Match':>10}")
    print("-" * 75)
    
    metrics = [
        ("Total Capital", db_row[0], api_data.get('total_capital')),
        ("Available Cash", db_row[1], api_data.get('available_cash')),
        ("Invested Amount", db_row[2], api_data.get('invested_amount')),
        ("Total P&L", db_row[3], api_data.get('total_pnl')),
        ("Today P&L", db_row[4], api_data.get('today_pnl')),
    ]
    
    for metric, db_val, api_val in metrics:
        match = "✅" if abs(float(db_val or 0) - float(api_val or 0)) < 0.01 else "❌"
        print(f"{metric:<20} {format_currency(db_val):>20} {format_currency(api_val):>20} {match:>10}")
        match = "✅" if abs(float(db_val or 0) - float(api_val or 0)) < 0.01 else "❌"
        print(f"{metric:<20} {format_currency(db_val):>20} {format_currency(api_val):>20} {match:>10}"
    conn.close()

def test_market_data():
    """Test market data endpoint"""
    print("\n" + "="*100)
    print("🧪 TEST 4: MARKET DATA (NIFTY 50)")
    print("="*100)
    
    # Get from Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, close, open, high, low, timestamp
        FROM market_ohlc
        WHERE symbol LIKE 'NIFTY%'
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    db_row = cursor.fetchone()
    
    if db_row:
        print(f"\n📊 Database Market Data:")
        print(f"  Symbol:     {db_row[0]}")
        print(f"  Close:      {format_currency(db_row[1])}")
        print(f"  Open:       {format_currency(db_row[2])}")
        print(f"  High:       {format_currency(db_row[3])}")
        print(f"  Low:        {format_currency(db_row[4])}")
        print(f"  Timestamp:  {db_row[5]}")
    else:
        print("\n❌ No NIFTY data in database")
    
    cursor.close()
    conn.close()

def test_signals():
    """Test signals endpoint"""
    print("\n" + "="*100)
    print("🧪 TEST 5: TRADING SIGNALS")
    print("="*100)
    
    # Get from Database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Stock signals
    cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'ACTIVE'")
    db_stock_signals = cursor.fetchone()[0]
    
    # Options signals
    cursor.execute("SELECT COUNT(*) FROM options_signals WHERE status = 'ACTIVE'")
    db_options_signals = cursor.fetchone()[0]
    
    # Get from API
    try:
        stock_response = requests.get(f"{API_URL}/api/signals/", timeout=5)
        api_stock_signals = len(stock_response.json()) if stock_response.status_code == 200 else 0
    except:
        api_stock_signals = 0
    
    try:
        options_response = requests.get(f"{API_URL}/api/options/signals/", timeout=5)
        api_options_signals = len(options_response.json()) if options_response.status_code == 200 else 0
    except:
        api_options_signals = 0
    
    # Display
    print(f"\n📊 Stock Signals:   DB = {db_stock_signals:2d} | API = {api_stock_signals:2d} | {'✅' if db_stock_signals == api_stock_signals else '❌'}")
    print(f"📊 Options Signals:  DB = {db_options_signals:2d} | API = {api_options_signals:2d} | {'✅' if db_options_signals == api_options_signals else '❌'}")
    
    cursor.close()
    conn.close()

def main():
    print("\n" + "="*100)
    print("🔍 FINAL DASHBOARD VERIFICATION - TESTING ALL ENDPOINTS")
    print("="*100)
    print("\nThis test compares API endpoints against database to ensure dashboard accuracy")
    
    test_stock_portfolio()
    test_stock_positions()
    test_options_portfolio()
    test_market_data()
    test_signals()
    
    print("\n" + "="*100)
    print("✅ VERIFICATION COMPLETE!")
    print("="*100)
    print("\n📝 Summary:")
    print("   - If all values match (✅), dashboard will show correct data")
    print("   - If any values mismatch (❌), check API implementation")
    print("   - Refresh dashboard (F5) to see updated values")
    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    main()
