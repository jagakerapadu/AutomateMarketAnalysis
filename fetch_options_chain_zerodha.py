"""
Fetch Options Chain from Zerodha
Populates options_chain table with live data from Zerodha Kite API
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
import asyncio
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from services.market_data.storage.data_writer import DataWriter
from config.logger import setup_logger

logger = setup_logger("fetch_options_zerodha")


async def fetch_options_chain():
    """Fetch and store options chain from Zerodha"""
    print("\n" + "=" * 70)
    print("FETCHING OPTIONS CHAIN FROM ZERODHA")
    print("=" * 70)
    
    zerodha = ZerodhaAdapter()
    writer = DataWriter()
    
    # Check if Zerodha is initialized
    if not zerodha.kite or not zerodha.access_token:
        print("\n[ERROR] Zerodha not initialized or token expired!")
        print("\nTo fix:")
        print("  1. Run: py setup_credentials.py")
        print("  2. Select option: 3 (Regenerate Zerodha Access Token)")
        print("  3. Follow the authentication process")
        print("  4. Run this script again")
        return
    
    indices = ["NIFTY", "BANKNIFTY"]
    
    for index in indices:
        try:
            print(f"\n>> Fetching {index} options chain from Zerodha...")
            df = await asyncio.to_thread(zerodha.get_options_chain, index)
            
            if not df.empty:
                writer.write_options_chain(df)
                print(f"[OK] Stored {len(df)} option contracts for {index}")
                
                # Show sample data
                print(f"\nSample {index} options:")
                for _, row in df.head(5).iterrows():
                    print(f"  {row['option_type']} {row['strike']:.0f} - LTP: Rs.{row['ltp']:.2f}, OI: {row['oi']:,.0f}")
                
                # Show specific strike mentioned by user (23550 PE)
                if index == "NIFTY":
                    pe_23550 = df[(df['strike'] == 23550) & (df['option_type'] == 'PE')]
                    if not pe_23550.empty:
                        ltp = pe_23550.iloc[0]['ltp']
                        print(f"\n[INFO] NIFTY 23550 PE current premium: Rs.{ltp:.2f}")
            else:
                print(f"[WARN] No options data available for {index}")
                
        except Exception as e:
            logger.error(f"Error fetching {index} options: {e}")
            print(f"[ERROR] Error fetching {index} options chain: {e}")
    
    print("\n" + "=" * 70)
    print("[OK] Options chain data fetch complete!")
    print("\nNext: Check your positions with 'py check_options_status.py'")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(fetch_options_chain())
