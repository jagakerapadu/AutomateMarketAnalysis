"""Zerodha Kite API Adapter"""
from typing import Optional, List
import pandas as pd
import pytz
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("zerodha_adapter")
settings = get_settings()

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')

class ZerodhaAdapter:
    """Adapter for Zerodha Kite API"""
    
    def __init__(self):
        self.api_key = settings.ZERODHA_API_KEY
        self.api_secret = settings.ZERODHA_API_SECRET
        self.access_token = settings.ZERODHA_ACCESS_TOKEN
        self.kite: Optional[KiteConnect] = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Kite connection"""
        if not self.api_key:
            logger.warning("Zerodha API key not configured")
            return
        
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            
            # Set access token if available
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                logger.info("Zerodha adapter initialized with access token")
            else:
                logger.warning("Zerodha access token not set. Run scripts/generate_kite_token.py")
                
        except Exception as e:
            logger.error(f"Failed to initialize Zerodha: {e}")
    
    def get_historical_data(
        self,
        symbol: str,
        interval: str = "day",
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical OHLC data
        
        Args:
            symbol: Trading symbol (e.g., "RELIANCE")
            interval: minute, day, 5minute, 15minute, 60minute
            days: Number of days to fetch
        """
        if not self.kite:
            logger.warning("Zerodha not initialized, returning empty DataFrame")
            return pd.DataFrame()
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Fetch data
            instrument_token = self._get_instrument_token(symbol)
            
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            if not data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['symbol'] = symbol
            df['timeframe'] = interval
            
            # Rename columns to match schema
            df = df.rename(columns={'date': 'timestamp'})
            
            # Fix timezone: Kite returns timestamps at midnight IST
            # For daily data, timestamps should be at market close (3:30 PM IST)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            if interval == 'day':
                # Kite returns timestamps at 00:00 (midnight)
                # Shift to 15:30 (3:30 PM IST - market close time)
                df['timestamp'] = df['timestamp'] + pd.Timedelta(hours=15, minutes=30)
            
            logger.info(f"Fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _get_instrument_token(self, symbol: str) -> int:
        """Get instrument token for a symbol"""
        # Simplified - In production, fetch from instruments dump
        # This is a placeholder
        instruments_map = {
            "RELIANCE": 738561,
            "TCS": 2953217,
            "INFY": 408065,
            # Add more mappings or load from instruments file
        }
        
        return instruments_map.get(symbol, 0)
    
    def get_quote(self, symbols: List[str]) -> dict:
        """Get real-time quotes for symbols"""
        if not self.kite:
            return {}
        
        try:
            instruments = [f"NSE:{s}" for s in symbols]
            quotes = self.kite.quote(instruments)
            return quotes
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return {}
    
    def get_options_chain(self, symbol: str, expiry: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch options chain data from Zerodha
        
        Args:
            symbol: NIFTY or BANKNIFTY
            expiry: Optional expiry date (YYYY-MM-DD). If None, uses nearest expiry
        
        Returns:
            DataFrame with columns: timestamp, symbol, expiry_date, strike, option_type, ltp, iv, oi, etc.
        """
        if not self.kite:
            logger.warning("Zerodha not initialized")
            return pd.DataFrame()
        
        try:
            # Fetch all instruments
            instruments = self.kite.instruments("NFO")
            
            # Filter for index options
            symbol_map = {
                "NIFTY": "NIFTY",
                "BANKNIFTY": "BANKNIFTY"
            }
            
            trading_symbol_prefix = symbol_map.get(symbol)
            if not trading_symbol_prefix:
                logger.error(f"Invalid symbol: {symbol}")
                return pd.DataFrame()
            
            # Filter options for this symbol
            options_instruments = [
                inst for inst in instruments
                if inst['name'] == trading_symbol_prefix 
                and inst['instrument_type'] in ['CE', 'PE']
            ]
            
            if not options_instruments:
                logger.warning(f"No options instruments found for {symbol}")
                return pd.DataFrame()
            
            # If expiry not specified, find nearest weekly expiry
            if not expiry:
                expiries = sorted(set([inst['expiry'] for inst in options_instruments]))
                if not expiries:
                    return pd.DataFrame()
                
                # IMPORTANT: Nifty/BankNifty weekly expiry is on TUESDAY (since 2024)
                # Filter to get only Tuesday expiries (weekday() returns 1 for Tuesday)
                tuesday_expiries = [exp for exp in expiries if exp.weekday() == 1]
                
                if tuesday_expiries:
                    expiry = tuesday_expiries[0]  # Nearest Tuesday expiry
                    logger.info(f"Using Tuesday expiry: {expiry.strftime('%Y-%m-%d (%A)')}")
                else:
                    # Fallback to nearest expiry if no Tuesday found (shouldn't happen normally)
                    expiry = expiries[0]
                    logger.warning(f"No Tuesday expiry found, using nearest: {expiry.strftime('%Y-%m-%d (%A)')}")
            else:
                expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
            
            # Filter by expiry
            options_instruments = [
                inst for inst in options_instruments
                if inst['expiry'] == expiry
            ]
            
            if not options_instruments:
                logger.warning(f"No options found for expiry {expiry}")
                return pd.DataFrame()
            
            # Get quotes for all options (batch processing - max 500 at a time)
            instrument_keys = [f"NFO:{inst['tradingsymbol']}" for inst in options_instruments]
            
            options_data = []
            
            # Process in batches of 200 (Kite API limit is 500, but keeping conservative)
            batch_size = 200
            for i in range(0, len(instrument_keys), batch_size):
                batch_keys = instrument_keys[i:i+batch_size]
                batch_instruments = options_instruments[i:i+batch_size]
                
                try:
                    quotes = self.kite.quote(batch_keys)
                    
                    for inst in batch_instruments:
                        key = f"NFO:{inst['tradingsymbol']}"
                        if key in quotes:
                            quote = quotes[key]
                            
                            options_data.append({
                                'timestamp': datetime.now(),
                                'symbol': symbol,
                                'expiry_date': inst['expiry'].strftime('%Y-%m-%d'),
                                'strike': inst['strike'],
                                'option_type': inst['instrument_type'],  # CE or PE
                                'ltp': quote.get('last_price', 0),
                                'iv': quote.get('oi', 0) * 0.0001,  # Placeholder - Kite doesn't provide IV directly
                                'oi': quote.get('oi', 0),
                                'oi_change': quote.get('oi_day_high', 0) - quote.get('oi_day_low', 0),
                                'volume': quote.get('volume', 0),
                                'bid': quote.get('depth', {}).get('buy', [{}])[0].get('price', 0),
                                'ask': quote.get('depth', {}).get('sell', [{}])[0].get('price', 0)
                            })
                            
                except Exception as e:
                    logger.error(f"Error fetching batch quotes: {e}")
                    continue
            
            df = pd.DataFrame(options_data)
            logger.info(f"Fetched {len(df)} options for {symbol} {expiry}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching options chain: {e}")
            return pd.DataFrame()
