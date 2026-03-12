"""
Options Paper Trading Engine - Auto-execute options signals
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone, time
from typing import Dict, List
import time as time_module
import psycopg2
from config.settings import get_settings
from config.logger import setup_logger
from services.paper_trading.options_virtual_portfolio import OptionsVirtualPortfolio
from services.strategy.options_signal_generator import OptionsSignalGenerator
from services.indicators.options_indicators import OptionsIndicators

logger = setup_logger("options_trading_engine")
settings = get_settings()


class OptionsTradingEngine:
    """Main options trading engine - auto-execution"""
    
    def __init__(self):
        self.portfolio = OptionsVirtualPortfolio()
        self.signal_generator = OptionsSignalGenerator()
        self.options_calc = OptionsIndicators()
        self.conn = self._get_db_connection()
        logger.info("Options Trading Engine initialized")
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
    
    def is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now()
        
        # Market hours: Mon-Fri, 9:15 AM - 3:30 PM
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = time(9, 15)
        market_close = time(15, 30)
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    def get_pending_signals(self) -> List[Dict]:
        """Get pending options signals"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, symbol, strike, option_type, expiry_date,
                   signal_type, strategy, entry_premium, stop_loss_premium, target_premium,
                   confidence, quantity, reason
            FROM options_signals
            WHERE status = 'PENDING'
                AND confidence >= 70
                AND expiry_date >= CURRENT_DATE
            ORDER BY confidence DESC, timestamp DESC
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row[0],
                'symbol': row[1],
                'strike': float(row[2]),
                'option_type': row[3],
                'expiry_date': row[4],
                'signal_type': row[5],
                'strategy': row[6],
                'entry_premium': float(row[7]),
                'stop_loss_premium': float(row[8]),
                'target_premium': float(row[9]),
                'confidence': float(row[10]),
                'quantity': row[11],
                'reason': row[12]
            })
        
        return signals
    
    def get_current_premium(self, symbol: str, strike: float, option_type: str) -> float:
        """Get current option premium from options chain"""
        df = self.options_calc.get_options_chain(symbol)
        
        if df.empty:
            return 0
        
        option_data = df[(df['strike'] == strike) & (df['option_type'] == option_type)]
        
        if not option_data.empty:
            return float(option_data.iloc[0]['ltp'])
        
        return 0
    
    def execute_pending_signals(self):
        """Execute pending signals if conditions met"""
        signals = self.get_pending_signals()
        
        if not signals:
            logger.info("No pending signals to execute")
            return
        
        logger.info(f"Found {len(signals)} pending signals")
        
        for signal in signals:
            try:
                # Get current premium
                current_premium = self.get_current_premium(
                    signal['symbol'],
                    signal['strike'],
                    signal['option_type']
                )
                
                if current_premium == 0:
                    logger.warning(f"No price data for {signal['option_type']} {signal['strike']}")
                    continue
                
                # Check if price is within acceptable range (±5%)
                entry_premium = signal['entry_premium']
                price_diff_pct = abs(current_premium - entry_premium) / entry_premium * 100
                
                if price_diff_pct <= 5:  # Within 5% tolerance
                    # Execute the trade
                    signal['entry_premium'] = current_premium  # Use current price
                    
                    success = self.portfolio.execute_buy_order(signal)
                    
                    if success:
                        # Mark signal as executed
                        cursor = self.conn.cursor()
                        cursor.execute("""
                            UPDATE options_signals SET status = 'EXECUTED'
                            WHERE id = %s
                        """, (signal['id'],))
                        self.conn.commit()
                        cursor.close()
                        
                        logger.info(f"[OK] Executed: {signal['strategy']} - {signal['option_type']} {signal['strike']} @ Rs.{current_premium:.2f}")
                else:
                    logger.info(f"Price moved {price_diff_pct:.1f}% - skipping {signal['option_type']} {signal['strike']}")
                    
            except Exception as e:
                logger.error(f"Error executing signal: {e}")
    
    def check_exit_conditions(self):
        """Check if any positions should be closed"""
        positions = self.portfolio.get_open_positions()
        
        if not positions:
            return
        
        logger.info(f"Checking exit conditions for {len(positions)} positions")
        
        for pos in positions:
            try:
                # Get current premium
                current_premium = self.get_current_premium(
                    pos['symbol'],
                    pos['strike'],
                    pos['option_type']
                )
                
                if current_premium == 0:
                    continue
                
                entry_premium = pos['entry_premium']
                pnl_percent = ((current_premium - entry_premium) / entry_premium) * 100
                
                exit_reason = None
                
                # Exit conditions
                # 1. Target hit (+60% to +80% based on strategy)
                if pnl_percent >= 60:
                    exit_reason = "TARGET"
                
                # 2. Stop loss hit (-40% to -50%)
                elif pnl_percent <= -40:
                    exit_reason = "STOP_LOSS"
                
                # 3. Time decay - exit 1 day before expiry
                elif pos['days_to_expiry'] <= 1:
                    exit_reason = "EXPIRY"
                
                # 4. End of day exit (3:00 PM for intraday)
                now = datetime.now()
                if now.hour >= 15 and pos['strategy'] in ['ORB_Options']:
                    exit_reason = "TIME_DECAY"
                
                if exit_reason:
                    success = self.portfolio.execute_sell_order(pos, current_premium, exit_reason)
                    
                    if success:
                        logger.info(f"[CLOSED] {pos['option_type']} {pos['strike']} @ Rs.{current_premium:.2f} | P&L: {pnl_percent:.2f}% ({exit_reason})")
                
            except Exception as e:
                logger.error(f"Error checking exit for position: {e}")
    
    def update_all_positions(self):
        """Update current prices for all positions"""
        positions = self.portfolio.get_open_positions()
        
        if not positions:
            return
        
        # Fetch options chain data
        df = self.options_calc.get_options_chain("NIFTY")
        
        if df.empty:
            return
        
        # Create lookup dict
        options_data = {}
        for _, row in df.iterrows():
            # Normalize strike to int for key matching
            strike_normalized = int(float(row['strike']))
            key = f"{row['symbol']}_{strike_normalized}_{row['option_type']}"
            options_data[key] = {
                'ltp': float(row['ltp']),
                'iv': float(row['iv']) if row['iv'] else 0
            }
        
        # Update positions
        self.portfolio.update_positions_prices(options_data)
    
    def run_cycle(self):
        """Run one trading cycle"""
        logger.info("=" * 70)
        logger.info("Running options trading cycle")
        
        try:
            # 1. Update current positions with live prices
            self.update_all_positions()
            
            # 2. Check exit conditions
            self.check_exit_conditions()
            
            # 3. Execute pending signals
            self.execute_pending_signals()
            
            # 4. Show summary
            summary = self.portfolio.get_portfolio_summary()
            positions = self.portfolio.get_open_positions()
            
            logger.info(f"""
OPTIONS PORTFOLIO STATUS:
  Capital: Rs.{summary.get('total_capital', 0):,.2f}
  Available: Rs.{summary.get('available_cash', 0):,.2f}
  Invested: Rs.{summary.get('invested_amount', 0):,.2f}
  P&L: Rs.{summary.get('total_pnl', 0):,.2f}
  Open Positions: {len(positions)}
            """)
            
            for pos in positions:
                logger.info(f"  {pos['option_type']} {pos['strike']} - Rs.{pos['current_premium']:.2f} | P&L: Rs.{pos['pnl']:.2f} ({pos['pnl_percent']:.2f}%)")
        
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    def start(self, interval: int = 60):
        """Start the trading engine"""
        logger.info(f"[START] Options Trading Engine started (interval: {interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                if self.is_market_open():
                    logger.info("[MARKET OPEN] Running cycle")
                    self.run_cycle()
                else:
                    logger.info("[MARKET CLOSED] Skipping cycle")
                
                time_module.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping options trading engine...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            logger.info("Options Trading Engine stopped")


if __name__ == "__main__":
    engine = OptionsTradingEngine()
    engine.start(interval=60)  # Run every 60 seconds
