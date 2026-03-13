"""
Complete Trading Analysis for March 13, 2026
Verify all transactions, calculations, and data consistency
"""
import psycopg2
from config.settings import get_settings
from datetime import datetime
from decimal import Decimal

settings = get_settings()
conn = psycopg2.connect(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD
)
cursor = conn.cursor()

print("="*90)
print(" " * 25 + "MARCH 13, 2026 - TRADING ANALYSIS")
print("="*90)
print(f"Generated at: {datetime.now().strftime('%I:%M:%S %p')}")

# ============================================================================
# 1. STARTING CAPITAL
# ============================================================================
print("\n" + "="*90)
print("1. STARTING POSITION")
print("-"*90)

cursor.execute("""
    SELECT total_capital, available_cash, invested_amount, total_pnl
    FROM paper_portfolio
    ORDER BY id DESC LIMIT 1
""")
portfolio = cursor.fetchone()

starting_capital = float(portfolio[0])
current_cash = float(portfolio[1])
portfolio_invested = float(portfolio[2])  # Save original to avoid loop overwrite
portfolio_cash = float(portfolio[1])  # Save original cash value
total_pnl = float(portfolio[3])

print(f"Starting Capital:      ₹{starting_capital:>15,.2f}")
print(f"Current Available:     ₹{portfolio_cash:>15,.2f}")
print(f"Currently Invested:    ₹{portfolio_invested:>15,.2f}")
print(f"Total P&L (All Time):  ₹{total_pnl:>15,.2f}")

# ============================================================================
# 2. ALL BUY TRANSACTIONS TODAY
# ============================================================================
print("\n" + "="*90)
print("2. BUY TRANSACTIONS - MARCH 13, 2026")
print("-"*90)

cursor.execute("""
    SELECT order_id, symbol, quantity, executed_price, 
           (quantity * executed_price) as amount,
           executed_at, status, signal_id
    FROM paper_orders
    WHERE order_type = 'BUY' 
    AND DATE(executed_at) = '2026-03-13'
    ORDER BY executed_at
""")

buy_orders = cursor.fetchall()

print(f"\nTotal BUY Orders: {len(buy_orders)}")
print("-"*90)
print(f"{'Time':<10} {'Symbol':<12} {'Qty':>6} {'Price':>12} {'Amount':>16} {'Status':<10} {'Signal'}")
print("-"*90)

total_bought_today = 0
for order in buy_orders:
    order_id, symbol, qty, price, amount, executed, status, signal_id = order
    time_str = executed.strftime('%I:%M %p')
    print(f"{time_str:<10} {symbol:<12} {qty:>6} ₹{price:>11,.2f} ₹{amount:>15,.2f} {status:<10} #{signal_id if signal_id else 'N/A'}")
    total_bought_today += float(amount)

print("-"*90)
print(f"{'TOTAL BUY AMOUNT:':<30} ₹{total_bought_today:>15,.2f}")

# ============================================================================
# 3. ALL SELL TRANSACTIONS TODAY
# ============================================================================
print("\n" + "="*90)
print("3. SELL TRANSACTIONS - MARCH 13, 2026")
print("-"*90)

cursor.execute("""
    SELECT order_id, symbol, quantity, executed_price,
           (quantity * executed_price) as amount,
           executed_at, status
    FROM paper_orders
    WHERE order_type = 'SELL'
    AND DATE(executed_at) = '2026-03-13'
    ORDER BY executed_at
""")

sell_orders = cursor.fetchall()

print(f"\nTotal SELL Orders: {len(sell_orders)}")
print("-"*90)
print(f"{'Time':<10} {'Symbol':<12} {'Qty':>6} {'Price':>12} {'Amount':>16} {'Status':<10}")
print("-"*90)

total_sold = 0
for order in sell_orders:
    order_id, symbol, qty, price, amount, executed, status = order
    time_str = executed.strftime('%I:%M %p')
    print(f"{time_str:<10} {symbol:<12} {qty:>6} ₹{price:>11,.2f} ₹{amount:>15,.2f} {status:<10}")
    total_sold += float(amount)

print("-"*90)
print(f"{'TOTAL SELL AMOUNT:':<30} ₹{total_sold:>15,.2f}")

# ============================================================================
# 4. CALCULATE PNL FOR CLOSED POSITIONS TODAY
# ============================================================================
print("\n" + "="*90)
print("4. CLOSED POSITIONS P&L (Sold Today)")
print("-"*90)

# For each SELL, find corresponding BUY to calculate P&L
closed_positions = []
for sell_order in sell_orders:
    sell_id, symbol, sell_qty, sell_price, sell_amount, sell_time, status = sell_order
    
    # Find BUY orders for this symbol
    cursor.execute("""
        SELECT quantity, executed_price, executed_at
        FROM paper_orders
        WHERE symbol = %s 
        AND order_type = 'BUY'
        AND executed_at < %s
        ORDER BY executed_at
    """, (symbol, sell_time))
    
    buy_history = cursor.fetchall()
    
    # Calculate average buy price
    total_bought_qty = sum(b[0] for b in buy_history)
    if total_bought_qty > 0:
        weighted_price = sum(b[0] * float(b[1]) for b in buy_history) / total_bought_qty
        
        # P&L calculation
        buy_cost = sell_qty * weighted_price
        sell_value = float(sell_amount)
        pnl = sell_value - buy_cost
        pnl_pct = (pnl / buy_cost) * 100 if buy_cost > 0 else 0
        
        closed_positions.append({
            'symbol': symbol,
            'qty': sell_qty,
            'buy_price': weighted_price,
            'sell_price': float(sell_price),
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'time': sell_time
        })

if closed_positions:
    print(f"\n{'Symbol':<12} {'Qty':>6} {'Buy Price':>12} {'Sell Price':>12} {'P&L':>16} {'%'}")
    print("-"*90)
    total_closed_pnl = 0
    for pos in closed_positions:
        print(f"{pos['symbol']:<12} {pos['qty']:>6} ₹{pos['buy_price']:>11,.2f} ₹{pos['sell_price']:>11,.2f} ₹{pos['pnl']:>15,.2f} {pos['pnl_pct']:>6.2f}%")
        total_closed_pnl += pos['pnl']
    print("-"*90)
    print(f"{'REALIZED P&L (Closed):':<30} ₹{total_closed_pnl:>15,.2f}")
else:
    print("\nNo closed positions today")

# ============================================================================
# 5. CURRENT OPEN POSITIONS
# ============================================================================
print("\n" + "="*90)
print("5. OPEN POSITIONS (Currently Held)")
print("-"*90)

cursor.execute("""
    SELECT symbol, quantity, avg_price, current_price, 
           invested_value, current_value, pnl, pnl_percent,
           updated_at
    FROM paper_positions
    ORDER BY pnl DESC
""")

open_positions = cursor.fetchall()

print(f"\nTotal Open: {len(open_positions)}")
print("-"*90)
print(f"{'Symbol':<12} {'Qty':>6} {'Entry':>10} {'Current':>10} {'Invested':>14} {'Current Val':>14} {'P&L':>14} {'%':<8} {'Updated'}")
print("-"*90)

total_open_invested = 0
total_open_current = 0
total_open_pnl = 0

for pos in open_positions:
    symbol, qty, entry, current, invested_val, current_val, pnl, pnl_pct, updated = pos
    age_minutes = (datetime.now() - updated.replace(tzinfo=None)).total_seconds() / 60
    freshness = "LIVE" if age_minutes < 2 else f"{int(age_minutes)}m"
    
    print(f"{symbol:<12} {qty:>6} ₹{entry:>9,.2f} ₹{current:>9,.2f} ₹{invested_val:>13,.2f} ₹{current_val:>13,.2f} ₹{pnl:>13,.2f} {pnl_pct:>6.2f}% {freshness}")
    
    total_open_invested += float(invested_val)
    total_open_current += float(current_val)
    total_open_pnl += float(pnl)

print("-"*90)
print(f"{'TOTAL OPEN:':<18} ₹{total_open_invested:>13,.2f} ₹{total_open_current:>13,.2f} ₹{total_open_pnl:>13,.2f}")

# ============================================================================
# 6. OPTIONS ANALYSIS
# ============================================================================
print("\n" + "="*90)
print("6. OPTIONS TRADING ANALYSIS")
print("-"*90)

# Options orders today
cursor.execute("""
    SELECT order_type, symbol, option_type, strike, quantity,
           order_premium, executed_premium, executed_at, status
    FROM paper_options_orders
    WHERE DATE(executed_at) = '2026-03-13'
    ORDER BY executed_at
""")

options_orders = cursor.fetchall()

print(f"\nOptions Orders Today: {len(options_orders)}")
if options_orders:
    print("-"*90)
    print(f"{'Time':<10} {'Action':<6} {'Option':<25} {'Qty':<6} {'Premium':<12} {'Amount':<16} {'Status'}")
    print("-"*90)
    
    for order in options_orders:
        ord_type, symbol, opt_type, strike, qty, order_prem, exec_prem, executed, status = order
        time_str = executed.strftime('%I:%M %p')
        opt_name = f"{symbol} {opt_type} {strike:.0f}"
        lot_size = 50 if symbol == 'NIFTY' else 25
        amount = qty * float(exec_prem) * lot_size
        print(f"{time_str:<10} {ord_type:<6} {opt_name:<25} {qty:<6} ₹{exec_prem:>10,.2f} ₹{amount:>14,.2f} {status}")

# Current options positions
cursor.execute("""
    SELECT symbol, option_type, strike, quantity,
           entry_premium, current_premium, 
           invested_value, current_value, pnl, pnl_percent
    FROM paper_options_positions
""")

options_positions = cursor.fetchall()

print(f"\n\nCurrent Open Options: {len(options_positions)}")
if options_positions:
    print("-"*90)
    print(f"{'Option':<25} {'Qty':<8} {'Entry':<12} {'Current':<12} {'Invested':<14} {'Current Val':<14} {'P&L'}")
    print("-"*90)
    
    for opt in options_positions:
        symbol, opt_type, strike, qty, entry_prem, current_prem, invested, current_val, pnl, pnl_pct = opt
        opt_name = f"{symbol} {opt_type} {strike:.0f}"
        print(f"{opt_name:<25} {qty} lots  ₹{entry_prem:>10,.2f} ₹{current_prem:>10,.2f} ₹{invested:>12,.2f} ₹{current_val:>12,.2f} ₹{pnl:>12,.2f} ({pnl_pct:+.2f}%)")

# ============================================================================
# 7. DAILY SUMMARY AND VERIFICATION
# ============================================================================
print("\n" + "="*90)
print("7. DAILY SUMMARY & VERIFICATION")
print("-"*90)

print(f"\n{'Metric':<35} {'Amount':>20} {'Notes'}")
print("-"*90)

# Cash flows
cash_inflow = total_sold
cash_outflow = total_bought_today
net_cash_flow = cash_inflow - cash_outflow

print(f"{'Total Cash Outflow (Bought):':<35} ₹{cash_outflow:>19,.2f}")
print(f"{'Total Cash Inflow (Sold):':<35} ₹{cash_inflow:>19,.2f}")
print(f"{'Net Cash Flow:':<35} ₹{net_cash_flow:>19,.2f} {'(+Used from capital)' if net_cash_flow < 0 else '(+Added to capital)'}")

# Realized vs Unrealized
realized_pnl = sum(p['pnl'] for p in closed_positions) if closed_positions else 0
unrealized_pnl = total_open_pnl

print(f"\n{'Realized P&L (Closed Trades):':<35} ₹{realized_pnl:>19,.2f} {'✅ Booked' if realized_pnl != 0 else ''}")
print(f"{'Unrealized P&L (Open Positions):':<35} ₹{unrealized_pnl:>19,.2f} {'Mark-to-market'}")
print(f"{'Total P&L (Today):':<35} ₹{(realized_pnl + unrealized_pnl):>19,.2f}")

# Capital verification
expected_cash = float(starting_capital) - portfolio_invested
cash_difference = portfolio_cash - expected_cash

print(f"\n{'Expected Available Cash:':<35} ₹{expected_cash:>19,.2f}")
print(f"{'Actual Available Cash:':<35} ₹{portfolio_cash:>19,.2f}")
print(f"{'Difference:':<35} ₹{cash_difference:>19,.2f} {'✅ Match!' if abs(cash_difference) < 1 else '❌ MISMATCH!'}")

# ============================================================================
# 8. TRANSACTION RECONCILIATION
# ============================================================================
print("\n" + "="*90)
print("8. TRANSACTION RECONCILIATION")
print("-"*90)

# Count orders
cursor.execute("""
    SELECT order_type, COUNT(*), SUM(quantity * executed_price)
    FROM paper_orders
    WHERE DATE(executed_at) = '2026-03-13'
    GROUP BY order_type
""")

order_summary = cursor.fetchall()

print(f"\n{'Order Type':<15} {'Count':>8} {'Total Value':>20}")
print("-"*90)
for ord_type, count, total_val in order_summary:
    print(f"{ord_type:<15} {count:>8} ₹{float(total_val):>19,.2f}")

# ============================================================================
# 9. POSITION-ORDER MATCHING VERIFICATION
# ============================================================================
print("\n" + "="*90)
print("9. POSITION-ORDER MATCHING")
print("-"*90)

# Check each open position has corresponding buy orders
print(f"\nVerifying {len(open_positions)} open positions...")
mismatches = []

for pos in open_positions:
    symbol = pos[0]
    pos_qty = pos[1]
    pos_avg = float(pos[2])
    
    # Get all BUY orders for this symbol
    cursor.execute("""
        SELECT SUM(quantity), 
               SUM(quantity * executed_price) / NULLIF(SUM(quantity), 0) as avg_price
        FROM paper_orders
        WHERE symbol = %s 
        AND order_type = 'BUY'
        AND status = 'EXECUTED'
    """, (symbol,))
    
    buy_total = cursor.fetchone()
    
    # Get all SELL orders for this symbol
    cursor.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM paper_orders
        WHERE symbol = %s
        AND order_type = 'SELL'
        AND status = 'EXECUTED'
    """, (symbol,))
    
    sell_total = cursor.fetchone()[0] or 0
    
    # Verify quantity
    total_bought = buy_total[0] or 0
    expected_qty = total_bought - sell_total
    avg_buy_price = float(buy_total[1]) if buy_total[1] else 0
    
    if expected_qty != pos_qty:
        mismatches.append({
            'symbol': symbol,
            'expected_qty': expected_qty,
            'actual_qty': pos_qty,
            'difference': expected_qty - pos_qty
        })
        print(f"  ❌ {symbol}: Expected qty={expected_qty}, Actual={pos_qty}, Diff={expected_qty - pos_qty}")
    elif abs(avg_buy_price - pos_avg) > 0.01:
        print(f"  ⚠️  {symbol}: Avg price mismatch - Calculated=₹{avg_buy_price:.2f}, Stored=₹{pos_avg:.2f}")
    else:
        print(f"  ✅ {symbol}: Qty={pos_qty}, Avg=₹{pos_avg:.2f} - Match!")

if not mismatches:
    print("\n✅ ALL POSITIONS MATCH ORDERS PERFECTLY!")
else:
    print(f"\n❌ FOUND {len(mismatches)} MISMATCHES - NEEDS INVESTIGATION!")

# ============================================================================
# 10. OPTIONS TRADING RECONCILIATION
# ============================================================================
print("\n" + "="*90)
print("10. OPTIONS POSITION VERIFICATION")
print("-"*90)

if options_positions:
    for opt in options_positions:
        symbol, opt_type, strike, qty, entry_prem, current_prem, invested, current_val, pnl, pnl_pct = opt
        
        # Get orders for this specific option
        cursor.execute("""
            SELECT order_type, quantity, executed_premium, executed_at
            FROM paper_options_orders
            WHERE symbol = %s 
            AND option_type = %s
            AND strike = %s
            ORDER BY executed_at
        """, (symbol, opt_type, strike))
        
        opt_orders = cursor.fetchall()
        
        print(f"\n{symbol} {opt_type} {strike:.0f}:")
        print(f"  Current Position: {qty} lots @ ₹{entry_prem:.2f}")
        print(f"  Order History ({len(opt_orders)} orders):")
        
        lots_bought = 0
        lots_sold = 0
        for ord_type, ord_qty, prem, exec_time in opt_orders:
            print(f"    {exec_time.strftime('%I:%M %p')}: {ord_type} {ord_qty} lot @ ₹{prem:.2f}")
            if ord_type == 'BUY':
                lots_bought += ord_qty
            else:
                lots_sold += ord_qty
        
        expected_qty = lots_bought - lots_sold
        lot_size = 50 if symbol == 'NIFTY' else 25
        
        # Verify calculation
        expected_invested = expected_qty * float(entry_prem) * lot_size
        expected_current = expected_qty * float(current_prem) * lot_size
        expected_pnl = expected_current - expected_invested
        
        print(f"\n  Verification:")
        print(f"    Lots Bought: {lots_bought}, Lots Sold: {lots_sold}")
        print(f"    Expected Qty: {expected_qty} lots, Actual: {qty} lots {'✅' if expected_qty == qty else '❌'}")
        print(f"    Lot Size: {lot_size} contracts")
        print(f"    Expected Invested: ₹{expected_invested:,.2f}, Actual: ₹{invested:,.2f} {'✅' if abs(expected_invested - float(invested)) < 1 else '❌'}")
        print(f"    Expected Current: ₹{expected_current:,.2f}, Actual: ₹{current_val:,.2f} {'✅' if abs(expected_current - float(current_val)) < 1 else '❌'}")
        print(f"    Expected P&L: ₹{expected_pnl:,.2f}, Actual: ₹{pnl:,.2f} {'✅' if abs(expected_pnl - float(pnl)) < 1 else '❌'}")
else:
    print("\nNo open options positions")

# ============================================================================
# 11. FINAL SUMMARY
# ============================================================================
print("\n" + "="*90)
print("11. FINAL TRADING SUMMARY - MARCH 13, 2026")
print("="*90)

print(f"\n{'Starting Capital:':<35} ₹{starting_capital:>19,.2f}")
print(f"{'Total Bought Today:':<35} ₹{total_bought_today:>19,.2f}")
print(f"{'Total Sold Today:':<35} ₹{total_sold:>19,.2f}")
print(f"{'Net Cash Used:':<35} ₹{(total_bought_today - total_sold):>19,.2f}")
print(f"\n{'Currently Invested:':<35} ₹{portfolio_invested:>19,.2f}")
print(f"{'Cash Available:':<35} ₹{portfolio_cash:>19,.2f}")
print(f"{'Account Value:':<35} ₹{(portfolio_invested + portfolio_cash):>19,.2f}")

print(f"\n{'Realized P&L (Closed):':<35} ₹{realized_pnl:>19,.2f}")
print(f"{'Unrealized P&L (Open):':<35} ₹{unrealized_pnl:>19,.2f}")
print(f"{'Total P&L Today:':<35} ₹{(realized_pnl + unrealized_pnl):>19,.2f}")

# Risk metrics
print(f"\n{'Capital Deployed %:':<35} {(portfolio_invested/starting_capital*100):>19.2f}%")
print(f"{'Cash Reserve %:':<35} {(portfolio_cash/starting_capital*100):>19.2f}%")

# Data quality check
cursor.execute("""
    SELECT 
        COUNT(CASE WHEN current_price IS NULL THEN 1 END) as null_prices,
        COUNT(*) as total_positions
    FROM paper_positions
""")
data_quality = cursor.fetchone()

print(f"\n{'Data Quality:':<35}")
print(f"  Positions with NULL prices:     {data_quality[0]} of {data_quality[1]}")
print(f"  Status: {'✅ All prices populated' if data_quality[0] == 0 else '❌ Missing price data'}")

cursor.close()
conn.close()

print("\n" + "="*90)
print(" " * 30 + "END OF ANALYSIS")
print("="*90)
