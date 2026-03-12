"""Opening Range Breakout Strategy"""
import pandas as pd
from typing import Optional
from datetime import time
from services.strategy.base_strategy import BaseStrategy, TradeSignal, SignalType
from config.logger import setup_logger

logger = setup_logger("orb_strategy")

class OpeningRangeBreakoutStrategy(BaseStrategy):
    """
    Opening Range Breakout (ORB) Strategy
    
    Logic:
    1. Identify opening range (first 15 minutes: 9:15 - 9:30)
    2. Mark high and low of opening range
    3. Entry on breakout above/below range with volume
    4. Target: 1.5x range distance
    5. Stop Loss: Opposite end of range
    
    Best for: Index futures, high-volume stocks
    Timeframe: 5-minute candles
    """
    
    def __init__(self):
        super().__init__(name="Opening_Range_Breakout", timeframe="5m")
        self.opening_range_minutes = 15
        self.breakout_threshold = 0.002  # 0.2% above/below range
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate ORB signal"""
        if len(data) < 20:
            return None
        
        # Identify opening range
        or_high, or_low = self._get_opening_range(data)
        
        if or_high is None or or_low is None:
            return None
        
        latest = data.iloc[-1]
        symbol = latest.get('symbol', 'UNKNOWN')
        close = latest['close']
        
        range_height = or_high - or_low
        
        # BUY on upside breakout
        if close > or_high * (1 + self.breakout_threshold):
            if not self._volume_confirmation(data):
                return None
            
            entry_price = close
            stop_loss = or_low
            target_price = close + (range_height * 1.5)
            
            confidence = self._calculate_confidence(data, 'BUY', or_high, or_low)
            
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target_price=target_price,
                confidence=confidence,
                strategy_name=self.name,
                timeframe=self.timeframe,
                reason=f"Opening range breakout above {or_high:.2f}"
            )
        
        # SELL on downside breakdown
        elif close < or_low * (1 - self.breakout_threshold):
            if not self._volume_confirmation(data):
                return None
            
            entry_price = close
            stop_loss = or_high
            target_price = close - (range_height * 1.5)
            
            confidence = self._calculate_confidence(data, 'SELL', or_high, or_low)
            
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target_price=target_price,
                confidence=confidence,
                strategy_name=self.name,
                timeframe=self.timeframe,
                reason=f"Opening range breakdown below {or_low:.2f}"
            )
        
        return None
    
    def validate_conditions(self, data: pd.DataFrame) -> bool:
        """Validate market conditions"""
        if 'timestamp' not in data.columns:
            return False
        
        # Check if we have passed opening range period
        latest_time = pd.to_datetime(data.iloc[-1]['timestamp']).time()
        market_open = time(9, 15)
        or_end = time(9, 30)
        
        # Only trade after opening range is formed
        if latest_time < or_end:
            return False
        
        return True
    
    def _get_opening_range(self, data: pd.DataFrame) -> tuple:
        """Get opening range high and low"""
        try:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data['time'] = data['timestamp'].dt.time
            
            # Filter for opening range (9:15 - 9:30)
            or_data = data[
                (data['time'] >= time(9, 15)) & 
                (data['time'] <= time(9, 30))
            ]
            
            if or_data.empty:
                return None, None
            
            or_high = or_data['high'].max()
            or_low = or_data['low'].min()
            
            return or_high, or_low
            
        except Exception as e:
            logger.error(f"Error calculating opening range: {e}")
            return None, None
    
    def _volume_confirmation(self, data: pd.DataFrame) -> bool:
        """Check if volume confirms breakout"""
        latest = data.iloc[-1]
        avg_volume = data['volume'].tail(20).mean()
        
        return latest['volume'] > avg_volume * 1.3
    
    def _calculate_confidence(self, data: pd.DataFrame, signal_type: str, 
                            or_high: float, or_low: float) -> float:
        """Calculate confidence score"""
        score = 60.0
        
        latest = data.iloc[-1]
        
        # Strong volume = higher confidence
        avg_volume = data['volume'].tail(20).mean()
        if latest['volume'] > avg_volume * 1.5:
            score += 20
        elif latest['volume'] > avg_volume * 1.2:
            score += 10
        
        # Range size matters (bigger range = better)
        range_pct = ((or_high - or_low) / or_low) * 100
        if range_pct > 1.0:
            score += 15
        elif range_pct > 0.5:
            score += 10
        
        # Trend alignment
        if 'ema_9' in data.columns and 'ema_21' in data.columns:
            if signal_type == 'BUY' and latest['ema_9'] > latest['ema_21']:
                score += 5
            elif signal_type == 'SELL' and latest['ema_9'] < latest['ema_21']:
                score += 5
        
        return min(score, 100.0)
