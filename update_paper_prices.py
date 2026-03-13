"""
Update Paper Trading Position Prices
Updates all open positions with current live prices from Zerodha
"""

import psycopg2
from datetime import datetime, timezone
from config.settings import get_settings
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter

def update_position_prices():
    """Update all paper trading positions with live prices"""
    settings = get_settings()
    
    # Connect to database
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    cursor = conn.cursor()
    
    try:
        # Get all symbols from open positions
        cursor.execute("""
            SELECT DISTINCT symbol 
            FROM paper_positions 
            WHERE quantity > 0
        """)
        symbols = [row[0] for row in cursor.fetchall()]
        
        if not symbols:
            print("No open positions to update")
            return
        
        print(f"Updating prices for {len(symbols)} symbols...")
        
        # Get live prices from Zerodha
        zerodha = ZerodhaAdapter()
        instruments = [f"NSE:{symbol}" for symbol in symbols]
        
        try:
            quotes = zerodha.kite.quote(instruments)
        except Exception as e:
            print(f"Error fetching live prices: {e}")
            return
        
        # Update each position
        updated_count = 0
        for symbol in symbols:
            instrument_key = f"NSE:{symbol}"
            if instrument_key in quotes:
                quote = quotes[instrument_key]
                current_price = quote.get('last_price', quote.get('ohlc', {}).get('close'))
                
                if current_price:
                    cursor.execute("""
                        UPDATE paper_positions
                        SET current_price = %s,
                            current_value = quantity * %s,
                            pnl = (quantity * %s) - invested_value,
                            pnl_percent = ((quantity * %s - invested_value) / invested_value * 100),
                            updated_at = %s
                        WHERE symbol = %s AND quantity > 0
                    """, (current_price, current_price, current_price, current_price, 
                          datetime.now(timezone.utc), symbol))
                    
                    updated_count += 1
                    print(f"✓ {symbol}: Rs.{current_price:.2f}")
        
        conn.commit()
        print(f"\nSuccessfully updated {updated_count} positions")
        
        # Show updated positions
        cursor.execute("""
            SELECT symbol, quantity, avg_price, current_price, pnl, pnl_percent
            FROM paper_positions
            WHERE quantity > 0
            ORDER BY pnl_percent DESC
        """)
        
        print("\nUpdated Positions:")
        print("-" * 80)
        for row in cursor.fetchall():
            symbol, qty, avg, current, pnl, pnl_pct = row
            pnl_sign = "+" if pnl >= 0 else ""
            print(f"{symbol:12} | Qty: {qty:4} | Entry: Rs.{avg:8.2f} | Current: Rs.{current:8.2f} | P&L: {pnl_sign}Rs.{pnl:8.2f} ({pnl_sign}{pnl_pct:.2f}%)")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Updating paper trading position prices...")
    print("=" * 80)
    update_position_prices()
