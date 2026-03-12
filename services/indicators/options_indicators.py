"""
Options Market Indicators Calculator
Calculates options-specific indicators like PCR, IV Rank, Max Pain, etc.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import psycopg2
from decimal import Decimal
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("options_indicators")
settings = get_settings()


class OptionsIndicators:
    """Calculate options-specific market indicators"""
    
    def __init__(self):
        self.conn = self._get_db_connection()
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
    
    def get_options_chain(self, symbol: str = "NIFTY", expiry: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch latest options chain data
        
        Args:
            symbol: Index name (NIFTY, BANKNIFTY)
            expiry: Expiry date (YYYY-MM-DD), if None uses nearest expiry
        """
        cursor = self.conn.cursor()
        
        if expiry is None:
            # Get nearest expiry
            cursor.execute("""
                SELECT DISTINCT expiry_date 
                FROM options_chain 
                WHERE symbol = %s AND expiry_date >= CURRENT_DATE
                ORDER BY expiry_date LIMIT 1
            """, (symbol,))
            result = cursor.fetchone()
            if result:
                expiry = result[0].strftime('%Y-%m-%d')
            else:
                logger.warning(f"No expiry found for {symbol}")
                return pd.DataFrame()
        
        # Fetch latest options chain for expiry
        cursor.execute("""
            SELECT DISTINCT ON (strike, option_type)
                timestamp, symbol, expiry_date, strike, option_type,
                ltp, iv, oi, oi_change, volume, bid, ask
            FROM options_chain
            WHERE symbol = %s AND expiry_date = %s
            ORDER BY strike, option_type, timestamp DESC
        """, (symbol, expiry))
        
        rows = cursor.fetchall()
        cursor.close()
        
        if not rows:
            logger.warning(f"No options data found for {symbol} {expiry}")
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=[
            'timestamp', 'symbol', 'expiry_date', 'strike', 'option_type',
            'ltp', 'iv', 'oi', 'oi_change', 'volume', 'bid', 'ask'
        ])
        
        return df
    
    def calculate_pcr_ratio(self, symbol: str = "NIFTY") -> Dict[str, float]:
        """
        Calculate Put-Call Ratio (PCR)
        
        Returns:
            Dict with pcr_all, pcr_oi, pcr_volume
            - PCR > 1.0: More puts (bullish)
            - PCR < 1.0: More calls (bearish)
        """
        df = self.get_options_chain(symbol)
        
        if df.empty:
            return {'pcr_all': 0, 'pcr_oi': 0, 'pcr_volume': 0}
        
        ce_df = df[df['option_type'] == 'CE']
        pe_df = df[df['option_type'] == 'PE']
        
        # PCR based on OI
        total_ce_oi = ce_df['oi'].sum()
        total_pe_oi = pe_df['oi'].sum()
        pcr_oi = float(total_pe_oi / total_ce_oi) if total_ce_oi > 0 else 0
        
        # PCR based on volume
        total_ce_volume = ce_df['volume'].sum()
        total_pe_volume = pe_df['volume'].sum()
        pcr_volume = float(total_pe_volume / total_ce_volume) if total_ce_volume > 0 else 0
        
        # Average PCR
        pcr_all = (pcr_oi + pcr_volume) / 2
        
        return {
            'pcr_all': round(pcr_all, 4),
            'pcr_oi': round(pcr_oi, 4),
            'pcr_volume': round(pcr_volume, 4),
            'total_ce_oi': int(total_ce_oi),
            'total_pe_oi': int(total_pe_oi),
            'oi_change_ce': int(ce_df['oi_change'].sum()),
            'oi_change_pe': int(pe_df['oi_change'].sum())
        }
    
    def calculate_max_pain(self, symbol: str = "NIFTY") -> float:
        """
        Calculate Max Pain - strike price with maximum open interest
        
        Max Pain Theory: Options tend to gravitate towards the strike 
        where maximum number of options expire worthless
        """
        df = self.get_options_chain(symbol)
        
        if df.empty:
            return 0
        
        strikes = sorted(df['strike'].unique())
        max_pain_values = {}
        
        for strike in strikes:
            pain = 0
            
            # Calculate pain for calls
            ce_data = df[(df['option_type'] == 'CE') & (df['strike'] < strike)]
            pain += (ce_data['oi'] * (strike - ce_data['strike'])).sum()
            
            # Calculate pain for puts
            pe_data = df[(df['option_type'] == 'PE') & (df['strike'] > strike)]
            pain += (pe_data['oi'] * (pe_data['strike'] - strike)).sum()
            
            max_pain_values[strike] = pain
        
        # Strike with minimum pain = Max Pain
        max_pain_strike = min(max_pain_values, key=max_pain_values.get)
        
        return float(max_pain_strike)
    
    def find_support_resistance(self, symbol: str = "NIFTY") -> Dict[str, float]:
        """
        Identify support/resistance levels from options OI
        
        Returns:
            call_resistance: Strike with highest CE OI (resistance)
            put_support: Strike with highest PE OI (support)
        """
        df = self.get_options_chain(symbol)
        
        if df.empty:
            return {'call_resistance': 0, 'put_support': 0}
        
        # Convert decimal columns to float
        df['strike'] = df['strike'].astype(float)
        df['oi'] = df['oi'].astype(float)
        
        # Highest CE OI = Strong resistance
        ce_df = df[df['option_type'] == 'CE']
        call_resistance = ce_df.loc[ce_df['oi'].idxmax(), 'strike'] if not ce_df.empty else 0
        
        # Highest PE OI = Strong support
        pe_df = df[df['option_type'] == 'PE']
        put_support = pe_df.loc[pe_df['oi'].idxmax(), 'strike'] if not pe_df.empty else 0
        
        return {
            'call_resistance': float(call_resistance),
            'put_support': float(put_support)
        }
    
    def calculate_iv_rank(self, symbol: str = "NIFTY", lookback_days: int = 30) -> Dict[str, float]:
        """
        Calculate IV Rank (where current IV stands in historical range)
        
        IV Rank = (Current IV - Min IV) / (Max IV - Min IV) * 100
        - IV Rank > 50: High volatility (good for option selling)
        - IV Rank < 50: Low volatility (good for option buying)
        """
        df = self.get_options_chain(symbol)
        
        if df.empty:
            return {'iv_rank': 0, 'atm_call_iv': 0, 'atm_put_iv': 0}
        
        # Get ATM strike (closest to spot price)
        spot_price = self.get_spot_price(symbol)
        df['strike_diff'] = abs(df['strike'] - spot_price)
        atm_strike = df.loc[df['strike_diff'].idxmin(), 'strike']
        
        # ATM IV
        atm_call_iv = df[(df['strike'] == atm_strike) & (df['option_type'] == 'CE')]['iv'].values
        atm_put_iv = df[(df['strike'] == atm_strike) & (df['option_type'] == 'PE')]['iv'].values
        
        atm_call_iv = float(atm_call_iv[0]) if len(atm_call_iv) > 0 else 0
        atm_put_iv = float(atm_put_iv[0]) if len(atm_put_iv) > 0 else 0
        current_iv = (atm_call_iv + atm_put_iv) / 2
        
        # Get historical IV range (last N days)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT MIN(iv) as min_iv, MAX(iv) as max_iv
            FROM options_chain
            WHERE symbol = %s 
                AND timestamp >= NOW() - INTERVAL '%s days'
                AND iv IS NOT NULL
        """, (symbol, lookback_days))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0] and result[1]:
            min_iv, max_iv = float(result[0]), float(result[1])
            iv_rank = ((current_iv - min_iv) / (max_iv - min_iv) * 100) if max_iv > min_iv else 50
        else:
            iv_rank = 50  # Default
        
        return {
            'iv_rank': round(iv_rank, 2),
            'atm_call_iv': round(atm_call_iv, 4),
            'atm_put_iv': round(atm_put_iv, 4),
            'current_iv': round(current_iv, 4)
        }
    
    def get_spot_price(self, symbol: str = "NIFTY") -> float:
        """Get current spot price of the index"""
        cursor = self.conn.cursor()
        
        # Try to get from latest OHLC
        cursor.execute("""
            SELECT close FROM market_ohlc
            WHERE symbol = %s
            ORDER BY timestamp DESC LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return float(result[0])
        
        # Fallback: estimate from options chain
        df = self.get_options_chain(symbol)
        if not df.empty:
            # ATM strike is close to spot
            return float(df['strike'].median())
        
        return 0
    
    def get_atm_strike(self, symbol: str = "NIFTY") -> float:
        """Get At-The-Money (ATM) strike"""
        spot = self.get_spot_price(symbol)
        df = self.get_options_chain(symbol)
        
        if df.empty:
            return round(spot / 50) * 50  # Nearest 50 strike
        
        df['strike'] = df['strike'].astype(float)  # Convert to float
        strikes = df['strike'].unique()
        atm = min(strikes, key=lambda x: abs(x - spot))
        
        return float(atm)
    
    def classify_strike(self, strike: float, symbol: str = "NIFTY", option_type: str = "CE") -> str:
        """
        Classify strike as ATM, ITM, or OTM
        
        For CE: ITM if strike < spot, OTM if strike > spot
        For PE: ITM if strike > spot, OTM if strike < spot
        """
        spot = self.get_spot_price(symbol)
        atm = self.get_atm_strike(symbol)
        
        if abs(strike - atm) <= 50:  # Within 50 points = ATM
            return "ATM"
        
        if option_type == "CE":
            return "ITM" if strike < spot else "OTM"
        else:  # PE
            return "ITM" if strike > spot else "OTM"
    
    def calculate_all_indicators(self, symbol: str = "NIFTY") -> Dict:
        """Calculate all options indicators at once"""
        logger.info(f"Calculating options indicators for {symbol}")
        
        try:
            spot = self.get_spot_price(symbol)
            pcr = self.calculate_pcr_ratio(symbol)
            max_pain = self.calculate_max_pain(symbol)
            support_resistance = self.find_support_resistance(symbol)
            iv_metrics = self.calculate_iv_rank(symbol)
            
            indicators = {
                'timestamp': datetime.now(timezone.utc),
                'symbol': symbol,
                'nifty_spot': spot,
                'nifty_fut': spot,  # Placeholder - can integrate futures data
                **pcr,
                'max_pain_nifty': max_pain,
                **support_resistance,
                **iv_metrics
            }
            
            logger.info(f"Options Indicators - Spot: {spot}, PCR: {pcr['pcr_oi']:.4f}, Max Pain: {max_pain}, IV Rank: {iv_metrics['iv_rank']:.2f}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating options indicators: {e}")
            return {}
    
    def save_indicators(self, indicators: Dict):
        """Save indicators to database"""
        if not indicators:
            return
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO options_market_indicators (
                timestamp, nifty_spot, nifty_fut,
                pcr_all, pcr_oi, pcr_volume,
                max_pain_nifty,
                atm_call_iv, atm_put_iv, iv_rank,
                total_ce_oi, total_pe_oi, oi_change_ce, oi_change_pe,
                call_resistance, put_support
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (timestamp) DO UPDATE SET
                nifty_spot = EXCLUDED.nifty_spot,
                pcr_oi = EXCLUDED.pcr_oi,
                max_pain_nifty = EXCLUDED.max_pain_nifty,
                iv_rank = EXCLUDED.iv_rank
        """, (
            indicators['timestamp'],
            indicators.get('nifty_spot', 0),
            indicators.get('nifty_fut', 0),
            indicators.get('pcr_all', 0),
            indicators.get('pcr_oi', 0),
            indicators.get('pcr_volume', 0),
            indicators.get('max_pain_nifty', 0),
            indicators.get('atm_call_iv', 0),
            indicators.get('atm_put_iv', 0),
            indicators.get('iv_rank', 0),
            indicators.get('total_ce_oi', 0),
            indicators.get('total_pe_oi', 0),
            indicators.get('oi_change_ce', 0),
            indicators.get('oi_change_pe', 0),
            indicators.get('call_resistance', 0),
            indicators.get('put_support', 0)
        ))
        
        self.conn.commit()
        cursor.close()
        logger.info("Options indicators saved to database")


if __name__ == "__main__":
    # Test the indicators
    calc = OptionsIndicators()
    indicators = calc.calculate_all_indicators("NIFTY")
    
    print("\n=== NIFTY OPTIONS INDICATORS ===")
    print(f"Spot Price: ₹{indicators.get('nifty_spot', 0):,.2f}")
    print(f"PCR (OI): {indicators.get('pcr_oi', 0):.4f}")
    print(f"PCR (Volume): {indicators.get('pcr_volume', 0):.4f}")
    print(f"Max Pain: ₹{indicators.get('max_pain_nifty', 0):,.2f}")
    print(f"IV Rank: {indicators.get('iv_rank', 0):.2f}%")
    print(f"ATM Call IV: {indicators.get('atm_call_iv', 0):.4f}")
    print(f"ATM Put IV: {indicators.get('atm_put_iv', 0):.4f}")
    print(f"Call Resistance: ₹{indicators.get('call_resistance', 0):,.2f}")
    print(f"Put Support: ₹{indicators.get('put_support', 0):,.2f}")
    
    # Save to database
    calc.save_indicators(indicators)
