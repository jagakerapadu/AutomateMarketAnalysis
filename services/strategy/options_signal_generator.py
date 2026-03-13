"""
Options Signal Generator - Scans and generates options trading signals
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone
from typing import Dict, List
import psycopg2
from config.settings import get_settings
from config.logger import setup_logger
from services.strategy.strategies.options_strategies import get_all_options_strategies

logger = setup_logger("options_signal_generator")
settings = get_settings()


class OptionsSignalGenerator:
    """Generate options trading signals from all strategies"""
    
    def __init__(self):
        self.conn = self._get_db_connection()
        self.strategies = get_all_options_strategies()
        logger.info(f"Loaded {len(self.strategies)} options strategies")
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
    
    def get_next_expiry(self, symbol: str = "NIFTY") -> str:
        """Get next weekly expiry date"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT expiry_date
            FROM options_chain
            WHERE symbol = %s AND expiry_date >= CURRENT_DATE
            ORDER BY expiry_date LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return result[0].strftime('%Y-%m-%d')
        return None
    
    def generate_all_signals(self, symbol: str = "NIFTY") -> List[Dict]:
        """Run all strategies and generate signals"""
        signals = []
        expiry = self.get_next_expiry(symbol)
        
        if not expiry:
            logger.warning(f"No expiry date found for {symbol}")
            return []
        
        logger.info(f"Generating options signals for {symbol}, expiry: {expiry}")
        
        for strategy in self.strategies:
            try:
                signal = strategy.generate_signal(symbol)
                
                if signal:
                    # Add expiry and timestamps
                    signal['expiry_date'] = expiry
                    signal['timestamp'] = datetime.now(timezone.utc)
                    
                    # Calculate risk/reward
                    entry_premium = signal['entry_premium']
                    target_premium = signal['target_premium']
                    sl_premium = signal['stop_loss_premium']
                    
                    risk = entry_premium - sl_premium
                    reward = target_premium - entry_premium
                    
                    signal['risk_amount'] = abs(risk) * signal['quantity'] * 50  # Lot size = 50
                    signal['reward_amount'] = reward * signal['quantity'] * 50
                    signal['risk_reward_ratio'] = round(reward / risk if risk > 0 else 0, 2)
                    
                    # Classify strike
                    signal['strike_distance'] = abs(signal['strike'] - signal['spot_price'])
                    
                    signals.append(signal)
                    
                    logger.info(f"{strategy.name}: {signal['option_type']} {signal['strike']} @ Rs.{entry_premium:.2f} (Conf: {signal['confidence']:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error in {strategy.name}: {e}")
        
        logger.info(f"Generated {len(signals)} options signals")
        return signals
    
    def save_signals(self, signals: List[Dict]):
        """Save signals to database"""
        if not signals:
            return
        
        cursor = self.conn.cursor()
        
        for signal in signals:
            try:
                cursor.execute("""
                    INSERT INTO options_signals (
                        timestamp, symbol, strike, option_type, expiry_date,
                        signal_type, strategy, entry_premium, stop_loss_premium, target_premium,
                        confidence, quantity, current_spot_price, strike_distance, strike_type,
                        entry_iv, pcr_ratio, oi_buildup, risk_amount, reward_amount, risk_reward_ratio,
                        reason, status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    signal['timestamp'],
                    signal['symbol'],
                    signal['strike'],
                    signal['option_type'],
                    signal['expiry_date'],
                    signal['signal_type'],
                    signal['strategy'],
                    signal['entry_premium'],
                    signal['stop_loss_premium'],
                    signal['target_premium'],
                    signal['confidence'],
                    signal['quantity'],
                    signal.get('spot_price', 0),
                    signal.get('strike_distance', 0),
                    signal.get('strike_type', 'ATM'),
                    signal.get('entry_iv', 0),
                    signal.get('pcr_ratio', None),
                    signal.get('oi_buildup', None),
                    signal.get('risk_amount', 0),
                    signal.get('reward_amount', 0),
                    signal.get('risk_reward_ratio', 0),
                    signal['reason'],
                    'PENDING'
                ))
                
                signal_id = cursor.fetchone()[0]
                signal['id'] = signal_id
                
            except Exception as e:
                logger.error(f"Error saving signal: {e}")
        
        self.conn.commit()
        cursor.close()
        
        logger.info(f"Saved {len(signals)} signals to database")
    
    def scan_and_save(self, symbol: str = "NIFTY") -> List[Dict]:
        """Complete workflow: scan and save signals"""
        signals = self.generate_all_signals(symbol)
        
        if signals:
            self.save_signals(signals)
        
        return signals


if __name__ == "__main__":
    # Test signal generation
    generator = OptionsSignalGenerator()
    signals = generator.scan_and_save("NIFTY")
    
    print(f"\n=== GENERATED {len(signals)} OPTIONS SIGNALS ===\n")
    
    for signal in signals:
        print(f"{signal['strategy']}: {signal['signal_type']} {signal['option_type']} @ {signal['strike']}")
        print(f"  Premium: ₹{signal['entry_premium']:.2f} → Target: ₹{signal['target_premium']:.2f}")
        print(f"  Confidence: {signal['confidence']:.1f}%")
        print(f"  R:R = 1:{signal['risk_reward_ratio']}")
        print(f"  {signal['reason']}\n")
