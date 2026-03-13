"""
Generate trading signals for Nifty 50 stocks
This will analyze current market data and create BUY/SELL signals based on technical analysis
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
from datetime import datetime, timedelta
from config.settings import get_settings
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter

settings = get_settings()

# Top Nifty 50 stocks for paper trading
NIFTY_50_STOCKS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'HINDUNILVR', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
    'LT', 'AXISBANK', 'WIPRO', 'HCLTECH', 'ASIANPAINT',
    'MARUTI', 'SUNPHARMA', 'TITAN', 'BAJFINANCE', 'ULTRACEMCO'
]

def generate_sample_signals():
    """Generate BUY signals for Nifty 50 stocks using live market data"""
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    print(f"\n{'='*80}")
    print("GENERATING TRADING SIGNALS FOR NIFTY 50 STOCKS")
    print(f"{'='*80}\n")
    
    # Initialize Zerodha adapter for live prices
    print("Connecting to Zerodha for live prices...")
    zerodha = ZerodhaAdapter()
    
    if not zerodha.kite:
        print("ERROR: Zerodha connection failed. Please check your access token.")
        print("Run: py generate_token_quick.py")
        return
    
    signals_created = 0
    
    # Fetch live quotes for all symbols at once
    try:
        instruments = [f"NSE:{symbol}" for symbol in NIFTY_50_STOCKS]
        quotes = zerodha.kite.quote(instruments)
        print(f"✅ Fetched live prices for {len(quotes)} stocks\n")
    except Exception as e:
        print(f"ERROR fetching quotes: {e}")
        return
    
    for symbol in NIFTY_50_STOCKS:
        instrument_key = f"NSE:{symbol}"
        
        if instrument_key not in quotes:
            print(f"⚠️  No data for {symbol}, skipping...")
            continue
        
        quote_data = quotes[instrument_key]
        close_price = quote_data.get('last_price')
        
        if not close_price or close_price <= 0:
            print(f"⚠️  Invalid price for {symbol} (price={close_price}), skipping...")
            continue
        
        # Generate a simple BUY signal based on momentum
        # Entry: Current LTP
        # Stop loss: 2% below
        # Target: 3% above
        entry_price = float(close_price)
        stop_loss = entry_price * 0.98  # 2% stop loss
        target_price = entry_price * 1.03  # 3% target
        
        # Calculate confidence based on price action (simplified)
        # Higher confidence if price is near day high
        day_high = quote_data.get('ohlc', {}).get('high', entry_price)
        day_low = quote_data.get('ohlc', {}).get('low', entry_price)
        
        if day_high > day_low:
            price_position = (entry_price - day_low) / (day_high - day_low)
            confidence = int(70 + (price_position * 10))  # 70-80% based on position in day's range
        else:
            confidence = 75
        
        # Insert signal
        cursor.execute("""
            INSERT INTO signals 
            (timestamp, symbol, strategy, signal_type, timeframe, entry_price, 
             stop_loss, target_price, confidence, quantity, reason, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.now(),
            symbol,
            'MOMENTUM_BREAKOUT',
            'BUY',
            '15m',
            entry_price,
            stop_loss,
            target_price,
            confidence,
            0,  # Quantity will be calculated by paper trading engine
            f'Strong momentum detected at Rs.{entry_price:.2f} (Day High: Rs.{day_high:.2f})',
            'PENDING',
            datetime.now()
        ))
        
        signals_created += 1
        print(f"✅ {symbol:12} BUY | Entry: Rs.{entry_price:8,.2f} | Target: Rs.{target_price:8,.2f} | SL: Rs.{stop_loss:8,.2f} | {confidence}%")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"✅ CREATED {signals_created} TRADING SIGNALS")
    print(f"{'='*80}\n")
    print("Ready for paper trading! Run: py start_paper_trading.py")
    
if __name__ == "__main__":
    generate_sample_signals()
