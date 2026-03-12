"""Scheduler - Automates trading system tasks"""
import schedule
import time
from datetime import datetime
import asyncio
import pytz
from config.logger import setup_logger
from services.market_data.ingestion_pipeline import MarketDataPipeline
from services.indicators.indicator_engine import IndicatorEngine
from services.strategy.strategy_engine import StrategyEngine

logger = setup_logger("scheduler")

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')

# Initialize components
market_pipeline = MarketDataPipeline()
indicator_engine = IndicatorEngine()
strategy_engine = StrategyEngine()

# Stock universe
NIFTY_50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
    "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "BAJFINANCE",
    "ITC", "ASIANPAINT", "HCLTECH", "AXISBANK", "LT"
]

def run_global_market_fetch():
    """7:30 AM - Fetch global market data"""
    logger.info("=== Job: Fetching global markets ===")
    asyncio.run(market_pipeline.fetch_global_markets())

def run_indian_market_fetch():
    """8:00 AM - Fetch Indian market OHLC"""
    logger.info("=== Job: Fetching Indian market data ===")
    asyncio.run(market_pipeline.fetch_indian_market_data())

def run_options_chain_fetch():
    """8:45 AM - Fetch options chain"""
    logger.info("=== Job: Fetching options chain ===")
    asyncio.run(market_pipeline.fetch_options_chain())

def run_indicator_calculation():
    """9:00 AM - Calculate technical indicators"""
    logger.info("=== Job: Calculating indicators ===")
    indicator_engine.process_all_symbols(NIFTY_50, timeframes=['1d', '1h', '15m'])

def run_strategy_scan():
    """9:10 AM - Generate trading signals"""
    logger.info("=== Job: Running strategy scan ===")
    strategy_engine.run_pre_market_scan(NIFTY_50)

def run_intraday_update():
    """Every 5 minutes during market hours"""
    current_time = datetime.now(IST).time()
    market_open = datetime.strptime("09:15", "%H:%M").time()
    market_close = datetime.strptime("15:30", "%H:%M").time()
    
    if market_open <= current_time <= market_close:
        logger.info("=== Job: Intraday update ===")
        asyncio.run(market_pipeline.run_intraday_update())

def run_post_market_analysis():
    """4:00 PM - Post-market analysis"""
    logger.info("=== Job: Post-market analysis ===")
    indicator_engine.process_all_symbols(NIFTY_50, timeframes=['1d'])

def setup_scheduler():
    """Setup all scheduled jobs"""
    logger.info("Setting up scheduler...")
    
    # Pre-market jobs
    schedule.every().day.at("07:30").do(run_global_market_fetch)
    schedule.every().day.at("08:00").do(run_indian_market_fetch)
    schedule.every().day.at("08:45").do(run_options_chain_fetch)
    schedule.every().day.at("09:00").do(run_indicator_calculation)
    schedule.every().day.at("09:10").do(run_strategy_scan)
    
    # Intraday jobs (every 5 minutes during market hours)
    schedule.every(5).minutes.do(run_intraday_update)
    
    # Post-market jobs
    schedule.every().day.at("16:00").do(run_post_market_analysis)
    
    logger.info("Scheduler configured successfully")

def run_scheduler():
    """Run the scheduler"""
    setup_scheduler()
    
    logger.info("Scheduler started - waiting for jobs...")
    
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
