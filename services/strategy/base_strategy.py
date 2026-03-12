"""Base Strategy Class - All strategies inherit from this"""
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    EXIT = "EXIT"

@dataclass
class TradeSignal:
    """Trading signal data structure"""
    symbol: str
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    target_price: float
    confidence: float
    strategy_name: str
    timeframe: str
    reason: str
    quantity: int = 0

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str, timeframe: str = "1d"):
        self.name = name
        self.timeframe = timeframe
        self.min_data_points = 50
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Optional[TradeSignal]:
        """
        Generate trading signal based on strategy logic
        
        Args:
            data: DataFrame with OHLC and indicators
        
        Returns:
            TradeSignal or None
        """
        pass
    
    @abstractmethod
    def validate_conditions(self, data: pd.DataFrame) -> bool:
        """
        Validate if current market conditions are suitable for this strategy
        
        Args:
            data: DataFrame with OHLC and indicators
        
        Returns:
            True if conditions are met
        """
        pass
    
    def calculate_position_size(
        self,
        capital: float,
        risk_percent: float,
        entry_price: float,
        stop_loss: float
    ) -> int:
        """
        Calculate position size based on risk management
        
        Args:
            capital: Available capital
            risk_percent: Risk per trade (e.g., 1.0 for 1%)
            entry_price: Entry price
            stop_loss: Stop loss price
        
        Returns:
            Number of shares/contracts
        """
        risk_amount = capital * (risk_percent / 100)
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
        
        quantity = int(risk_amount / price_diff)
        return quantity
    
    def calculate_risk_reward(self, entry: float, stop_loss: float, target: float) -> float:
        """Calculate risk-reward ratio"""
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        
        if risk == 0:
            return 0
        
        return reward / risk
    
    def is_bullish_trend(self, data: pd.DataFrame) -> bool:
        """Check if market is in bullish trend"""
        if 'ema_9' not in data.columns or 'ema_21' not in data.columns:
            return False
        
        latest = data.iloc[-1]
        return latest['ema_9'] > latest['ema_21'] and latest['close'] > latest['ema_9']
    
    def is_bearish_trend(self, data: pd.DataFrame) -> bool:
        """Check if market is in bearish trend"""
        if 'ema_9' not in data.columns or 'ema_21' not in data.columns:
            return False
        
        latest = data.iloc[-1]
        return latest['ema_9'] < latest['ema_21'] and latest['close'] < latest['ema_9']
