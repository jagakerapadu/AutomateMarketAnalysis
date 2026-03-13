"""
Position Monitor - Continuous monitoring with alerts
Runs independently to watch for risk conditions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
from datetime import datetime
from services.paper_trading.risk_manager import RiskManager
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter
from config.logger import setup_logger
import psycopg2
from config.settings import get_settings

logger = setup_logger("position_monitor")


class PositionMonitor:
    """Continuously monitor positions and alert on risk conditions"""
    
    def __init__(self):
        self.risk_manager = RiskManager()
        self.zerodha = ZerodhaAdapter()
        self.settings = get_settings()
        self.running = False
        self.alert_history = {}  # Track alerts to avoid spam
    
    def update_all_prices(self):
        """Update all position prices with live data"""
        conn = psycopg2.connect(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        try:
            # Get equity positions
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM paper_positions 
                WHERE quantity > 0
            """)
            equity_symbols = [row[0] for row in cursor.fetchall()]
            
            if equity_symbols:
                # Get live quotes
                instruments = [f"NSE:{s}" for s in equity_symbols]
                
                try:
                    quotes = self.zerodha.kite.quote(instruments)
                    updated = 0
                    
                    for symbol in equity_symbols:
                        key = f"NSE:{symbol}"
                        if key in quotes:
                            price = quotes[key].get('last_price')
                            
                            if price:
                                cursor.execute("""
                                    UPDATE paper_positions
                                    SET current_price = %s,
                                        current_value = quantity * %s,
                                        pnl = (quantity * %s) - invested_value,
                                        pnl_percent = ((quantity * %s - invested_value) / invested_value * 100),
                                        updated_at = %s
                                    WHERE symbol = %s AND quantity > 0
                                """, (price, price, price, price, datetime.utcnow(), symbol))
                                updated += 1
                    
                    conn.commit()
                    logger.info(f"Updated {updated} equity positions")
                    
                except Exception as e:
                    logger.error(f"Error fetching equity prices: {e}")
            
            # Update options positions
            cursor.execute("""
                SELECT DISTINCT symbol, option_type, strike
                FROM paper_options_positions
                WHERE quantity > 0
            """)
            options = cursor.fetchall()
            
            if options:
                # Fetch options chain
                try:
                    nifty_chain = self.zerodha.fetch_options_chain('NIFTY')
                    
                    for symbol, opt_type, strike in options:
                        # Find matching option
                        for opt in nifty_chain:
                            if (opt['strike'] == float(strike) and 
                                opt['option_type'] == opt_type):
                                
                                premium = opt['ltp']
                                
                                cursor.execute("""
                                    UPDATE paper_options_positions
                                    SET current_premium = %s,
                                        current_value = quantity * %s * 50,
                                        pnl = (quantity * %s * 50) - invested,
                                        pnl_percent = ((quantity * %s * 50 - invested) / invested * 100),
                                        updated_at = %s
                                    WHERE symbol = %s AND option_type = %s 
                                      AND strike = %s AND quantity > 0
                                """, (premium, premium, premium, premium, 
                                     datetime.utcnow(), symbol, opt_type, strike))
                                break
                    
                    conn.commit()
                    logger.info(f"Updated {len(options)} options positions")
                    
                except Exception as e:
                    logger.error(f"Error fetching options prices: {e}")
        
        finally:
            cursor.close()
            conn.close()
    
    def check_risk_alerts(self) -> List[Dict]:
        """Check for risk conditions and generate alerts"""
        alerts = []
        
        # Get positions at risk
        at_risk = self.risk_manager.get_positions_at_risk()
        
        for pos in at_risk:
            symbol = pos['symbol']
            
            # Check if we already alerted on this (within last 5 minutes)
            last_alert = self.alert_history.get(symbol, 0)
            if time.time() - last_alert < 300:  # 5 minutes
                continue
            
            alert = {
                'time': datetime.now(),
                'symbol': symbol,
                'risk_level': pos['risk_level'],
                'pnl_percent': pos['pnl_percent'],
                'action': pos['action'],
                'current_price': pos['current_price']
            }
            alerts.append(alert)
            
            # Record alert
            self.alert_history[symbol] = time.time()
            
            # Log alert
            logger.warning(f"🚨 ALERT: {symbol} - {pos['risk_level']} - {pos['action']} "
                          f"(P&L: {pos['pnl_percent']:+.2f}%)")
        
        return alerts
    
    def monitor_cycle(self):
        """Run one monitoring cycle"""
        try:
            logger.info("="*60)
            logger.info("Running position monitor cycle")
            now = datetime.now()
            
            # Update prices
            self.update_all_prices()
            
            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            
            # Check alerts
            alerts = self.check_risk_alerts()
            
            # Display summary
            print(f"\n[{now.strftime('%I:%M:%S %p')}] Position Monitor Status:")
            print(f"  Capital: Rs.{risk_summary['total_capital']:,.0f} | "
                  f"Exposure: {risk_summary['exposure_percent']:.1f}% | "
                  f"Positions: {risk_summary['position_count']}")
            
            if risk_summary['positions_near_stop_loss'] > 0:
                print(f"  ⚠️  {risk_summary['positions_near_stop_loss']} positions near stop-loss!")
            
            if alerts:
                print(f"  🚨 {len(alerts)} NEW ALERTS:")
                for alert in alerts:
                    print(f"     {alert['symbol']}: {alert['action']}")
            else:
                print("  ✅ No critical alerts")
            
            # Check if running outside market hours
            if not self.is_market_open():
                print("  💤 Market closed - monitoring at reduced frequency")
            
        except Exception as e:
            logger.error(f"Error in monitor cycle: {e}")
            print(f"  ❌ Error: {e}")
    
    def is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now()
        
        # Skip weekends
        if now.weekday() >= 5:
            return False
        
        # Market hours: 9:15 AM to 3:30 PM
        from datetime import time as dt_time
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    def start(self):
        """Start continuous monitoring"""
        self.running = True
        
        print("="*60)
        print("🔍 Position Monitor Started")
        print("="*60)
        print()
        print("Monitoring:")
        print(f"  • Stop-Loss: -{self.risk_manager.STOP_LOSS_PERCENT}%")
        print(f"  • Target: +{self.risk_manager.TARGET_PROFIT_PERCENT}%")
        print(f"  • Position Size Limit: {self.risk_manager.MAX_POSITION_SIZE_PERCENT}%")
        print(f"  • Total Exposure Limit: {self.risk_manager.MAX_TOTAL_EXPOSURE}%")
        print()
        print("Press Ctrl+C to stop")
        print("="*60)
        print()
        
        try:
            while self.running:
                self.monitor_cycle()
                
                # Adjust frequency based on market hours
                if self.is_market_open():
                    time.sleep(30)  # Every 30 seconds during market
                else:
                    time.sleep(300)  # Every 5 minutes after hours
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Monitor stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    monitor = PositionMonitor()
    monitor.start()
