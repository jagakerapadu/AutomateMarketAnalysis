"""
Paper Trading Engine - Execute virtual trades with live market data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
from datetime import datetime, time as dt_time
from typing import List, Dict, Optional
import psycopg2
from services.paper_trading.virtual_portfolio import VirtualPortfolio
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("paper_trading_engine")
settings = get_settings()


class PaperTradingEngine:
    """Main paper trading engine with live market data"""
    
    def __init__(self, auto_execute: bool = True):
        """
        Initialize paper trading engine
        
        Args:
            auto_execute: Automatically execute signals
        """
        self.portfolio = VirtualPortfolio()
        self.zerodha = ZerodhaAdapter()
        self.auto_execute = auto_execute
        self.watchlist = ['INFY', 'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK']
        self.running = False
        
        logger.info("Paper Trading Engine initialized")
    
    def get_live_prices(self, symbols: List[str] = None) -> Dict[str, float]:
        """
        Fetch live prices from Zerodha
        
        Args:
            symbols: List of symbols to fetch (defaults to watchlist)
        """
        if symbols is None:
            symbols = self.watchlist
        
        try:
            prices = {}
            
            for symbol in symbols:
                # Get latest quote from Zerodha
                instruments = self.zerodha.kite.ltp([f"NSE:{symbol}"])
                
                if instruments:
                    key = f"NSE:{symbol}"
                    if key in instruments:
                        prices[symbol] = instruments[key]['last_price']
            
            logger.debug(f"Fetched live prices: {prices}")
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching live prices: {e}")
            return {}
    
    def get_pending_signals(self) -> List[Dict]:
        """Get unexecuted trading signals"""
        try:
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )
            cursor = conn.cursor()
            
            # Get signals not yet executed in paper trading
            cursor.execute("""
                SELECT s.id, s.symbol, s.signal_type, s.entry_price, 
                       s.stop_loss, s.target_price, s.confidence, s.strategy
                FROM signals s
                LEFT JOIN paper_orders po ON s.id = po.signal_id
                WHERE po.signal_id IS NULL
                  AND s.timestamp >= CURRENT_DATE - INTERVAL '7 days'
                  AND s.confidence >= 70
                ORDER BY s.confidence DESC, s.timestamp DESC
                LIMIT 10
            """)
            
            signals = []
            for row in cursor.fetchall():
                signals.append({
                    'id': row[0],
                    'symbol': row[1],
                    'signal_type': row[2],
                    'entry_price': float(row[3]),
                    'stop_loss': float(row[4]) if row[4] else None,
                    'target': float(row[5]) if row[5] else None,
                    'confidence': float(row[6]),
                    'strategy': row[7]
                })
            
            cursor.close()
            conn.close()
            
            return signals
            
        except Exception as e:
            logger.error(f"Error fetching signals: {e}")
            return []
    
    def execute_signal(self, signal: Dict, current_price: float) -> bool:
        """
        Execute a trading signal
        
        Args:
            signal: Signal dictionary
            current_price: Current market price
        """
        try:
            symbol = signal['symbol']
            signal_type = signal['signal_type']
            confidence = signal['confidence']
            
            # Calculate position size based on confidence
            # Higher confidence = larger position
            portfolio_summary = self.portfolio.get_portfolio_summary()
            available_cash = portfolio_summary['available_cash']
            
            # Risk management: Don't use more than 20% per trade
            max_trade_value = available_cash * 0.20
            
            # Calculate quantity (rounded to nearest lot)
            quantity = int(max_trade_value / current_price)
            quantity = max(quantity, 1)  # At least 1 share
            
            # Generate order ID
            order_id = f"PAPER_{symbol}_{int(time.time())}"
            
            # Execute order
            success = self.portfolio.place_order(
                order_id=order_id,
                symbol=symbol,
                order_type=signal_type,
                quantity=quantity,
                price=current_price,
                signal_id=signal['id']
            )
            
            if success:
                logger.info(f"✅ Executed: {signal_type} {quantity} {symbol} @ ₹{current_price:.2f} (Confidence: {confidence}%)")
            else:
                logger.warning(f"❌ Failed to execute: {signal_type} {symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return False
    
    def check_exit_conditions(self):
        """Check if any positions should be exited"""
        positions = self.portfolio.get_positions()
        live_prices = self.get_live_prices([p['symbol'] for p in positions])
        
        for position in positions:
            symbol = position['symbol']
            current_price = live_prices.get(symbol)
            
            if not current_price:
                continue
            
            avg_price = position['avg_price']
            pnl_percent = position['pnl_percent']
            
            # Simple exit logic
            # Exit if profit > 3% or loss > 2%
            should_exit = False
            reason = ""
            
            if pnl_percent >= 3:
                should_exit = True
                reason = f"Target hit: +{pnl_percent:.2f}%"
            elif pnl_percent <= -2:
                should_exit = True
                reason = f"Stop loss hit: {pnl_percent:.2f}%"
            
            if should_exit:
                order_id = f"PAPER_EXIT_{symbol}_{int(time.time())}"
                success = self.portfolio.place_order(
                    order_id=order_id,
                    symbol=symbol,
                    order_type='SELL',
                    quantity=position['quantity'],
                    price=current_price
                )
                
                if success:
                    logger.info(f"🔔 Exited position: {symbol} - {reason}")
    
    def update_portfolio_prices(self):
        """Update all portfolio positions with live prices"""
        positions = self.portfolio.get_positions()
        
        if not positions:
            return
        
        symbols = [p['symbol'] for p in positions]
        live_prices = self.get_live_prices(symbols)
        
        if live_prices:
            self.portfolio.update_positions_with_live_prices(live_prices)
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Skip weekends
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    def run_cycle(self):
        """Run one trading cycle"""
        try:
            logger.info("=" * 60)
            logger.info("Running paper trading cycle")
            
            # Update portfolio with live prices
            self.update_portfolio_prices()
            
            # Check exit conditions
            self.check_exit_conditions()
            
            # Execute pending signals (if auto-execute enabled)
            if self.auto_execute:
                signals = self.get_pending_signals()
                
                if signals:
                    logger.info(f"Found {len(signals)} pending signals")
                    
                    for signal in signals:
                        symbol = signal['symbol']
                        
                        # Get current price
                        prices = self.get_live_prices([symbol])
                        current_price = prices.get(symbol)
                        
                        if current_price:
                            # Check if price is close to signal entry (within 2%)
                            entry_price = signal['entry_price']
                            price_diff_pct = abs(current_price - entry_price) / entry_price * 100
                            
                            if price_diff_pct <= 2:
                                self.execute_signal(signal, current_price)
                            else:
                                logger.debug(f"Skipping {symbol}: Price moved {price_diff_pct:.2f}% from signal")
                else:
                    logger.info("No pending signals to execute")
            
            # Display portfolio summary
            summary = self.portfolio.get_portfolio_summary()
            logger.info(f"""
📊 Portfolio Summary:
   Total Capital: ₹{summary['total_capital']:,.2f}
   Available Cash: ₹{summary['available_cash']:,.2f}
   Invested: ₹{summary['invested_amount']:,.2f}
   Total P&L: ₹{summary['total_pnl']:,.2f}
   Today P&L: ₹{summary['today_pnl']:,.2f}
   Positions: {summary['positions_count']}
            """)
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    def start(self, interval: int = 60):
        """
        Start paper trading engine
        
        Args:
            interval: Update interval in seconds (default: 60)
        """
        self.running = True
        logger.info(f"🚀 Paper Trading Engine started (interval: {interval}s)")
        
        try:
            while self.running:
                if self.is_market_open():
                    logger.info("📈 Market is OPEN")
                    self.run_cycle()
                else:
                    logger.info("🔒 Market is CLOSED - Skipping cycle")
                
                # Sleep until next cycle
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping paper trading engine...")
            self.stop()
    
    def stop(self):
        """Stop the trading engine"""
        self.running = False
        logger.info("Paper Trading Engine stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper Trading Engine")
    parser.add_argument('--interval', type=int, default=60, 
                       help='Update interval in seconds (default: 60)')
    parser.add_argument('--no-auto', action='store_true',
                       help='Disable auto-execution of signals')
    
    args = parser.parse_args()
    
    engine = PaperTradingEngine(auto_execute=not args.no_auto)
    engine.start(interval=args.interval)


if __name__ == '__main__':
    main()
