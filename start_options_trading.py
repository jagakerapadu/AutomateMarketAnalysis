"""
Start Nifty 50 Options Paper Trading
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.paper_trading.options_trading_engine import OptionsTradingEngine
from services.strategy.options_signal_generator import OptionsSignalGenerator
from config.logger import setup_logger

logger = setup_logger("start_options_trading")


def main():
    print("\n" + "=" * 70)
    print("INDEX OPTIONS PAPER TRADING ENGINE")
    print("Nifty 50 & Bank Nifty Options")
    print("=" * 70)
    
    # 1. Generate initial signals
    print("\n[SCAN] Scanning for options trading signals...")
    signal_gen = OptionsSignalGenerator()
    signals = signal_gen.scan_and_save("NIFTY")
    
    if signals:
        print(f"\n[OK] Generated {len(signals)} signals:")
        for signal in signals:
            print(f"  - {signal['strategy']}: {signal['option_type']} {signal['strike']} @ Rs.{signal['entry_premium']:.2f} (Conf: {signal['confidence']:.1f}%)")
    else:
        print("\n[WARNING] No signals generated (market conditions may not be ideal)")
        print("   Engine will monitor for opportunities...")
    
    # 2. Start trading engine
    print("\n[START] Starting Options Trading Engine...")
    print("   - Auto-execution: Enabled")
    print("   - Check interval: 60 seconds")
    print("   - Target: +60% to +80%")
    print("   - Stop Loss: -40% to -50%")
    print("\n[WARNING] Press Ctrl+C to stop\n")
    
    engine = OptionsTradingEngine()
    engine.start(interval=60)


if __name__ == "__main__":
    main()
