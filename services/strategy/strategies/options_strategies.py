"""
Nifty 50 Options Trading Strategies
- Opening Range Breakout (Options)
- Volatility Spike Strategy  
- OI Buildup Momentum Strategy
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import pandas as pd
from decimal import Decimal
from config.logger import setup_logger
from services.indicators.options_indicators import OptionsIndicators

logger = setup_logger("options_strategies")


class OptionsStrategyBase:
    """Base class for options trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.options_calc = OptionsIndicators()
    
    def generate_signal(self, symbol: str = "NIFTY") -> Optional[Dict]:
        """
        Generate trading signal
        
        Returns:
            Signal dict or None if no signal
        """
        raise NotImplementedError("Subclasses must implement generate_signal")
    
    def calculate_confidence(self, conditions: Dict) -> float:
        """Calculate signal confidence based on conditions met"""
        raise NotImplementedError("Subclasses must implement calculate_confidence")


class OpeningRangeBreakoutOptions(OptionsStrategyBase):
    """
    Opening Range Breakout Strategy for Nifty Options
    
    Entry Rules:
    - Wait for first 15 minutes (9:15-9:30)
    - If Nifty breaks above OR High by 0.3%: BUY CE
    - If Nifty breaks below OR Low by 0.3%: BUY PE
    
    Strike Selection:
    - Use ATM or slightly OTM (50-100 points)
    
    Exit Rules:
    - Target: +60% premium
    - Stop Loss: -40% premium
    - Time: Exit by 3:00 PM
    """
    
    def __init__(self):
        super().__init__("ORB_Options")
        self.or_high = None
        self.or_low = None
        self.or_captured = False
    
    def capture_opening_range(self, symbol: str = "NIFTY") -> bool:
        """Capture opening range (9:15-9:30 AM)"""
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        or_end = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        if market_open <= now <= or_end:
            # Capture high/low from OHLC data
            cursor = self.options_calc.conn.cursor()
            cursor.execute("""
                SELECT MAX(high), MIN(low)
                FROM market_ohlc
                WHERE symbol = %s 
                    AND timeframe = '5m'
                    AND timestamp >= %s
            """, (symbol, market_open))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                self.or_high = float(result[0])
                self.or_low = float(result[1])
                self.or_captured = True
                logger.info(f"OR Captured: High={self.or_high}, Low={self.or_low}")
                return True
        
        return False
    
    def generate_signal(self, symbol: str = "NIFTY") -> Optional[Dict]:
        """Generate ORB options signal"""
        now = datetime.now()
        
        # Only trade between 9:30 AM and 2:30 PM
        if now.hour < 9 or (now.hour == 9 and now.minute < 30) or now.hour >= 14:
            return None
        
        # Capture OR if not done
        if not self.or_captured:
            self.capture_opening_range(symbol)
            return None
        
        # Get current spot price
        spot = self.options_calc.get_spot_price(symbol)
        if spot == 0:
            return None
        
        # Check for breakout
        breakout_threshold = 0.003  # 0.3%
        or_range = self.or_high - self.or_low
        
        signal = None
        
        # BULLISH BREAKOUT - Buy CE
        if spot > self.or_high * (1 + breakout_threshold):
            atm_strike = self.options_calc.get_atm_strike(symbol)
            strike = atm_strike  # ATM strike for ORB
            option_type = "CE"
            
            # Get option premium
            df = self.options_calc.get_options_chain(symbol)
            option_data = df[(df['strike'] == strike) & (df['option_type'] == option_type)]
            
            if not option_data.empty:
                premium = float(option_data.iloc[0]['ltp'])
                iv = float(option_data.iloc[0]['iv'])
                
                conditions = {
                    'breakout_confirmed': spot > self.or_high * 1.003,
                    'wide_range': or_range > spot * 0.01,  # > 1% range
                    'moderate_iv': 10 < iv < 40,  # Not too high/low IV
                    'liquid_option': premium > 10,  # Premium > ₹10
                }
                
                confidence = self.calculate_confidence(conditions)
                
                if confidence >= 70:
                    signal = {
                        'strategy': self.name,
                        'symbol': symbol,
                        'strike': strike,
                        'option_type': option_type,
                        'signal_type': 'BUY',
                        'entry_premium': premium,
                        'stop_loss_premium': premium * 0.6,  # -40% SL
                        'target_premium': premium * 1.6,  # +60% target
                        'confidence': confidence,
                        'quantity': 1,  # 1 lot
                        'reason': f"ORB Bullish Breakout - Spot {spot} > OR High {self.or_high}",
                        'entry_iv': iv,
                        'spot_price': spot,
                        'strike_type': 'ATM'
                    }
        
        # BEARISH BREAKDOWN - Buy PE
        elif spot < self.or_low * (1 - breakout_threshold):
            atm_strike = self.options_calc.get_atm_strike(symbol)
            strike = atm_strike  # ATM strike for ORB
            option_type = "PE"
            
            df = self.options_calc.get_options_chain(symbol)
            option_data = df[(df['strike'] == strike) & (df['option_type'] == option_type)]
            
            if not option_data.empty:
                premium = float(option_data.iloc[0]['ltp'])
                iv = float(option_data.iloc[0]['iv'])
                
                conditions = {
                    'breakdown_confirmed': spot < self.or_low * 0.997,
                    'wide_range': or_range > spot * 0.01,
                    'moderate_iv': 10 < iv < 40,
                    'liquid_option': premium > 10,
                }
                
                confidence = self.calculate_confidence(conditions)
                
                if confidence >= 70:
                    signal = {
                        'strategy': self.name,
                        'symbol': symbol,
                        'strike': strike,
                        'option_type': option_type,
                        'signal_type': 'BUY',
                        'entry_premium': premium,
                        'stop_loss_premium': premium * 0.6,
                        'target_premium': premium * 1.6,
                        'confidence': confidence,
                        'quantity': 1,
                        'reason': f"ORB Bearish Breakdown - Spot {spot} < OR Low {self.or_low}",
                        'entry_iv': iv,
                        'spot_price': spot,
                        'strike_type': 'ATM'
                    }
        
        return signal
    
    def calculate_confidence(self, conditions: Dict) -> float:
        """Calculate confidence score"""
        base = 50
        
        if conditions.get('breakout_confirmed') or conditions.get('breakdown_confirmed'):
            base += 20
        if conditions.get('wide_range'):
            base += 15
        if conditions.get('moderate_iv'):
            base += 10
        if conditions.get('liquid_option'):
            base += 5
        
        return min(base, 100)


class VolatilitySpikeStrategy(OptionsStrategyBase):
    """
    IV Spike Strategy - Buy options when volatility spikes
    
    Entry Rules:
    - IV Rank > 70 (high volatility)
    - PCR > 1.2 or < 0.8 (extreme sentiment)
    - Buy options in direction of trend
    
    Strike Selection:
    - Slightly OTM (50-100 points from ATM)
    
    Exit Rules:
    - Target: +80% premium
    - Stop Loss: -50% premium
    - Exit if IV drops below 50 rank
    """
    
    def __init__(self):
        super().__init__("IV_Spike")
    
    def generate_signal(self, symbol: str = "NIFTY") -> Optional[Dict]:
        """Generate IV spike signal"""
        now = datetime.now()
        
        # Trade hours: 9:30 AM - 2:30 PM
        if now.hour < 9 or (now.hour == 9 and now.minute < 30) or now.hour >= 14:
            return None
        
        # Get options indicators
        indicators = self.options_calc.calculate_all_indicators(symbol)
        
        if not indicators:
            return None
        
        iv_rank = indicators.get('iv_rank', 0)
        pcr_oi = indicators.get('pcr_oi', 1)
        spot = indicators.get('nifty_spot', 0)
        atm_strike = self.options_calc.get_atm_strike(symbol)
        
        signal = None
        
        # HIGH IV + Bullish sentiment (low PCR) = Buy CE
        if iv_rank > 60 and pcr_oi < 0.8:
            strike = atm_strike + 100  # OTM CE
            option_type = "CE"
            
            df = self.options_calc.get_options_chain(symbol)
            option_data = df[(df['strike'] == strike) & (df['option_type'] == option_type)]
            
            if not option_data.empty:
                premium = float(option_data.iloc[0]['ltp'])
                iv = float(option_data.iloc[0]['iv'])
                oi = int(option_data.iloc[0]['oi'])
                
                conditions = {
                    'high_iv': iv_rank > 70,
                    'extreme_pcr': pcr_oi < 0.75,
                    'decent_premium': 20 < premium < 200,
                    'high_oi': oi > 100000
                }
                
                confidence = self.calculate_confidence(conditions)
                
                if confidence >= 70:
                    signal = {
                        'strategy': self.name,
                        'symbol': symbol,
                        'strike': strike,
                        'option_type': option_type,
                        'signal_type': 'BUY',
                        'entry_premium': premium,
                        'stop_loss_premium': premium * 0.5,  # -50% SL
                        'target_premium': premium * 1.8,  # +80% target
                        'confidence': confidence,
                        'quantity': 1,
                        'reason': f"IV Spike Bullish - IV Rank {iv_rank:.1f}, PCR {pcr_oi:.4f}",
                        'entry_iv': iv,
                        'spot_price': spot,
                        'strike_type': 'OTM',
                        'pcr_ratio': pcr_oi,
                        'iv_rank': iv_rank
                    }
        
        # HIGH IV + Bearish sentiment (high PCR) = Buy PE
        elif iv_rank > 60 and pcr_oi > 1.2:
            strike = atm_strike - 100  # OTM PE
            option_type = "PE"
            
            df = self.options_calc.get_options_chain(symbol)
            option_data = df[(df['strike'] == strike) & (df['option_type'] == option_type)]
            
            if not option_data.empty:
                premium = float(option_data.iloc[0]['ltp'])
                iv = float(option_data.iloc[0]['iv'])
                oi = int(option_data.iloc[0]['oi'])
                
                conditions = {
                    'high_iv': iv_rank > 70,
                    'extreme_pcr': pcr_oi > 1.25,
                    'decent_premium': 20 < premium < 200,
                    'high_oi': oi > 100000
                }
                
                confidence = self.calculate_confidence(conditions)
                
                if confidence >= 70:
                    signal = {
                        'strategy': self.name,
                        'symbol': symbol,
                        'strike': strike,
                        'option_type': option_type,
                        'signal_type': 'BUY',
                        'entry_premium': premium,
                        'stop_loss_premium': premium * 0.5,
                        'target_premium': premium * 1.8,
                        'confidence': confidence,
                        'quantity': 1,
                        'reason': f"IV Spike Bearish - IV Rank {iv_rank:.1f}, PCR {pcr_oi:.4f}",
                        'entry_iv': iv,
                        'spot_price': spot,
                        'strike_type': 'OTM',
                        'pcr_ratio': pcr_oi,
                        'iv_rank': iv_rank
                    }
        
        return signal
    
    def calculate_confidence(self, conditions: Dict) -> float:
        """Calculate confidence score"""
        base = 55
        
        if conditions.get('high_iv'):
            base += 20
        if conditions.get('extreme_pcr'):
            base += 15
        if conditions.get('decent_premium'):
            base += 5
        if conditions.get('high_oi'):
            base += 5
        
        return min(base, 100)


class OIBuildupStrategy(OptionsStrategyBase):
    """
    Open Interest Buildup Strategy
    
    Entry Rules:
    - Detect significant OI buildup at a strike (> 20% increase)
    - Price moving towards that strike
    - Buy options in direction of OI buildup
    
    Strike Selection:
    - Strikes with highest OI change
    
    Exit Rules:
    - Target: +70% premium
    - Stop Loss: -45% premium
    """
    
    def __init__(self):
        super().__init__("OI_Buildup")
    
    def generate_signal(self, symbol: str = "NIFTY") -> Optional[Dict]:
        """Generate OI buildup signal"""
        now = datetime.now()
        
        if now.hour < 9 or (now.hour == 9 and now.minute < 30) or now.hour >= 14:
            return None
        
        df = self.options_calc.get_options_chain(symbol)
        
        if df.empty:
            return None
        
        spot = self.options_calc.get_spot_price(symbol)
        
        # Find strikes with significant OI buildup
        df['oi_change_pct'] = (df['oi_change'] / df['oi']) * 100
        
        # CE buildup (bullish)
        ce_df = df[df['option_type'] == 'CE'].sort_values('oi_change', ascending=False)
        
        # PE buildup (bearish)
        pe_df = df[df['option_type'] == 'PE'].sort_values('oi_change', ascending=False)
        
        signal = None
        
        # Strong CE OI buildup = Bullish
        if not ce_df.empty:
            top_ce = ce_df.iloc[0]
            oi_change = int(top_ce['oi_change'])
            
            if oi_change > 0 and top_ce['oi_change_pct'] > 15:  # 15% OI increase
                strike = float(top_ce['strike'])
                premium = float(top_ce['ltp'])
                iv = float(top_ce['iv'])
                
                conditions = {
                    'significant_oi_change': top_ce['oi_change_pct'] > 20,
                    'strike_near_spot': abs(strike - spot) < 200,
                    'decent_premium': premium > 15,
                    'moderate_iv': iv < 35
                }
                
                confidence = self.calculate_confidence(conditions)
                
                if confidence >= 70:
                    signal = {
                        'strategy': self.name,
                        'symbol': symbol,
                        'strike': strike,
                        'option_type': 'CE',
                        'signal_type': 'BUY',
                        'entry_premium': premium,
                        'stop_loss_premium': premium * 0.55,
                        'target_premium': premium * 1.7,
                        'confidence': confidence,
                        'quantity': 1,
                        'reason': f"CE OI Buildup at {strike} - {oi_change:,} contracts",
                        'entry_iv': iv,
                        'spot_price': spot,
                        'strike_type': self.options_calc.classify_strike(strike, symbol, 'CE'),
                        'oi_buildup': oi_change
                    }
        
        # Strong PE OI buildup = Bearish (only if no CE signal)
        if signal is None and not pe_df.empty:
            top_pe = pe_df.iloc[0]
            oi_change = int(top_pe['oi_change'])
            
            if oi_change > 0 and top_pe['oi_change_pct'] > 15:
                strike = float(top_pe['strike'])
                premium = float(top_pe['ltp'])
                iv = float(top_pe['iv'])
                
                conditions = {
                    'significant_oi_change': top_pe['oi_change_pct'] > 20,
                    'strike_near_spot': abs(strike - spot) < 200,
                    'decent_premium': premium > 15,
                    'moderate_iv': iv < 35
                }
                
                confidence = self.calculate_confidence(conditions)
                
                if confidence >= 70:
                    signal = {
                        'strategy': self.name,
                        'symbol': symbol,
                        'strike': strike,
                        'option_type': 'PE',
                        'signal_type': 'BUY',
                        'entry_premium': premium,
                        'stop_loss_premium': premium * 0.55,
                        'target_premium': premium * 1.7,
                        'confidence': confidence,
                        'quantity': 1,
                        'reason': f"PE OI Buildup at {strike} - {oi_change:,} contracts",
                        'entry_iv': iv,
                        'spot_price': spot,
                        'strike_type': self.options_calc.classify_strike(strike, symbol, 'PE'),
                        'oi_buildup': oi_change
                    }
        
        return signal
    
    def calculate_confidence(self, conditions: Dict) -> float:
        """Calculate confidence score"""
        base = 55
        
        if conditions.get('significant_oi_change'):
            base += 20
        if conditions.get('strike_near_spot'):
            base += 15
        if conditions.get('decent_premium'):
            base += 5
        if conditions.get('moderate_iv'):
            base += 5
        
        return min(base, 100)


# Factory to get all strategies
def get_all_options_strategies() -> List[OptionsStrategyBase]:
    """Get all options strategies"""
    return [
        OpeningRangeBreakoutOptions(),
        VolatilitySpikeStrategy(),
        OIBuildupStrategy()
    ]


if __name__ == "__main__":
    # Test strategies
    strategies = get_all_options_strategies()
    
    print("=== TESTING OPTIONS STRATEGIES ===\n")
    
    for strategy in strategies:
        print(f"\n{strategy.name}:")
        signal = strategy.generate_signal("NIFTY")
        
        if signal:
            print(f"  Signal: {signal['signal_type']} {signal['option_type']} @ Strike {signal['strike']}")
            print(f"  Premium: ₹{signal['entry_premium']:.2f}")
            print(f"  Target: ₹{signal['target_premium']:.2f}")
            print(f"  SL: ₹{signal['stop_loss_premium']:.2f}")
            print(f"  Confidence: {signal['confidence']:.1f}%")
            print(f"  Reason: {signal['reason']}")
        else:
            print("  No signal generated")
