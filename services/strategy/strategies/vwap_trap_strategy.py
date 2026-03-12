"""VWAP Trap Strategy - Price bounce off VWAP with confirmation"""
import pandas as pd
from typing import Optional
from services.strategy.base_strategy import BaseStrategy, TradeSignal, SignalType
from config.logger import setup_logger

logger = setup_logger("vwap_trap_strategy")

class VWAPTrapStrategy(BaseStrategy):
    """
    VWAP Trap Strategy
    
    Entry Conditions (BUY):
    1. Price dips below VWAP
    2. RSI < 40 (oversold)
    3. Price bounces back above VWAP with volume
    4. EMA 9 > EMA 21 (trend confirmation)
    
    Entry Conditions (SELL):
    1. Price goes above VWAP
    2. RSI > 60 (overbought)
    3. Price falls back below VWAP with volume
    4. EMA 9 < EMA 21 (trend confirmation)
    
    Exit:
    - Target: 1.5x ATR from entry
    - Stop Loss: VWAP or 1x ATR (whichever is closer)
    """
    
    def __init__(self, timeframe: str = "15m"):
        super().__init__(name="VWAP_Trap", timeframe=timeframe)
        self.min_data_points = 50
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate signal based on VWAP trap logic"""
        if len(data) < self.min_data_points:
            logger.debug(f"Insufficient data: {len(data)} rows")
            return None
        
        if not self.validate_conditions(data):
            return None
        
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        symbol = latest.get('symbol', 'UNKNOWN')
        close = latest['close']
        vwap = latest['vwap']
        rsi = latest['rsi']
        atr = latest['atr']
        
        # BUY Signal: Bounce from below VWAP
        if (prev['close'] < prev['vwap'] and 
            close > vwap and 
            rsi < 40 and 
            self.is_bullish_trend(data)):
            
            entry_price = close
            stop_loss = max(vwap - atr, close - (1.5 * atr))
            target_price = close + (2 * atr)
            
            confidence = self._calculate_confidence(data, signal_type='BUY')
            
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target_price=target_price,
                confidence=confidence,
                strategy_name=self.name,
                timeframe=self.timeframe,
                reason="VWAP bounce with RSI oversold and bullish trend"
            )
        
        # SELL Signal: Rejection from above VWAP
        elif (prev['close'] > prev['vwap'] and 
              close < vwap and 
              rsi > 60 and 
              self.is_bearish_trend(data)):
            
            entry_price = close
            stop_loss = min(vwap + atr, close + (1.5 * atr))
            target_price = close - (2 * atr)
            
            confidence = self._calculate_confidence(data, signal_type='SELL')
            
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target_price=target_price,
                confidence=confidence,
                strategy_name=self.name,
                timeframe=self.timeframe,
                reason="VWAP rejection with RSI overbought and bearish trend"
            )
        
        return None
    
    def validate_conditions(self, data: pd.DataFrame) -> bool:
        """Validate if market conditions are suitable"""
        required_cols = ['close', 'vwap', 'rsi', 'atr', 'ema_9', 'ema_21', 'volume']
        
        if not all(col in data.columns for col in required_cols):
            logger.debug("Missing required columns")
            return False
        
        # Check for NaN values in latest row
        latest = data.iloc[-1]
        if latest[required_cols].isna().any():
            logger.debug("NaN values in latest data")
            return False
        
        # Volume confirmation - current volume should be above average
        avg_volume = data['volume'].tail(20).mean()
        if latest['volume'] < avg_volume * 0.8:
            logger.debug("Insufficient volume")
            return False
        
        return True
    
    def _calculate_confidence(self, data: pd.DataFrame, signal_type: str) -> float:
        """Calculate confidence score (0-100)"""
        latest = data.iloc[-1]
        score = 50.0  # Base score
        
        # Volume confirmation
        avg_volume = data['volume'].tail(20).mean()
        if latest['volume'] > avg_volume * 1.2:
            score += 15
        
        # Strong trend confirmation
        if signal_type == 'BUY':
            if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                score += 20
            if latest['rsi'] < 30:  # Very oversold
                score += 10
        else:
            if latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                score += 20
            if latest['rsi'] > 70:  # Very overbought
                score += 10
        
        # MACD confirmation
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            if signal_type == 'BUY' and latest['macd'] > latest['macd_signal']:
                score += 5
            elif signal_type == 'SELL' and latest['macd'] < latest['macd_signal']:
                score += 5
        
        return min(score, 100.0)
