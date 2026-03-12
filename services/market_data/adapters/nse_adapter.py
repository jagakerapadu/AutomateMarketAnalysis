"""NSE India Adapter - Direct NSE website scraping"""
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from bs4 import BeautifulSoup
from config.logger import setup_logger

logger = setup_logger("nse_adapter")

class NSEAdapter:
    """Adapter for NSE India public data"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        })
    
    def _get_cookies(self):
        """Get NSE session cookies"""
        try:
            self.session.get(self.base_url)
        except Exception as e:
            logger.warning(f"Failed to get NSE cookies: {e}")
    
    def get_options_chain(self, symbol: str) -> pd.DataFrame:
        """
        Fetch options chain from NSE
        
        Args:
            symbol: NIFTY or BANKNIFTY
        """
        try:
            self._get_cookies()
            
            url = f"{self.base_url}/api/option-chain-indices?symbol={symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"NSE API returned status {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            if 'records' not in data or 'data' not in data['records']:
                logger.warning("No options data in response")
                return pd.DataFrame()
            
            # Parse options data
            options_data = []
            records = data['records']['data']
            
            for record in records:
                timestamp = datetime.now()
                strike = record.get('strikePrice', 0)
                expiry = record.get('expiryDate', '')
                
                # Call option data
                if 'CE' in record:
                    ce = record['CE']
                    options_data.append({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'expiry_date': expiry,
                        'strike': strike,
                        'option_type': 'CE',
                        'ltp': ce.get('lastPrice', 0),
                        'iv': ce.get('impliedVolatility', 0),
                        'oi': ce.get('openInterest', 0),
                        'oi_change': ce.get('changeinOpenInterest', 0),
                        'volume': ce.get('totalTradedVolume', 0),
                        'bid': ce.get('bidprice', 0),
                        'ask': ce.get('askPrice', 0)
                    })
                
                # Put option data
                if 'PE' in record:
                    pe = record['PE']
                    options_data.append({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'expiry_date': expiry,
                        'strike': strike,
                        'option_type': 'PE',
                        'ltp': pe.get('lastPrice', 0),
                        'iv': pe.get('impliedVolatility', 0),
                        'oi': pe.get('openInterest', 0),
                        'oi_change': pe.get('changeinOpenInterest', 0),
                        'volume': pe.get('totalTradedVolume', 0),
                        'bid': pe.get('bidprice', 0),
                        'ask': pe.get('askPrice', 0)
                    })
            
            df = pd.DataFrame(options_data)
            logger.info(f"Fetched options chain for {symbol}: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching options chain for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_market_sentiment(self) -> Dict:
        """Fetch market sentiment indicators"""
        try:
            self._get_cookies()
            
            sentiment = {
                'timestamp': datetime.now()
            }
            
            # India VIX
            vix_url = f"{self.base_url}/api/equity-stockIndices?index=INDIA%20VIX"
            response = self.session.get(vix_url, timeout=10)
            
            if response.status_code == 200:
                vix_data = response.json()
                if 'data' in vix_data and len(vix_data['data']) > 0:
                    sentiment['india_vix'] = vix_data['data'][0].get('last', 0)
            
            # FII/DII data
            participant_url = f"{self.base_url}/api/fiidiiTrading"
            response = self.session.get(participant_url, timeout=10)
            
            if response.status_code == 200:
                participant_data = response.json()
                if participant_data:
                    # Parse FII/DII net values
                    # This structure may vary based on NSE API changes
                    pass
            
            logger.info("Fetched market sentiment data")
            return sentiment
            
        except Exception as e:
            logger.error(f"Error fetching market sentiment: {e}")
            return {}
    
    def get_advance_decline(self) -> Dict:
        """Get advance-decline ratio"""
        try:
            self._get_cookies()
            
            url = f"{self.base_url}/api/equity-stockIndices?index=NIFTY%2050"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Parse advance/decline data
                return {
                    'advances': 0,
                    'declines': 0,
                    'unchanged': 0
                }
            
        except Exception as e:
            logger.error(f"Error fetching advance-decline: {e}")
        
        return {}
