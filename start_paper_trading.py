"""
Start Paper Trading Engine - Run virtual trading with live market data
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Clear cached Zerodha environment variables to force token refresh
for key in list(os.environ.keys()):
    if key.startswith('ZERODHA_'):
        del os.environ[key]

from services.paper_trading.paper_trading_engine import PaperTradingEngine
from config.logger import setup_logger

logger = setup_logger("start_paper_trading")


def main():
    """Start paper trading engine"""
    print("=" * 60)
    print("🚀 Starting Paper Trading Engine")
    print("=" * 60)
    print()
    print("Features:")
    print("  ✅ Virtual portfolio with ₹10,00,000 capital")
    print("  ✅ Live market data from Zerodha")
    print("  ✅ Auto-execution of trading signals")
    print("  ✅ Real-time position tracking")
    print("  ✅ Automatic stop-loss and target management")
    print()
    print("Settings:")
    print("  • Update interval: 60 seconds")
    print("  • Risk per trade: 20% max")
    print("  • Target: +3% | Stop Loss: -2%")
    print("  • Market hours: 9:15 AM - 3:30 PM IST")
    print()
    print("=" * 60)
    print()
    
    try:
        # Create and start engine
        engine = PaperTradingEngine(auto_execute=True)
        
        print("✅ Engine initialized successfully")
        print("⏰ Starting trading loop...")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        # Start the engine (runs indefinitely)
        engine.start(interval=60)
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("🛑 Stopping paper trading engine...")
        print("=" * 60)
    except Exception as e:
        logger.error(f"Error starting engine: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
