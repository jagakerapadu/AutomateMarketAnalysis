"""
Update Paper Trading Prices using Yahoo Finance
Quick alternative when Zerodha API is not available
"""
import psycopg2
import yfinance as yf
from datetime import datetime
from config.settings import get_settings

def update_stock_prices():
    """Update stock positions with Yahoo Finance prices"""
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
    print("UPDATING STOCK PRICES FROM YAHOO FINANCE")
    print("="*80)
    
    # Get all open positions
    cursor.execute("""
        SELECT id, symbol, quantity, avg_price, invested_value
        FROM paper_positions
        WHERE quantity > 0
        ORDER BY symbol
    """)
    positions = cursor.fetchall()
    
    if not positions:
        print("No open positions to update")
        return
    
    print(f"\nFound {len(positions)} positions to update\n")
    
    total_pnl = 0
    total_invested = 0
    updated_count = 0
    
    for pos_id, symbol, quantity, entry_price, invested_value in positions:
        try:
            # Fetch from Yahoo Finance (NSE symbols need .NS suffix)
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period="1d")
            
            if data.empty:
                print(f"⚠️  {symbol:12s} - No data from Yahoo Finance")
                continue
            
            current_price = float(data['Close'].iloc[-1])
            current_value = current_price * quantity
            invested_value = float(invested_value)  # Convert Decimal to float
            pnl = current_value - invested_value
            pnl_percent = (pnl / invested_value) * 100
            
            # Update position
            cursor.execute("""
                UPDATE paper_positions
                SET current_price = %s,
                    current_value = %s,
                    pnl = %s,
                    pnl_percent = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (current_price, current_value, pnl, pnl_percent, pos_id))
            
            total_pnl += pnl
            total_invested += invested_value
            updated_count += 1
            
            # Print status
            status = "📉" if pnl < 0 else "📈"
            print(f"{status} {symbol:12s} ₹{entry_price:8.2f} → ₹{current_price:8.2f} = ₹{pnl:10.2f} ({pnl_percent:+.2f}%)")
            
        except Exception as e:
            print(f"❌ {symbol:12s} - Error: {str(e)[:50]}")
    
    conn.commit()
    
    # Update portfolio summary
    cursor.execute("SELECT total_capital FROM paper_portfolio WHERE id = 1")
    total_capital = float(cursor.fetchone()[0])
    available_cash = total_capital - total_invested
    
    cursor.execute("""
        UPDATE paper_portfolio
        SET total_pnl = %s,
            invested_amount = %s,
            available_cash = %s,
            today_pnl = %s,
            updated_at = NOW()
        WHERE id = 1
    """, (total_pnl, total_invested, available_cash, total_pnl))
    
    conn.commit()
    
    print("\n" + "-"*80)
    print(f"✅ Updated {updated_count}/{len(positions)} positions")
    print(f"   Total P&L:      ₹{total_pnl:,.2f}")
    print(f"   Total Invested: ₹{total_invested:,.2f}")
    print(f"   Available Cash: ₹{available_cash:,.2f}")
    print("="*80 + "\n")
    
    cursor.close()
    conn.close()

def update_nifty_spot_price():
    """Update NIFTY spot price in market_ohlc"""
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
    print("UPDATING NIFTY SPOT PRICE")
    print("="*80)
    
    try:
        # Fetch NIFTY 50 index from Yahoo Finance
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="1d")
        
        if not data.empty:
            current_price = float(data['Close'].iloc[-1])
            open_price = float(data['Open'].iloc[-1])
            high_price = float(data['High'].iloc[-1])
            low_price = float(data['Low'].iloc[-1])
            volume = int(data['Volume'].iloc[-1])
            
            # Insert into market_ohlc (upsert)
            cursor.execute("""
                INSERT INTO market_ohlc (symbol, timestamp, open, high, low, close, volume, timeframe)
                VALUES ('NIFTY50', NOW(), %s, %s, %s, %s, %s, '1d')
                ON CONFLICT (symbol, timestamp, timeframe) 
                DO UPDATE SET 
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """, (open_price, high_price, low_price, current_price, volume))
            
            conn.commit()
            
            change = current_price - open_price
            change_percent = (change / open_price) * 100
            status = "📈" if change >= 0 else "📉"
            
            print(f"\n{status} NIFTY 50 Index:")
            print(f"   Current:  ₹{current_price:,.2f}")
            print(f"   Open:     ₹{open_price:,.2f}")
            print(f"   High:     ₹{high_price:,.2f}")
            print(f"   Low:      ₹{low_price:,.2f}")
            print(f"   Change:   ₹{change:+,.2f} ({change_percent:+.2f}%)")
            print("\n✅ NIFTY spot price updated in market_ohlc table")
        else:
            print("⚠️  No NIFTY data from Yahoo Finance")
    
    except Exception as e:
        print(f"❌ Error updating NIFTY price: {e}")
    
    print("="*80 + "\n")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    update_stock_prices()
    update_nifty_spot_price()
    
    print("\n💡 TIP: Restart API server and refresh dashboard to see updated prices")
