"""
Fetch Nifty Options Chain Data
Populates options_chain table with live data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timezone
import asyncio
from services.market_data.adapters.nse_adapter import NSEAdapter
from services.market_data.storage.data_writer import DataWriter
from config.logger import setup_logger

logger = setup_logger("fetch_options_data")


async def fetch_options_chain():
    """Fetch and store Nifty options chain"""
    print("\n" + "=" * 70)
    print("FETCHING NIFTY OPTIONS CHAIN DATA")
    print("=" * 70)
    
    nse = NSEAdapter()
    writer = DataWriter()
    
    indices = ["NIFTY", "BANKNIFTY"]
    
    for index in indices:
        try:
            print(f"\n>> Fetching {index} options chain...")
            df = await asyncio.to_thread(nse.get_options_chain, index)
            
            if not df.empty:
                writer.write_options_chain(df)
                print(f"[OK] Stored {len(df)} option contracts for {index}")
                
                # Show sample data
                print(f"\nSample {index} options:")
                for _, row in df.head(3).iterrows():
                    print(f"  {row['option_type']} {row['strike']} - LTP: Rs.{row['ltp']:.2f}, IV: {row['iv']:.4f}, OI: {row['oi']:,}")
            else:
                print(f"[WARN] No options data available for {index}")
                
        except Exception as e:
            logger.error(f"Error fetching {index} options: {e}")
            print(f"[ERROR] Error fetching {index} options chain")
    
    print("\n" + "=" * 70)
    print("[OK] Options chain data fetch complete!")
    print("\nNext: Run 'py generate_options_signals.py' to generate trading signals")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(fetch_options_chain())
