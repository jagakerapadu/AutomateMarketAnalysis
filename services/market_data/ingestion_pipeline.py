"""Market data ingestion service - Main orchestrator"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from config.logger import setup_logger
from config.database import get_db_context
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from services.market_data.adapters.yfinance_adapter import YFinanceAdapter
from services.market_data.adapters.nse_adapter import NSEAdapter
from services.market_data.storage.data_writer import DataWriter

logger = setup_logger("market_data_ingestion")

class MarketDataPipeline:
    """Orchestrates market data fetching and storage"""
    
    def __init__(self):
        self.zerodha = ZerodhaAdapter()
        self.yfinance = YFinanceAdapter()
        self.nse = NSEAdapter()
        self.writer = DataWriter()
        
        # Symbol lists
        self.nifty_50 = self._load_nifty_50_symbols()
        self.indices = ["NIFTY 50", "NIFTY BANK", "NIFTY FIN SERVICE", "INDIA VIX"]
        self.global_indices = ["^GSPC", "^DJI", "^IXIC", "^N225", "^HSI"]
    
    def _load_nifty_50_symbols(self) -> List[str]:
        """Load Nifty 50 constituent symbols"""
        # Top liquid NSE stocks for initial version
        return [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
            "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "BAJFINANCE",
            "ITC", "ASIANPAINT", "HCLTECH", "AXISBANK", "LT",
            "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND",
            "WIPRO", "BAJAJFINSV", "ONGC", "NTPC", "POWERGRID",
            "TATAMOTORS", "M&M", "TECHM", "ADANIPORTS", "COALINDIA",
            "TATASTEEL", "INDUSINDBK", "DIVISLAB", "DRREDDY", "CIPLA",
            "EICHERMOT", "HINDALCO", "GRASIM", "HEROMOTOCO", "BRITANNIA",
            "BAJAJ-AUTO", "SHREECEM", "UPL", "APOLLOHOSP", "TATACONSUM",
            "BPCL", "JSWSTEEL", "SBILIFE", "HDFCLIFE", "ADANIENT"
        ]
    
    async def fetch_global_markets(self):
        """Fetch global market data - Run at 7:30 AM IST"""
        logger.info("Fetching global market data...")
        
        try:
            data = await asyncio.to_thread(
                self.yfinance.get_global_indices,
                self.global_indices
            )
            
            if not data.empty:
                self.writer.write_global_indices(data)
                logger.info(f"Stored global indices: {len(data)} records")
            else:
                logger.warning("No global market data fetched")
                
        except Exception as e:
            logger.error(f"Error fetching global markets: {e}")
    
    async def fetch_indian_market_data(self):
        """Fetch Indian market OHLC - Run at 8:00 AM IST"""
        logger.info("Fetching Indian market data...")
        
        try:
            # Fetch Nifty 50 stocks
            tasks = []
            for symbol in self.nifty_50:
                task = asyncio.to_thread(
                    self.zerodha.get_historical_data,
                    symbol,
                    "day",
                    days=5
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine and store
            valid_data = [r for r in results if isinstance(r, pd.DataFrame) and not r.empty]
            
            if valid_data:
                combined_df = pd.concat(valid_data, ignore_index=True)
                self.writer.write_ohlc(combined_df)
                logger.info(f"Stored OHLC data: {len(combined_df)} records")
            else:
                logger.warning("No Indian market data fetched")
                
        except Exception as e:
            logger.error(f"Error fetching Indian market data: {e}")
    
    async def fetch_options_chain(self):
        """Fetch options chain data - Run at 8:45 AM IST"""
        logger.info("Fetching options chain...")
        
        try:
            # Fetch for Nifty and BankNifty
            symbols = ["NIFTY", "BANKNIFTY"]
            
            tasks = [
                asyncio.to_thread(self.nse.get_options_chain, symbol)
                for symbol in symbols
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, pd.DataFrame) and not result.empty:
                    self.writer.write_options_chain(result)
                    logger.info(f"Stored options chain: {len(result)} records")
            
        except Exception as e:
            logger.error(f"Error fetching options chain: {e}")
    
    async def fetch_market_sentiment(self):
        """Fetch VIX and market sentiment indicators"""
        logger.info("Fetching market sentiment...")
        
        try:
            sentiment_data = await asyncio.to_thread(self.nse.get_market_sentiment)
            
            if sentiment_data:
                self.writer.write_market_sentiment(sentiment_data)
                logger.info("Stored market sentiment data")
                
        except Exception as e:
            logger.error(f"Error fetching market sentiment: {e}")
    
    async def run_pre_market_pipeline(self):
        """Run complete pre-market data pipeline"""
        logger.info("=== Starting Pre-Market Data Pipeline ===")
        start_time = datetime.now()
        
        # Run tasks in sequence (some depend on others)
        await self.fetch_global_markets()
        await self.fetch_indian_market_data()
        await self.fetch_options_chain()
        await self.fetch_market_sentiment()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== Pre-Market Pipeline Complete in {duration:.2f}s ===")
    
    async def run_intraday_update(self):
        """Update intraday data during market hours"""
        logger.info("Running intraday data update...")
        
        try:
            # Fetch 1-min and 5-min data for active trading
            for symbol in self.nifty_50[:10]:  # Top 10 for intraday
                data_1m = await asyncio.to_thread(
                    self.zerodha.get_historical_data,
                    symbol,
                    "minute",
                    days=1
                )
                
                if not data_1m.empty:
                    self.writer.write_ohlc(data_1m)
            
            logger.info("Intraday update complete")
            
        except Exception as e:
            logger.error(f"Error in intraday update: {e}")

# Main execution
async def main():
    """Main entry point for market data service"""
    pipeline = MarketDataPipeline()
    
    # Run pre-market pipeline
    await pipeline.run_pre_market_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
