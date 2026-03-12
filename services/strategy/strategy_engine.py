"""Strategy Engine - Orchestrates all trading strategies"""
import pandas as pd
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from config.database import get_db_context
from config.logger import setup_logger
from services.strategy.base_strategy import TradeSignal
from services.strategy.strategies.vwap_trap_strategy import VWAPTrapStrategy
from services.strategy.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

logger = setup_logger("strategy_engine")

class StrategyEngine:
    """Manages and executes all trading strategies"""
    
    def __init__(self):
        self.strategies = [
            VWAPTrapStrategy(timeframe="15m"),
            VWAPTrapStrategy(timeframe="1h"),
            OpeningRangeBreakoutStrategy(),
        ]
        logger.info(f"Initialized {len(self.strategies)} strategies")
    
    def scan_market(self, symbols: List[str]) -> List[TradeSignal]:
        """
        Scan market for all signals across all strategies
        
        Args:
            symbols: List of symbols to scan
        
        Returns:
            List of trade signals
        """
        all_signals = []
        
        for symbol in symbols:
            for strategy in self.strategies:
                try:
                    # Fetch data with indicators
                    data = self._fetch_market_data_with_indicators(
                        symbol,
                        strategy.timeframe
                    )
                    
                    if data.empty:
                        continue
                    
                    # Generate signal
                    signal = strategy.generate_signal(data)
                    
                    if signal:
                        # Calculate position size
                        signal.quantity = strategy.calculate_position_size(
                            capital=100000,  # 1 Lakh
                            risk_percent=1.0,  # 1% risk per trade
                            entry_price=signal.entry_price,
                            stop_loss=signal.stop_loss
                        )
                        
                        all_signals.append(signal)
                        logger.info(f"Signal generated: {signal.symbol} {signal.signal_type.value} by {signal.strategy_name}")
                
                except Exception as e:
                    logger.error(f"Error scanning {symbol} with {strategy.name}: {e}")
        
        # Rank signals by confidence
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return all_signals
    
    def _fetch_market_data_with_indicators(
        self, 
        symbol: str, 
        timeframe: str,
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch OHLC data joined with indicators"""
        try:
            with get_db_context() as db:
                query = text("""
                    SELECT 
                        o.timestamp,
                        o.symbol,
                        o.open,
                        o.high,
                        o.low,
                        o.close,
                        o.volume,
                        o.vwap,
                        i.rsi,
                        i.macd,
                        i.macd_signal,
                        i.ema_9,
                        i.ema_21,
                        i.ema_50,
                        i.atr,
                        i.bb_upper,
                        i.bb_lower,
                        i.supertrend,
                        i.supertrend_direction
                    FROM market_ohlc o
                    LEFT JOIN indicators i ON 
                        o.timestamp = i.timestamp AND 
                        o.symbol = i.symbol AND 
                        o.timeframe = i.timeframe
                    WHERE o.symbol = :symbol 
                      AND o.timeframe = :timeframe
                    ORDER BY o.timestamp DESC
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
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def save_signals(self, signals: List[TradeSignal]) -> int:
        """Save generated signals to database"""
        if not signals:
            return 0
        
        try:
            with get_db_context() as db:
                insert_query = text("""
                    INSERT INTO signals (
                        timestamp, symbol, strategy, signal_type, timeframe,
                        entry_price, stop_loss, target_price, confidence, quantity, reason
                    )
                    VALUES (
                        :timestamp, :symbol, :strategy, :signal_type, :timeframe,
                        :entry_price, :stop_loss, :target_price, :confidence, :quantity, :reason
                    )
                """)
                
                records = []
                for signal in signals:
                    records.append({
                        'timestamp': datetime.now(),
                        'symbol': signal.symbol,
                        'strategy': signal.strategy_name,
                        'signal_type': signal.signal_type.value,
                        'timeframe': signal.timeframe,
                        'entry_price': signal.entry_price,
                        'stop_loss': signal.stop_loss,
                        'target_price': signal.target_price,
                        'confidence': signal.confidence,
                        'quantity': signal.quantity,
                        'reason': signal.reason
                    })
                
                db.execute(insert_query, records)
                logger.info(f"Saved {len(records)} signals to database")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error saving signals: {e}")
            return 0
    
    def run_pre_market_scan(self, symbols: List[str]):
        """Run pre-market strategy scan"""
        logger.info("=== Running Pre-Market Strategy Scan ===")
        
        signals = self.scan_market(symbols)
        
        logger.info(f"Generated {len(signals)} signals")
        
        # Display top signals
        for i, signal in enumerate(signals[:5], 1):
            logger.info(f"{i}. {signal.symbol} - {signal.signal_type.value} "
                       f"@ {signal.entry_price:.2f} (Confidence: {signal.confidence:.1f}%)")
        
        # Save to database
        self.save_signals(signals)
        
        return signals

# CLI execution
if __name__ == "__main__":
    engine = StrategyEngine()
    
    # Run scan for top stocks
    nifty_50 = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    signals = engine.run_pre_market_scan(nifty_50)
