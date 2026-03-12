"""
Generate Options Trading Signals (Manual Scan)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.strategy.options_signal_generator import OptionsSignalGenerator
from services.indicators.options_indicators import OptionsIndicators


def main():
    print("\n" + "=" * 70)
    print("OPTIONS TRADING SIGNALS GENERATOR")
    print("=" * 70)
    
    # 1. Calculate options indicators
    print("\n📊 Calculating options market indicators...")
    options_calc = OptionsIndicators()
    indicators = options_calc.calculate_all_indicators("NIFTY")
    
    if indicators:
        print(f"\n✅ Market Indicators:")
        print(f"  Nifty Spot: ₹{indicators.get('nifty_spot', 0):,.2f}")
        print(f"  PCR (OI): {indicators.get('pcr_oi', 0):.4f}")
        print(f"  IV Rank: {indicators.get('iv_rank', 0):.2f}%")
        print(f"  Max Pain: ₹{indicators.get('max_pain_nifty', 0):,.2f}")
        print(f"  Call Resistance: ₹{indicators.get('call_resistance', 0):,.2f}")
        print(f"  Put Support: ₹{indicators.get('put_support', 0):,.2f}")
        
        options_calc.save_indicators(indicators)
    
    # 2. Generate signals
    print("\n🔍 Scanning all options strategies...")
    signal_gen = OptionsSignalGenerator()
    signals = signal_gen.scan_and_save("NIFTY")
    
    if signals:
        print(f"\n✅ Generated {len(signals)} trading signals:\n")
        
        for i, signal in enumerate(signals, 1):
            print(f"{i}. {signal['strategy']}")
            print(f"   Action: {signal['signal_type']} {signal['option_type']} @ Strike {signal['strike']}")
            print(f"   Entry Premium: ₹{signal['entry_premium']:.2f}")
            print(f"   Target: ₹{signal['target_premium']:.2f} (+{((signal['target_premium']/signal['entry_premium']-1)*100):.1f}%)")
            print(f"   Stop Loss: ₹{signal['stop_loss_premium']:.2f} ({((signal['stop_loss_premium']/signal['entry_premium']-1)*100):.1f}%)")
            print(f"   Confidence: {signal['confidence']:.1f}%")
            print(f"   Risk:Reward: 1:{signal['risk_reward_ratio']}")
            print(f"   Reason: {signal['reason']}")
            print()
        
        print(f"💡 Signals saved to database")
        print(f"   Run 'py start_options_trading.py' to auto-execute")
    else:
        print("\n⚠️  No signals generated")
        print("   Possible reasons:")
        print("   • Market conditions not favorable")
        print("   • No clear setup found")
        print("   • All signals below 70% confidence threshold")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
