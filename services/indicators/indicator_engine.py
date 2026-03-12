"""Technical Indicator Engine - Calculates all indicators"""
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from sqlalchemy import text
from config.database import get_db_context
from config.logger import setup_logger

logger = setup_logger("indicator_engine")

class IndicatorEngine:
    """Calculates technical indicators for market data"""
    
    def __init__(self):
        self.indicators_calculated = 0
    
    def calculate_all_indicators(self, symbol: str, timeframe: str = "1d") -> pd.DataFrame:
        """
        Calculate all indicators for a symbol
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe (1m, 5m, 15m, 1h, 1d)
        
        Returns:
            DataFrame with all indicators
        """
        try:
            # Fetch OHLC data from database
            df = self._fetch_ohlc_data(symbol, timeframe)
            
            if df.empty or len(df) < 200:
                logger.warning(f"Insufficient data for {symbol} {timeframe}")
                return pd.DataFrame()
            
            # Calculate indicators
            df = self._calculate_trend_indicators(df)
            df = self._calculate_momentum_indicators(df)
            df = self._calculate_volatility_indicators(df)
            df = self._calculate_supertrend(df)
            
            # Save to database
            self._save_indicators(df, symbol, timeframe)
            
            logger.info(f"Calculated indicators for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_ohlc_data(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Fetch OHLC data from database"""
        try:
            with get_db_context() as db:
                query = text("""
                    SELECT timestamp, open, high, low, close, volume, vwap
                    FROM market_ohlc
                    WHERE symbol = :symbol AND timeframe = :timeframe
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                
                result = db.execute(query, {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'limit': limit
                })
                
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                return df
                
        except Exception as e:
            logger.error(f"Error fetching OHLC data: {e}")
            return pd.DataFrame()
    
    def _calculate_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trend indicators (EMA, VWAP, ADX)"""
        close = df['close']
        
        # Exponential Moving Averages
        df['ema_9'] = EMAIndicator(close, window=9).ema_indicator()
        df['ema_21'] = EMAIndicator(close, window=21).ema_indicator()
        df['ema_50'] = EMAIndicator(close, window=50).ema_indicator()
        df['ema_200'] = EMAIndicator(close, window=200).ema_indicator()
        
        # MACD
        macd = MACD(close)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_hist'] = macd.macd_diff()
        
        # VWAP is already in the data; if not, calculate simple version
        if 'vwap' not in df.columns or df['vwap'].isna().all():
            df['vwap'] = (df['high'] + df['low'] + df['close']) / 3
        
        return df
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators (RSI, Stochastic)"""
        close = df['close']
        high = df['high']
        low = df['low']
        
        # RSI
        df['rsi'] = RSIIndicator(close, window=14).rsi()
        
        # Stochastic Oscillator
        stoch = StochasticOscillator(high, low, close, window=14, smooth_window=3)
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        
        return df
    
    def _calculate_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility indicators (ATR, Bollinger Bands)"""
        close = df['close']
        high = df['high']
        low = df['low']
        
        # Average True Range
        atr = AverageTrueRange(high, low, close, window=14)
        df['atr'] = atr.average_true_range()
        
        # Bollinger Bands
        bb = BollingerBands(close, window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        
        return df
    
    def _calculate_supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """
        Calculate Supertrend indicator
        
        Supertrend is a popular trend-following indicator
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate ATR
        atr = AverageTrueRange(high, low, close, window=period).average_true_range()
        
        # Basic bands
        hl_avg = (high + low) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # Initialize supertrend
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=str)
        
        # Calculate supertrend
        for i in range(1, len(df)):
            if close.iloc[i] > upper_band.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 'up'
            elif close.iloc[i] < lower_band.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = 'down'
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]
        
        df['supertrend'] = supertrend
        df['supertrend_direction'] = direction
        
        return df
    
    def _save_indicators(self, df: pd.DataFrame, symbol: str, timeframe: str) -> bool:
        """Save calculated indicators to database"""
        try:
            with get_db_context() as db:
                # Prepare data for insertion
                indicator_cols = [
                    'timestamp', 'rsi', 'macd', 'macd_signal', 'macd_hist',
                    'ema_9', 'ema_21', 'ema_50', 'ema_200', 'vwap',
                    'supertrend', 'supertrend_direction', 'atr',
                    'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d'
                ]
                
                # Filter to only available columns
                available_cols = [col for col in indicator_cols if col in df.columns]
                subset = df[available_cols].copy()
                subset['symbol'] = symbol
                subset['timeframe'] = timeframe
                
                # Insert query
                insert_query = text("""
                    INSERT INTO indicators (
                        timestamp, symbol, timeframe, rsi, macd, macd_signal, macd_hist,
                        ema_9, ema_21, ema_50, ema_200, vwap, supertrend, supertrend_direction,
                        atr, bb_upper, bb_middle, bb_lower, stoch_k, stoch_d
                    )
                    VALUES (
                        :timestamp, :symbol, :timeframe, :rsi, :macd, :macd_signal, :macd_hist,
                        :ema_9, :ema_21, :ema_50, :ema_200, :vwap, :supertrend, :supertrend_direction,
                        :atr, :bb_upper, :bb_middle, :bb_lower, :stoch_k, :stoch_d
                    )
                    ON CONFLICT (timestamp, symbol, timeframe) DO UPDATE SET
                        rsi = EXCLUDED.rsi,
                        macd = EXCLUDED.macd,
                        ema_9 = EXCLUDED.ema_9,
                        ema_21 = EXCLUDED.ema_21,
                        vwap = EXCLUDED.vwap,
                        supertrend = EXCLUDED.supertrend
                """)
                
                records = subset.to_dict('records')
                db.execute(insert_query, records)
                
                self.indicators_calculated += len(records)
                logger.info(f"Saved {len(records)} indicator records for {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving indicators: {e}")
            return False
    
    def process_all_symbols(self, symbols: list, timeframes: list = None) -> int:
        """Process indicators for multiple symbols"""
        if timeframes is None:
            timeframes = ['1d', '1h', '15m']
        
        total_processed = 0
        
        for symbol in symbols:
            for timeframe in timeframes:
                result = self.calculate_all_indicators(symbol, timeframe)
                if not result.empty:
                    total_processed += 1
        
        logger.info(f"Processed indicators for {total_processed} symbol-timeframe combinations")
        return total_processed

# Main execution
if __name__ == "__main__":
    engine = IndicatorEngine()
    
    # Example: Calculate for Nifty 50 stocks
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
    engine.process_all_symbols(symbols)
