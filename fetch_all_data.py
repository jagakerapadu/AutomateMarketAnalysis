"""
Complete Data Pipeline - Fetch from all sources and populate database
This script fetches data from Zerodha, NSE, and Yahoo Finance and stores it in the database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
get_settings.cache_clear()

import asyncio
from datetime import datetime, timedelta
import pandas as pd
from config.logger import setup_logger
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from services.market_data.adapters.yfinance_adapter import YFinanceAdapter
from services.market_data.adapters.nse_adapter import NSEAdapter
from services.market_data.storage.data_writer import DataWriter

logger = setup_logger("data_pipeline")

# Top liquid NSE stocks
WATCHLIST = [
    "INFY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK",
    "KOTAKBANK", "SBIN", "BHARTIARTL", "BAJFINANCE", "ITC",
    "HINDUNILVR", "ASIANPAINT", "HCLTECH", "AXISBANK", "LT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND"
]

INDICES = ["NIFTY 50", "NIFTY BANK"]
GLOBAL_INDICES = ["^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225"]

async def fetch_from_zerodha(symbols, days=30):
    """Fetch historical data from Zerodha Kite"""
    print("\n" + "="*70)
    print("  FETCHING FROM ZERODHA KITE")
    print("="*70)
    
    zerodha = ZerodhaAdapter()
    writer = DataWriter()
    
    print(f"\n⏳ Fetching {days} days of historical data for {len(symbols)} symbols...")
    
    all_data = []
    success_count = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"  [{i}/{len(symbols)}] Fetching {symbol}...", end=" ")
            df = await asyncio.to_thread(
                zerodha.get_historical_data,
                symbol,
                "day",
                days=days
            )
            
            if df is not None and not df.empty:
                all_data.append(df)
                success_count += 1
                print(f"✅ {len(df)} records")
            else:
                print("⚠️  No data")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"\n⏳ Storing {len(combined_df)} OHLC records to database...")
        writer.write_ohlc(combined_df)
        print(f"✅ Stored {len(combined_df)} records from {success_count} symbols")
    else:
        print("⚠️  No data to store")
    
    return success_count

async def fetch_global_indices():
    """Fetch global market indices from Yahoo Finance"""
    print("\n" + "="*70)
    print("  FETCHING GLOBAL INDICES (YAHOO FINANCE)")
    print("="*70)
    
    yfinance = YFinanceAdapter()
    writer = DataWriter()
    
    print(f"\n⏳ Fetching global indices: {', '.join(GLOBAL_INDICES)}")
    
    try:
        df = await asyncio.to_thread(
            yfinance.get_global_indices,
            GLOBAL_INDICES
        )
        
        if df is not None and not df.empty:
            print(f"✅ Fetched {len(df)} records")
            writer.write_global_indices(df)
            print("✅ Stored global indices data")
            
            # Show summary
            print("\nGlobal Market Summary:")
            for _, row in df.iterrows():
                print(f"  {row['symbol']}: {row['close']:.2f} ({row['change_percent']:+.2f}%)")
            return True
        else:
            print("⚠️  No global data fetched")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def fetch_nse_data():
    """Fetch NSE market sentiment and options data"""
    print("\n" + "="*70)
    print("  FETCHING NSE DATA (OPTIONS & SENTIMENT)")
    print("="*70)
    
    nse = NSEAdapter()
    writer = DataWriter()
    
    # Fetch market sentiment
    print("\n⏳ Fetching market sentiment (VIX, PCR, FII/DII)...")
    try:
        sentiment = await asyncio.to_thread(nse.get_market_sentiment)
        if sentiment:
            writer.write_market_sentiment(sentiment)
            print(f"✅ Stored market sentiment")
            print(f"  VIX: {sentiment.get('vix', 'N/A')}")
            print(f"  PCR: {sentiment.get('put_call_ratio', 'N/A')}")
    except Exception as e:
        print(f"⚠️  Sentiment fetch failed: {str(e)[:50]}")
    
    # Fetch options chain for NIFTY and BANKNIFTY
    print("\n⏳ Fetching options chain for NIFTY and BANKNIFTY...")
    for index in ["NIFTY", "BANKNIFTY"]:
        try:
            print(f"  Fetching {index} options...", end=" ")
            df = await asyncio.to_thread(nse.get_options_chain, index)
            
            if df is not None and not df.empty:
                writer.write_options_chain(df)
                print(f"✅ {len(df)} option strikes")
            else:
                print("⚠️  No data")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")

async def calculate_indicators():
    """Calculate technical indicators for all OHLC data"""
    print("\n" + "="*70)
    print("  CALCULATING TECHNICAL INDICATORS")
    print("="*70)
    
    from services.indicators.indicator_engine import IndicatorEngine
    
    engine = IndicatorEngine()
    
    print("\n⏳ Calculating indicators for all symbols in database...")
    try:
        await asyncio.to_thread(engine.calculate_all_indicators)
        print("✅ Indicators calculated and stored")
    except Exception as e:
        print(f"❌ Error calculating indicators: {e}")

async def generate_signals():
    """Generate trading signals from strategies"""
    print("\n" + "="*70)
    print("  GENERATING TRADING SIGNALS")
    print("="*70)
    
    from services.strategy.strategy_engine import StrategyEngine
    
    engine = StrategyEngine()
    
    print("\n⏳ Running strategies to generate signals...")
    try:
        signals = await asyncio.to_thread(engine.generate_all_signals)
        
        if signals:
            print(f"✅ Generated {len(signals)} signals")
            
            # Show top signals
            print("\nTop Signals:")
            for i, signal in enumerate(signals[:5], 1):
                print(f"  {i}. {signal['symbol']} - {signal['signal_type']} "
                      f"(Confidence: {signal['confidence']}%)")
        else:
            print("⚠️  No signals generated (might need more data)")
            
    except Exception as e:
        print(f"❌ Error generating signals: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main data pipeline"""
    print("="*70)
    print("  TRADING SYSTEM - COMPLETE DATA PIPELINE")
    print("="*70)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = datetime.now()
    
    # Step 1: Fetch global markets
    await fetch_global_indices()
    
    # Step 2: Fetch Zerodha data
    await fetch_from_zerodha(WATCHLIST, days=90)
    
    # Step 3: Fetch NSE data
    await fetch_nse_data()
    
    # Step 4: Calculate indicators
    await calculate_indicators()
    
    # Step 5: Generate signals
    await generate_signals()
    
    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("  PIPELINE COMPLETE")
    print("="*70)
    print(f"\nTotal time: {duration:.1f} seconds")
    print("\nData fetched from:")
    print("  ✅ Zerodha Kite - Historical OHLC for Indian stocks")
    print("  ✅ Yahoo Finance - Global market indices")
    print("  ✅ NSE India - Options chain and market sentiment")
    print("\nDatabase populated with:")
    print("  • OHLC price data (market_ohlc table)")
    print("  • Global indices (global_indices table)")
    print("  • Technical indicators (indicators table)")
    print("  • Options chain (options_chain table)")
    print("  • Market sentiment (market_sentiment table)")
    print("  • Trading signals (signals table)")
    
    print("\n🎯 Next Steps:")
    print("  1. Refresh dashboard: http://localhost:3000")
    print("  2. View signals: http://localhost:8000/api/signals/latest")
    print("  3. Check API docs: http://localhost:8000/api/docs")
    
    print("\n💡 Run this script daily to keep data updated!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
