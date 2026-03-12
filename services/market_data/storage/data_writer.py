"""Data writer - Persists market data to TimescaleDB"""
import pandas as pd
from datetime import datetime
from typing import Dict
from sqlalchemy import text
from config.database import get_db_context
from config.logger import setup_logger

logger = setup_logger("data_writer")

class DataWriter:
    """Writes market data to database"""
    
    def write_ohlc(self, df: pd.DataFrame) -> int:
        """
        Write OHLC data to market_ohlc table
        
        Args:
            df: DataFrame with columns: timestamp, symbol, timeframe, open, high, low, close, volume
        
        Returns:
            Number of records inserted
        """
        if df.empty:
            logger.warning("Empty DataFrame, nothing to write")
            return 0
        
        try:
            with get_db_context() as db:
                # Prepare data
                df = df.copy()
                
                # Ensure required columns exist
                required_cols = ['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    logger.error(f"Missing columns: {missing_cols}")
                    return 0
                
                # Add optional columns with defaults
                if 'vwap' not in df.columns:
                    df['vwap'] = (df['high'] + df['low'] + df['close']) / 3
                
                if 'oi' not in df.columns:
                    df['oi'] = 0
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Insert using ON CONFLICT to handle duplicates
                insert_query = text("""
                    INSERT INTO market_ohlc (timestamp, symbol, timeframe, open, high, low, close, volume, vwap, oi)
                    VALUES (:timestamp, :symbol, :timeframe, :open, :high, :low, :close, :volume, :vwap, :oi)
                    ON CONFLICT (timestamp, symbol, timeframe) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        vwap = EXCLUDED.vwap,
                        oi = EXCLUDED.oi
                """)
                
                records = df.to_dict('records')
                db.execute(insert_query, records)
                
                logger.info(f"Inserted/Updated {len(records)} OHLC records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error writing OHLC data: {e}")
            return 0
    
    def write_options_chain(self, df: pd.DataFrame) -> int:
        """Write options chain data"""
        if df.empty:
            return 0
        
        try:
            with get_db_context() as db:
                # Ensure timestamp column
                df['timestamp'] = pd.to_datetime(df.get('timestamp', datetime.now()))
                
                insert_query = text("""
                    INSERT INTO options_chain 
                    (timestamp, symbol, expiry_date, strike, option_type, ltp, iv, oi, oi_change, volume, bid, ask)
                    VALUES (:timestamp, :symbol, :expiry_date, :strike, :option_type, :ltp, :iv, :oi, :oi_change, :volume, :bid, :ask)
                    ON CONFLICT (timestamp, symbol, expiry_date, strike, option_type) DO UPDATE SET
                        ltp = EXCLUDED.ltp,
                        iv = EXCLUDED.iv,
                        oi = EXCLUDED.oi,
                        oi_change = EXCLUDED.oi_change,
                        volume = EXCLUDED.volume,
                        bid = EXCLUDED.bid,
                        ask = EXCLUDED.ask
                """)
                
                records = df.to_dict('records')
                db.execute(insert_query, records)
                
                logger.info(f"Inserted/Updated {len(records)} options chain records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error writing options chain: {e}")
            return 0
    
    def write_global_indices(self, df: pd.DataFrame) -> int:
        """Write global indices data"""
        if df.empty:
            return 0
        
        try:
            with get_db_context() as db:
                df['timestamp'] = pd.to_datetime(df.get('timestamp', datetime.now()))
                
                insert_query = text("""
                    INSERT INTO global_indices (timestamp, index_name, value, change_percent)
                    VALUES (:timestamp, :index_name, :value, :change_percent)
                    ON CONFLICT (timestamp, index_name) DO UPDATE SET
                        value = EXCLUDED.value,
                        change_percent = EXCLUDED.change_percent
                """)
                
                records = df.to_dict('records')
                db.execute(insert_query, records)
                
                logger.info(f"Inserted/Updated {len(records)} global indices records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error writing global indices: {e}")
            return 0
    
    def write_market_sentiment(self, data: Dict) -> bool:
        """Write market sentiment data"""
        try:
            with get_db_context() as db:
                data['timestamp'] = data.get('timestamp', datetime.now())
                
                insert_query = text("""
                    INSERT INTO market_sentiment (timestamp, india_vix, nifty_pe_ratio, nifty_pb_ratio, 
                                                 fii_net, dii_net, advance_decline_ratio, put_call_ratio)
                    VALUES (:timestamp, :india_vix, :nifty_pe_ratio, :nifty_pb_ratio,
                            :fii_net, :dii_net, :advance_decline_ratio, :put_call_ratio)
                    ON CONFLICT (timestamp) DO UPDATE SET
                        india_vix = EXCLUDED.india_vix,
                        nifty_pe_ratio = EXCLUDED.nifty_pe_ratio,
                        fii_net = EXCLUDED.fii_net,
                        dii_net = EXCLUDED.dii_net
                """)
                
                # Fill missing fields with None
                defaults = {
                    'india_vix': None, 'nifty_pe_ratio': None, 'nifty_pb_ratio': None,
                    'fii_net': None, 'dii_net': None, 'advance_decline_ratio': None, 'put_call_ratio': None
                }
                defaults.update(data)
                
                db.execute(insert_query, defaults)
                
                logger.info("Inserted market sentiment data")
                return True
                
        except Exception as e:
            logger.error(f"Error writing market sentiment: {e}")
            return False
