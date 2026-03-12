"""
Paper Trading Daemon - Runs only during market hours
Smart version that sleeps at night and auto-wakes at market open
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
from datetime import datetime, time as dt_time
from services.paper_trading.paper_trading_engine import PaperTradingEngine
from config.logger import setup_logger

logger = setup_logger("paper_trading_daemon")


def seconds_until_market_open():
    """Calculate seconds until market opens"""
    now = datetime.now()
    
    # Market opens at 9:15 AM
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    
    # If already past 9:15 today, target tomorrow
    if now >= market_open:
        from datetime import timedelta
        market_open += timedelta(days=1)
    
    # Skip weekends
    while market_open.weekday() >= 5:  # Saturday=5, Sunday=6
        from datetime import timedelta
        market_open += timedelta(days=1)
    
    delta = market_open - now
    return int(delta.total_seconds())


def main():
    """Smart daemon that runs only during market hours"""
    print("=" * 60)
    print("🤖 Paper Trading Daemon (Smart Mode)")
    print("=" * 60)
    print()
    print("This version:")
    print("  ✅ Only runs during market hours (9:15 AM - 3:30 PM)")
    print("  ✅ Auto-sleeps at night")
    print("  ✅ Auto-wakes when market opens")
    print("  ✅ Skips weekends automatically")
    print()
    print("=" * 60)
    print()
    
    while True:
        now = datetime.now()
        
        # Check if weekend
        if now.weekday() >= 5:
            seconds = seconds_until_market_open()
            hours = seconds // 3600
            print(f"📅 Weekend detected! Sleeping until Monday...")
            print(f"   Next market open: {hours} hours from now")
            print()
            time.sleep(3600)  # Check every hour
            continue
        
        # Check if market hours
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        current_time = now.time()
        
        if current_time < market_open:
            # Before market open
            seconds = seconds_until_market_open()
            minutes = seconds // 60
            print(f"🌅 Pre-market: Sleeping until 9:15 AM...")
            print(f"   Market opens in: {minutes} minutes")
            print()
            time.sleep(min(seconds, 300))  # Check every 5 min max
            continue
        
        elif current_time > market_close:
            # After market close
            seconds = seconds_until_market_open()
            hours = seconds // 3600
            print(f"🌙 Post-market: Sleeping until tomorrow 9:15 AM...")
            print(f"   Next market open: {hours} hours from now")
            print()
            time.sleep(3600)  # Check every hour
            continue
        
        else:
            # Market is open - run trading engine
            print("=" * 60)
            print(f"📈 Market OPEN - Starting trading engine")
            print(f"   Time: {now.strftime('%I:%M %p')}")
            print("=" * 60)
            print()
            
            try:
                engine = PaperTradingEngine(auto_execute=True)
                
                # Run until market close
                engine.running = True
                
                while engine.running and engine.is_market_open():
                    engine.run_cycle()
                    time.sleep(60)  # Update every 60 seconds
                
                print()
                print("=" * 60)
                print(f"🔔 Market CLOSED - Stopping engine")
                print(f"   Time: {datetime.now().strftime('%I:%M %p')}")
                print("=" * 60)
                print()
                
            except KeyboardInterrupt:
                print("\n🛑 Daemon stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in trading engine: {e}")
                print(f"❌ Error: {e}")
                print("Waiting 5 minutes before retry...")
                time.sleep(300)


if __name__ == '__main__':
    main()
