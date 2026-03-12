"""
Automated Morning Routine for Options Trading
Runs at 9:00 AM daily (before market open)

Checklist:
- [ ] Check India VIX level
- [ ] Calculate PCR ratio  
- [ ] Identify max pain level
- [ ] Check option chain for OI buildup
- [ ] Generate fresh signals
- [ ] Review overnight positions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from datetime import datetime
from services.indicators.options_indicators import OptionsIndicators
from services.strategy.options_signal_generator import OptionsSignalGenerator
from services.paper_trading.options_virtual_portfolio import OptionsVirtualPortfolio
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from config.logger import setup_logger

logger = setup_logger("morning_routine")


async def morning_routine():
    """Complete morning analysis and signal generation"""
    
    print("\n" + "=" * 80)
    print("☀️  AUTOMATED MORNING ROUTINE - OPTIONS TRADING")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"Time: {datetime.now().strftime('%I:%M %p')}")
    print("=" * 80)
    
    # Step 1: Verify Zerodha token
    print("\n[1/7] 🔐 Verifying Zerodha Access Token...")
    zerodha = ZerodhaAdapter()
    if not zerodha.kite or not zerodha.access_token:
        print("     ❌ CRITICAL: Zerodha token expired or missing!")
        print("     Action required: Run 'py generate_token_quick.py'")
        return False
    
    try:
        profile = zerodha.kite.profile()
        print(f"     ✅ Token valid - User: {profile['user_name']}")
    except Exception as e:
        print(f"     ❌ Token validation failed: {e}")
        print("     Action required: Regenerate token")
        return False
    
    # Step 2: Fetch latest options data
    print("\n[2/7] 📊 Fetching Live Options Chain from Zerodha...")
    try:
        df_nifty = await asyncio.to_thread(zerodha.get_options_chain, "NIFTY")
        df_banknifty = await asyncio.to_thread(zerodha.get_options_chain, "BANKNIFTY")
        
        if df_nifty.empty and df_banknifty.empty:
            print("     ⚠️  No options data available (market might be closed)")
        else:
            from services.market_data.storage.data_writer import DataWriter
            writer = DataWriter()
            
            if not df_nifty.empty:
                writer.write_options_chain(df_nifty)
                print(f"     ✅ NIFTY: {len(df_nifty)} contracts updated")
            
            if not df_banknifty.empty:
                writer.write_options_chain(df_banknifty)
                print(f"     ✅ BANKNIFTY: {len(df_banknifty)} contracts updated")
    except Exception as e:
        logger.error(f"Error fetching options data: {e}")
        print(f"     ❌ Failed to fetch options data: {e}")
    
    # Step 3: Calculate India VIX
    print("\n[3/7] 📈 Checking India VIX Level...")
    try:
        # Fetch VIX from market data
        quotes = zerodha.kite.quote(["NSE:INDIA VIX"])
        if "NSE:INDIA VIX" in quotes:
            vix = quotes["NSE:INDIA VIX"]["last_price"]
            print(f"     India VIX: {vix:.2f}")
            
            # VIX interpretation
            if vix < 12:
                print(f"     📊 Low volatility - Market is calm")
            elif vix < 18:
                print(f"     📊 Moderate volatility - Normal conditions")
            elif vix < 25:
                print(f"     📊 Elevated volatility - Caution advised")
            else:
                print(f"     📊 High volatility - High risk/reward environment")
        else:
            print("     ⚠️  VIX data not available")
            vix = 0
    except Exception as e:
        logger.error(f"Error fetching VIX: {e}")
        print(f"     ⚠️  Could not fetch VIX: {e}")
        vix = 0
    
    # Step 4: Calculate PCR Ratio
    print("\n[4/7] 🎯 Calculating Put-Call Ratio (PCR)...")
    options_calc = OptionsIndicators()
    pcr_data = options_calc.calculate_pcr_ratio("NIFTY")
    
    if pcr_data and pcr_data['pcr_oi'] > 0:
        print(f"     PCR (OI): {pcr_data['pcr_oi']:.4f}")
        print(f"     PCR (Volume): {pcr_data['pcr_volume']:.4f}")
        print(f"     Total CE OI: {pcr_data['total_ce_oi']:,}")
        print(f"     Total PE OI: {pcr_data['total_pe_oi']:,}")
        
        # PCR interpretation
        if pcr_data['pcr_oi'] > 1.2:
            print(f"     📊 BULLISH: More puts than calls (strong bullish sentiment)")
        elif pcr_data['pcr_oi'] > 0.8:
            print(f"     📊 NEUTRAL: Balanced options activity")
        else:
            print(f"     📊 BEARISH: More calls than puts (bearish sentiment)")
    else:
        print("     ⚠️  PCR data not available")
    
    # Step 5: Identify Max Pain Level
    print("\n[5/7] 💰 Identifying Max Pain Level...")
    max_pain = options_calc.calculate_max_pain("NIFTY")
    
    if max_pain > 0:
        print(f"     Max Pain Strike: ₹{max_pain:,.2f}")
        
        # Get Nifty spot price
        nifty_quote = zerodha.kite.quote(["NSE:NIFTY 50"])
        if "NSE:NIFTY 50" in nifty_quote:
            nifty_spot = nifty_quote["NSE:NIFTY 50"]["last_price"]
            deviation = ((nifty_spot - max_pain) / max_pain) * 100
            
            print(f"     Nifty Spot: ₹{nifty_spot:,.2f}")
            print(f"     Deviation from Max Pain: {deviation:+.2f}%")
            
            if abs(deviation) < 1:
                print(f"     📊 Spot near Max Pain - Expect rangebound movement")
            elif deviation > 2:
                print(f"     📊 Spot above Max Pain - Downward pull likely")
            elif deviation < -2:
                print(f"     📊 Spot below Max Pain - Upward pull likely")
    else:
        print("     ⚠️  Max Pain calculation not available")
    
    # Step 6: Check OI Buildup
    print("\n[6/7] 🔍 Analyzing Open Interest Buildup...")
    support_resistance = options_calc.find_support_resistance("NIFTY")
    
    if support_resistance and support_resistance['call_resistance'] > 0:
        print(f"     Call Resistance: ₹{support_resistance['call_resistance']:,.2f}")
        print(f"     Put Support: ₹{support_resistance['put_support']:,.2f}")
        
        # Get highest OI changes
        df = options_calc.get_options_chain("NIFTY")
        if not df.empty:
            top_oi_change = df.nlargest(3, 'oi_change')
            print(f"\n     Top 3 OI Changes:")
            for idx, row in top_oi_change.iterrows():
                print(f"       {row['option_type']} {row['strike']:.0f}: +{row['oi_change']:,} contracts")
    else:
        print("     ⚠️  OI buildup analysis not available")
    
    # Step 7: Generate Fresh Signals
    print("\n[7/7] 🎲 Generating Fresh Trading Signals...")
    signal_gen = OptionsSignalGenerator()
    signals = signal_gen.scan_and_save("NIFTY")
    
    if signals:
        print(f"     ✅ Generated {len(signals)} trading signals")
        print(f"\n     📋 Top Signals (Confidence ≥ 70%):\n")
        
        high_conf_signals = [s for s in signals if s['confidence'] >= 70]
        
        if high_conf_signals:
            for i, signal in enumerate(high_conf_signals[:5], 1):  # Top 5
                print(f"     {i}. {signal['strategy']}")
                print(f"        {signal['signal_type']} {signal['option_type']} @ ₹{signal['strike']:.0f}")
                print(f"        Entry: ₹{signal['entry_premium']:.2f} | Target: ₹{signal['target_premium']:.2f} (+{((signal['target_premium']/signal['entry_premium']-1)*100):.0f}%)")
                print(f"        Confidence: {signal['confidence']:.0f}% | Risk:Reward: 1:{signal['risk_reward_ratio']:.1f}")
                print(f"        💡 {signal['reason']}\n")
        else:
            print("     ⚠️  All signals below 70% confidence threshold")
            print("     Recommendation: Wait for better setups")
    else:
        print("     ℹ️  No signals generated")
        print("     Possible reasons:")
        print("       • Market conditions not favorable")
        print("       • No clear setup found")
        print("       • Waiting for market open (9:15 AM)")
    
    # Review existing positions
    print("\n" + "=" * 80)
    print("📊 CURRENT PORTFOLIO STATUS")
    print("=" * 80)
    
    portfolio = OptionsVirtualPortfolio()
    positions = portfolio.get_open_positions()
    summary = portfolio.get_portfolio_summary()
    
    print(f"\nCapital: ₹{summary['total_capital']:,.2f}")
    print(f"Available Cash: ₹{summary['available_cash']:,.2f}")
    print(f"Invested: ₹{summary['invested_amount']:,.2f}")
    print(f"Unrealized P&L: ₹{summary['total_pnl']:,.2f}")
    
    if positions:
        print(f"\nOpen Positions ({len(positions)}):")
        for pos in positions:
            print(f"  • {pos['option_type']} {pos['strike']:.0f} | Entry: ₹{pos['entry_premium']:.2f} | Current: ₹{pos['current_premium']:.2f} | P&L: {pos['pnl_percent']:.2f}%")
    else:
        print(f"\nNo open positions")
    
    # Summary and recommendations
    print("\n" + "=" * 80)
    print("✅ MORNING ROUTINE COMPLETE")
    print("=" * 80)
    print(f"\n💡 Next Steps:")
    print(f"   1. Review generated signals above")
    print(f"   2. Trading engine will auto-execute signals with confidence ≥ 70%")
    print(f"   3. Monitor positions at http://localhost:3000/options-trading")
    print(f"   4. Options data updater running (updates every 5 min)")
    print(f"\n⚠️  Remember:")
    print(f"   • Max risk per trade: 2-5% of capital (₹{summary['total_capital'] * 0.02:,.0f} - ₹{summary['total_capital'] * 0.05:,.0f})")
    print(f"   • Exit by 3:00 PM for intraday strategies")
    print(f"   • Close all positions 1 day before expiry")
    print(f"\n" + "=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    print("\n[INFO] Starting Automated Morning Routine...")
    print("[INFO] This should be run at 9:00 AM before market opens")
    print("[INFO] Or run manually anytime to get current market analysis\n")
    
    try:
        success = asyncio.run(morning_routine())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Morning routine interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Morning routine failed: {e}")
        print(f"\n[ERROR] Morning routine failed: {e}")
        sys.exit(1)
