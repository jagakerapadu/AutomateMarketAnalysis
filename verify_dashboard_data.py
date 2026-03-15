"""Comprehensive Dashboard Data Verification"""
import psycopg2
from config.settings import get_settings
from decimal import Decimal
from datetime import datetime

settings = get_settings()

conn = psycopg2.connect(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD
)
cursor = conn.cursor()

print("\n" + "=" * 100)
print("COMPREHENSIVE DASHBOARD DATA VERIFICATION")
print("=" * 100)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# PART 1: STOCK PAPER TRADING VERIFICATION
# ============================================================================
print("\n" + "=" * 100)
print("PART 1: STOCK PAPER TRADING")
print("=" * 100)

# 1.1 Portfolio Summary
print("\n1.1 PORTFOLIO SUMMARY (Dashboard Main KPIs)")
print("-" * 100)
cursor.execute("""
    SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl 
    FROM paper_portfolio WHERE id = 1
""")
portfolio = cursor.fetchone()

if portfolio:
    print(f"Total Capital:    ₹{portfolio[0]:,.2f}")
    print(f"Available Cash:   ₹{portfolio[1]:,.2f}")
    print(f"Invested Amount:  ₹{portfolio[2]:,.2f}")
    print(f"Portfolio P&L:    ₹{portfolio[3]:,.2f}")
    print(f"Today's P&L:      ₹{portfolio[4]:,.2f}")
else:
    print("⚠️  No portfolio data found!")

# 1.2 Calculate actual P&L from positions
cursor.execute("""
    SELECT 
        COUNT(*) as total_positions,
        COALESCE(SUM(pnl), 0) as total_pnl,
        COALESCE(SUM(invested_value), 0) as total_invested
    FROM paper_positions
""")
pos_summary = cursor.fetchone()

print(f"\nCalculated from Positions:")
print(f"Total Positions:  {pos_summary[0]}")
print(f"Total P&L:        ₹{pos_summary[1]:,.2f}")
print(f"Total Invested:   ₹{pos_summary[2]:,.2f}")

if abs(float(pos_summary[1])) > 0.01:
    if abs(float(portfolio[3] or 0) - float(pos_summary[1])) > 0.01:
        print(f"\n⚠️  MISMATCH DETECTED!")
        print(f"   Portfolio table shows: ₹{portfolio[3]:,.2f}")
        print(f"   Positions sum shows:   ₹{pos_summary[1]:,.2f}")
        print(f"   Dashboard should show: ₹{pos_summary[1]:,.2f} (from positions)")

# 1.3 Individual Positions (Top 10 by P&L)
print("\n1.3 OPEN POSITIONS (Top 10 by P&L)")
print("-" * 100)
cursor.execute("""
    SELECT symbol, quantity, avg_price, current_price, 
           invested_value, current_value, pnl, pnl_percent
    FROM paper_positions
    ORDER BY pnl DESC
    LIMIT 10
""")

print(f"{'Symbol':<15} {'Qty':>6} {'Avg Price':>12} {'Curr Price':>12} {'Invested':>14} {'Current Val':>14} {'P&L':>12} {'P&L %':>8}")
print("-" * 100)

positions = cursor.fetchall()
for pos in positions:
    symbol, qty, avg_price, curr_price, invested, curr_val, pnl, pnl_pct = pos
    print(f"{symbol:<15} {qty:>6} {avg_price:>12.2f} {curr_price or 0:>12.2f} "
          f"{invested:>14.2f} {curr_val or 0:>14.2f} {pnl or 0:>12.2f} {pnl_pct or 0:>7.2f}%")

# 1.4 Recent Orders
print("\n1.4 RECENT ORDERS (Last 10)")
print("-" * 100)
cursor.execute("""
    SELECT order_id, symbol, order_type, quantity, executed_price, 
           status, placed_at
    FROM paper_orders
    ORDER BY placed_at DESC
    LIMIT 10
""")

print(f"{'Order ID':<20} {'Symbol':<15} {'Type':<6} {'Qty':>6} {'Price':>10} {'Status':<10} {'Date':<20}")
print("-" * 100)

orders = cursor.fetchall()
for order in orders:
    order_id, symbol, order_type, qty, price, status, placed_at = order
    print(f"{order_id:<20} {symbol:<15} {order_type:<6} {qty:>6} {price or 0:>10.2f} {status:<10} {str(placed_at)[:19]}")

# 1.5 Signals
print("\n1.5 TRADING SIGNALS (Last 10)")
print("-" * 100)
cursor.execute("""
    SELECT id, symbol, signal_type, strategy, entry_price, 
           confidence, status, timestamp
    FROM signals
    ORDER BY timestamp DESC
    LIMIT 10
""")

print(f"{'ID':>5} {'Symbol':<15} {'Type':<6} {'Strategy':<20} {'Entry':>10} {'Conf':>5} {'Status':<10} {'Date':<20}")
print("-" * 100)

signals = cursor.fetchall()
for sig in signals:
    sig_id, symbol, sig_type, strategy, entry, conf, status, timestamp = sig
    print(f"{sig_id:>5} {symbol:<15} {sig_type:<6} {strategy:<20} {entry:>10.2f} {conf or 0:>5.0f} {status:<10} {str(timestamp)[:19]}")

# ============================================================================
# PART 2: NIFTY OPTIONS TRADING VERIFICATION
# ============================================================================
print("\n" + "=" * 100)
print("PART 2: NIFTY OPTIONS TRADING")
print("=" * 100)

# 2.1 Options Portfolio Summary
print("\n2.1 OPTIONS PORTFOLIO SUMMARY")
print("-" * 100)
cursor.execute("""
    SELECT total_capital, available_cash, invested_amount, 
           total_pnl, today_pnl, total_premium_paid, total_premium_received
    FROM paper_options_portfolio WHERE id = 1
""")
opt_portfolio = cursor.fetchone()

if opt_portfolio:
    print(f"Total Capital:          ₹{opt_portfolio[0]:,.2f}")
    print(f"Available Cash:         ₹{opt_portfolio[1]:,.2f}")
    print(f"Invested Amount:        ₹{opt_portfolio[2]:,.2f}")
    print(f"Total P&L:              ₹{opt_portfolio[3]:,.2f}")
    print(f"Today's P&L:            ₹{opt_portfolio[4]:,.2f}")
    print(f"Total Premium Paid:     ₹{opt_portfolio[5]:,.2f}")
    print(f"Total Premium Received: ₹{opt_portfolio[6]:,.2f}")
else:
    print("⚠️  No options portfolio data found!")

# 2.2 Options Positions
print("\n2.2 OPEN OPTIONS POSITIONS")
print("-" * 100)
cursor.execute("""
    SELECT symbol, strike, option_type, expiry_date, quantity,
           entry_premium, current_premium, invested_value, 
           current_value, pnl, pnl_percent, position_type
    FROM paper_options_positions
    ORDER BY pnl DESC
""")

opt_positions = cursor.fetchall()

if opt_positions:
    print(f"{'Symbol':<10} {'Strike':>8} {'Type':<4} {'Expiry':<12} {'Qty':>4} "
          f"{'Entry Prem':>11} {'Curr Prem':>11} {'Invested':>12} {'Curr Val':>12} {'P&L':>12} {'P&L %':>8}")
    print("-" * 100)
    
    for pos in opt_positions:
        symbol, strike, opt_type, expiry, qty, entry_prem, curr_prem, invested, curr_val, pnl, pnl_pct, pos_type = pos
        print(f"{symbol:<10} {strike:>8.0f} {opt_type:<4} {str(expiry):<12} {qty:>4} "
              f"{entry_prem:>11.2f} {curr_prem or 0:>11.2f} {invested:>12.2f} "
              f"{curr_val or 0:>12.2f} {pnl or 0:>12.2f} {pnl_pct or 0:>7.2f}%")
else:
    print("ℹ️  No open options positions")

# 2.3 Options Orders
print("\n2.3 RECENT OPTIONS ORDERS (Last 10)")
print("-" * 100)
cursor.execute("""
    SELECT order_id, symbol, strike, option_type, order_type,
           quantity, executed_premium, status, placed_at
    FROM paper_options_orders
    ORDER BY placed_at DESC
    LIMIT 10
""")

opt_orders = cursor.fetchall()

if opt_orders:
    print(f"{'Order ID':<25} {'Symbol':<10} {'Strike':>8} {'Opt':<4} {'Type':<6} "
          f"{'Qty':>4} {'Premium':>10} {'Status':<10} {'Date':<20}")
    print("-" * 100)
    
    for order in opt_orders:
        order_id, symbol, strike, opt_type, order_type, qty, premium, status, placed_at = order
        print(f"{order_id:<25} {symbol:<10} {strike:>8.0f} {opt_type:<4} {order_type:<6} "
              f"{qty:>4} {premium or 0:>10.2f} {status:<10} {str(placed_at)[:19]}")
else:
    print("ℹ️  No options orders yet")

# 2.4 Options Signals
print("\n2.4 OPTIONS SIGNALS (Last 10)")
print("-" * 100)
cursor.execute("""
    SELECT id, symbol, strike, option_type, signal_type, 
           entry_premium, confidence, status, timestamp
    FROM options_signals
    ORDER BY timestamp DESC
    LIMIT 10
""")

opt_signals = cursor.fetchall()

if opt_signals:
    print(f"{'ID':>5} {'Symbol':<10} {'Strike':>8} {'Opt':<4} {'Signal':<6} "
          f"{'Premium':>10} {'Conf':>5} {'Status':<10} {'Date':<20}")
    print("-" * 100)
    
    for sig in opt_signals:
        sig_id, symbol, strike, opt_type, sig_type, premium, conf, status, timestamp = sig
        print(f"{sig_id:>5} {symbol:<10} {strike:>8.0f} {opt_type:<4} {sig_type:<6} "
              f"{premium:>10.2f} {conf or 0:>5.0f} {status:<10} {str(timestamp)[:19]}")
else:
    print("ℹ️  No options signals yet")

# ============================================================================
# PART 3: MARKET DATA
# ============================================================================
print("\n" + "=" * 100)
print("PART 3: MARKET DATA (For Dashboard Market Overview)")
print("=" * 100)

# 3.1 Latest OHLC Data
print("\n3.1 LATEST MARKET DATA (OHLC)")
print("-" * 100)
cursor.execute("""
    SELECT DISTINCT ON (symbol) 
        symbol, timestamp, open, high, low, close, volume
    FROM market_ohlc
    WHERE timeframe = '1d'
    ORDER BY symbol, timestamp DESC
    LIMIT 10
""")

market_data = cursor.fetchall()

if market_data:
    print(f"{'Symbol':<15} {'Date':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>12}")
    print("-" * 100)
    
    for data in market_data:
        symbol, timestamp, open_p, high, low, close, volume = data
        print(f"{symbol:<15} {str(timestamp)[:19]:<20} {open_p:>10.2f} {high:>10.2f} {low:>10.2f} {close:>10.2f} {volume:>12,}")
else:
    print("⚠️  No market data found! Dashboard market overview will be empty.")

# 3.2 Global Indices
print("\n3.2 GLOBAL INDICES")
print("-" * 100)
cursor.execute("""
    SELECT DISTINCT ON (index_name)
        index_name, value, change_percent, timestamp
    FROM global_indices
    ORDER BY index_name, timestamp DESC
""")

indices = cursor.fetchall()

if indices:
    print(f"{'Index':<20} {'Value':>12} {'Change %':>10} {'Updated':<20}")
    print("-" * 100)
    
    for idx in indices:
        idx_name, value, change_pct, timestamp = idx
        print(f"{idx_name:<20} {value:>12.2f} {change_pct or 0:>9.2f}% {str(timestamp)[:19]}")
else:
    print("ℹ️  No global indices data")

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================
print("\n" + "=" * 100)
print("VERIFICATION SUMMARY")
print("=" * 100)

issues = []

# Check stock trading
if not portfolio:
    issues.append("❌ Stock paper_portfolio table is empty")
elif pos_summary[0] == 0:
    issues.append("⚠️  Stock paper_positions table is empty (no open positions)")

if not orders:
    issues.append("⚠️  No stock orders in paper_orders table")

if not signals:
    issues.append("⚠️  No trading signals in signals table")

# Check options trading
if not opt_portfolio:
    issues.append("❌ Options paper_options_portfolio table is empty")
    
if not opt_positions:
    issues.append("ℹ️  No open options positions (may be normal if not trading options yet)")

if not market_data:
    issues.append("❌ CRITICAL: No market_ohlc data! Market overview will be broken!")

# Print results
if issues:
    print("\n🔍 ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n✅ All data tables have content!")

print("\n📊 DASHBOARD COMPONENTS STATUS:")
print("-" * 100)
print(f"✅ Stock Portfolio Summary:  {'Has Data' if portfolio else 'EMPTY'}")
print(f"✅ Stock Positions:          {pos_summary[0]} positions")
print(f"✅ Stock Orders:             {len(orders)} orders")
print(f"✅ Trading Signals:          {len(signals)} signals")
print(f"✅ Options Portfolio:        {'Has Data' if opt_portfolio else 'EMPTY'}")
print(f"✅ Options Positions:        {len(opt_positions)} positions")
print(f"✅ Options Orders:           {len(opt_orders)} orders")
print(f"✅ Market Data:              {len(market_data)} symbols")
print(f"✅ Global Indices:           {len(indices)} indices")

print("\n" + "=" * 100)
print("NEXT STEPS")
print("=" * 100)
print("1. If API is running and dashboard is open:")
print("   - Refresh dashboard (F5)")
print("   - Check each component matches the data above")
print("2. If some components are empty:")
print("   - Run data fetching scripts (fetch_all_data.py)")
print("   - Update positions prices (update_paper_prices.py)")
print("3. Compare dashboard values with this report line by line")
print("=" * 100 + "\n")

cursor.close()
conn.close()
