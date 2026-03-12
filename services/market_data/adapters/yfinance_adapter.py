"""Yahoo Finance Adapter - Fallback data source"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import List
from config.logger import setup_logger

logger = setup_logger("yfinance_adapter")

class YFinanceAdapter:
    """Adapter for Yahoo Finance API (Fallback)"""
    
    def __init__(self):
        self.symbol_map = {
            "NIFTY 50": "^NSEI",
            "NIFTY BANK": "^NSEBANK",
            "SENSEX": "^BSESN",
        }
    
    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data from Yahoo Finance
        
        Args:
            symbol: Yahoo ticker symbol
            period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
            interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo
        """
        try:
            # Convert NSE symbol to Yahoo format
            yahoo_symbol = f"{symbol}.NS" if "^" not in symbol else symbol
            
            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data fetched for {symbol}")
                return pd.DataFrame()
            
            # Reset index to get timestamp as column
            data = data.reset_index()
            
            # Standardize columns
            data = data.rename(columns={
                'Date': 'timestamp',
                'Datetime': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            data['symbol'] = symbol
            data['timeframe'] = interval
            
            # Calculate VWAP (approximation)
            if 'volume' in data.columns:
                data['vwap'] = ((data['high'] + data['low'] + data['close']) / 3)
            
            logger.info(f"Fetched {len(data)} records for {symbol} from YFinance")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching YFinance data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_global_indices(self, indices: List[str]) -> pd.DataFrame:
        """Fetch global market indices"""
        try:
            all_data = []
            
            for index in indices:
                ticker = yf.Ticker(index)
                info = ticker.info
                
                if not info:
                    continue
                
                data_point = {
                    'timestamp': datetime.now(),
                    'index_name': index,
                    'value': info.get('regularMarketPrice', 0),
                    'change_percent': info.get('regularMarketChangePercent', 0)
                }
                all_data.append(data_point)
            
            df = pd.DataFrame(all_data)
            logger.info(f"Fetched {len(df)} global indices")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching global indices: {e}")
            return pd.DataFrame()
    
    def get_nifty_50_constituents(self) -> List[str]:
        """Get Nifty 50 constituent symbols"""
        # This would ideally fetch from NSE website
        # For now, return static list
        return [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
            "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "BAJFINANCE"
            # ... add rest
        ]
