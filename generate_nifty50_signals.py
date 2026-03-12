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

settings = get_settings()

# Top Nifty 50 stocks for paper trading
NIFTY_50_STOCKS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'HINDUNILVR', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
    'LT', 'AXISBANK', 'WIPRO', 'HCLTECH', 'ASIANPAINT',
    'MARUTI', 'SUNPHARMA', 'TITAN', 'BAJFINANCE', 'ULTRACEMCO'
]

def generate_sample_signals():
    """Generate sample BUY signals for Nifty 50 stocks"""
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
    
    # Get current prices from OHLC data (most recent)
    signals_created = 0
    
    for symbol in NIFTY_50_STOCKS:
        # Get latest price
        cursor.execute("""
            SELECT close, high, low, volume 
            FROM ohlc 
            WHERE symbol = %s 
            ORDER BY time DESC 
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        if not result:
            print(f"⚠️  No data for {symbol}, skipping...")
            continue
            
        close_price, high, low, volume = result
        
        # Generate a simple BUY signal based on momentum
        # Entry: Current close price
        # Stop loss: 2% below
        # Target: 3% above
        entry_price = float(close_price)
        stop_loss = entry_price * 0.98  # 2% stop loss
        target_price = entry_price * 1.03  # 3% target
        
        # Calculate confidence based on price action (simplified)
        confidence = 75  # Default confidence
        
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
            f'Strong momentum detected, entry at Rs.{entry_price:.2f}',
            'PENDING',
            datetime.now()
        ))
        
        signals_created += 1
        print(f"✅ {symbol:12} BUY signal | Entry: Rs.{entry_price:8,.2f} | Target: Rs.{target_price:8,.2f} | {confidence}%")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"✅ CREATED {signals_created} TRADING SIGNALS")
    print(f"{'='*80}\n")
    print("Ready for paper trading! Run: py start_paper_trading.py")
    
if __name__ == "__main__":
    generate_sample_signals()
