"""
Automated Options Price Updater
Fetches fresh options chain from Zerodha and updates all position prices
Run this script to fix stale price issues
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from datetime import datetime
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from services.market_data.storage.data_writer import DataWriter
from services.paper_trading.options_trading_engine import OptionsTradingEngine
from config.logger import setup_logger

logger = setup_logger("update_options_prices")


async def update_all_options_prices():
    """Fetch fresh prices and update all positions"""
    print("=" * 80)
    print("UPDATING OPTIONS PRICES FROM ZERODHA")
    print("=" * 80)
    
    # Step 1: Fetch fresh options chain
    print("\n[1/2] Fetching live options chain from Zerodha...")
    zerodha = ZerodhaAdapter()
    writer = DataWriter()
    
    if not zerodha.kite or not zerodha.access_token:
        print("\n❌ ERROR: Zerodha not initialized or token expired!")
        print("\nTo fix:")
        print("  1. Run: py setup_credentials.py")
        print("  2. Select option: 3 (Regenerate Zerodha Access Token)")
        print("  3. Follow the authentication process")
        print("  4. Run this script again")
        return False
    
    success = True
    for index in ["NIFTY", "BANKNIFTY"]:
        try:
            df = await asyncio.to_thread(zerodha.get_options_chain, index)
            
            if not df.empty:
                writer.write_options_chain(df)
                print(f"  ✅ Updated {len(df)} {index} contracts in options_chain table")
                
                # Show CE 23500 if NIFTY
                if index == "NIFTY":
                    ce_23500 = df[(df['strike'] == 23500) & (df['option_type'] == 'CE')]
                    if not ce_23500.empty:
                        ltp = ce_23500.iloc[0]['ltp']
                        print(f"     📊 CE 23500 current price: Rs.{ltp:.2f}")
            else:
                print(f"  ⚠️ No data received for {index}")
                success = False
                
        except Exception as e:
            print(f"  ❌ Error fetching {index}: {e}")
            success = False
    
    if not success:
        return False
    
    # Step 2: Update all position prices from fresh options chain
    print("\n[2/2] Updating position prices from fresh options_chain data...")
    try:
        engine = OptionsTradingEngine(auto_execute=False)
        engine.update_all_positions()
        print("  ✅ All position prices updated successfully")
        
        # Show updated positions
        positions = engine.portfolio.get_open_positions()
        if positions:
            print(f"\n📈 Updated {len(positions)} positions:")
            for pos in positions:
                pnl_sign = "+" if pos['pnl'] >= 0 else ""
                print(f"  {pos['option_type']} {pos['strike']:.0f}: "
                      f"Entry Rs.{pos['entry_premium']:.2f} → "
                      f"Current Rs.{pos['current_premium']:.2f} | "
                      f"P&L: {pnl_sign}Rs.{pos['pnl']:,.2f} ({pnl_sign}{pos['pnl_percent']:.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating positions: {e}")
        return False


async def main():
    """Main entry point"""
    success = await update_all_options_prices()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ SUCCESS: All options prices updated from live market data")
        print("=" * 80)
        print("\nℹ️ To keep prices updated automatically:")
        print("   Run: py run_options_data_updater.py")
        print("   (Updates every 5 minutes during market hours)")
        print("=" * 80)
    else:
        print("\n❌ FAILED: Could not update prices. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
