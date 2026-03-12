"""
Options Data Updater - Runs Periodically During Market Hours
Fetches live options chain every 5 minutes and updates database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import asyncio
from datetime import datetime, time as dt_time
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from services.market_data.storage.data_writer import DataWriter
from config.logger import setup_logger

logger = setup_logger("options_updater")

# Market hours (IST)
MARKET_OPEN = dt_time(9, 15)  # 9:15 AM
MARKET_CLOSE = dt_time(15, 30)  # 3:30 PM
UPDATE_INTERVAL = 300  # 5 minutes in seconds


def is_market_hours():
    """Check if current time is within market hours"""
    now = datetime.now().time()
    return MARKET_OPEN <= now <= MARKET_CLOSE


async def update_options_data():
    """Fetch and store latest options chain"""
    zerodha = ZerodhaAdapter()
    writer = DataWriter()
    
    if not zerodha.kite or not zerodha.access_token:
        logger.error("Zerodha not initialized or token expired!")
        print("[ERROR] Zerodha token expired! Run: py setup_credentials.py")
        return False
    
    indices = ["NIFTY", "BANKNIFTY"]
    success_count = 0
    
    for index in indices:
        try:
            df = await asyncio.to_thread(zerodha.get_options_chain, index)
            
            if not df.empty:
                writer.write_options_chain(df)
                logger.info(f"Updated {len(df)} options for {index}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Updated {index}: {len(df)} contracts")
                success_count += 1
            else:
                logger.warning(f"No data received for {index}")
                
        except Exception as e:
            logger.error(f"Error updating {index}: {e}")
    
    return success_count > 0


async def run_updater():
    """Main updater loop"""
    print("\n" + "=" * 70)
    print("OPTIONS DATA UPDATER - BACKGROUND SERVICE")
    print("=" * 70)
    print(f"Market Hours: {MARKET_OPEN.strftime('%H:%M')} - {MARKET_CLOSE.strftime('%H:%M')}")
    print(f"Update Interval: {UPDATE_INTERVAL // 60} minutes")
    print("=" * 70 + "\n")
    
    # Initial update
    print("Running initial options data fetch...")
    await update_options_data()
    
    print("\n[INFO] Updater is now running. Press Ctrl+C to stop.")
    print("[INFO] Updates will occur every 5 minutes during market hours.\n")
    
    try:
        while True:
            # Check if market is open
            if is_market_hours():
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"[{current_time}] Market is open - updating options data...")
                
                success = await update_options_data()
                if not success:
                    print("[WARN] Update failed - check Zerodha token")
                
                # Wait for next update
                await asyncio.sleep(UPDATE_INTERVAL)
            else:
                # Market closed - check every minute
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"[{current_time}] Market closed - waiting...")
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        print("\n[INFO] Updater stopped by user")
    except Exception as e:
        logger.error(f"Updater error: {e}")
        print(f"\n[ERROR] Updater stopped: {e}")


if __name__ == "__main__":
    print("\n[INFO] Starting Options Data Updater Service...")
    print("[INFO] This will run continuously and update options prices every 5 minutes.")
    print("[INFO] Keep this window open during trading hours.\n")
    
    try:
        asyncio.run(run_updater())
    except KeyboardInterrupt:
        print("\n[INFO] Service stopped")
