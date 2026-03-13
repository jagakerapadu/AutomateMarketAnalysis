"""
Options Virtual Portfolio - Track paper trading options positions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import psycopg2
from decimal import Decimal
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("options_virtual_portfolio")
settings = get_settings()

NIFTY_LOT_SIZE = 50  # Nifty lot size


class OptionsVirtualPortfolio:
    """Manage virtual options trading portfolio"""
    
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.conn = self._get_db_connection()
        self._initialize_portfolio()
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
    
    def _initialize_portfolio(self):
        """Initialize portfolio if not exists"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM paper_options_portfolio")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute("""
                INSERT INTO paper_options_portfolio (total_capital, available_cash)
                VALUES (%s, %s)
            """, (self.initial_capital, self.initial_capital))
            self.conn.commit()
            logger.info(f"Initialized options portfolio with Rs.{self.initial_capital:,.2f}")
        
        cursor.close()
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl
            FROM paper_options_portfolio
            ORDER BY id DESC LIMIT 1
        """)
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return {
                'total_capital': float(row[0]),
                'available_cash': float(row[1]),
                'invested_amount': float(row[2]),
                'total_pnl': float(row[3]),
                'today_pnl': float(row[4])
            }
        
        return {}
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open options positions"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, symbol, strike, option_type, expiry_date, quantity,
                   entry_premium, current_premium, invested_value, current_value,
                   pnl, pnl_percent, strategy, opened_at, days_to_expiry
            FROM paper_options_positions
            WHERE quantity > 0
            ORDER BY opened_at DESC
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        
        positions = []
        for row in rows:
            positions.append({
                'id': row[0],
                'symbol': row[1],
                'strike': float(row[2]),
                'option_type': row[3],
                'expiry_date': row[4],
                'quantity': row[5],
                'entry_premium': float(row[6]),
                'current_premium': float(row[7]) if row[7] else 0,
                'invested_value': float(row[8]),
                'current_value': float(row[9]) if row[9] else 0,
                'pnl': float(row[10]) if row[10] else 0,
                'pnl_percent': float(row[11]) if row[11] else 0,
                'strategy': row[12],
                'opened_at': row[13],
                'days_to_expiry': row[14]
            })
        
        return positions
    
    def execute_buy_order(self, signal: Dict) -> bool:
        """Execute options buy order"""
        try:
            symbol = signal['symbol']
            strike = signal['strike']
            option_type = signal['option_type']
            expiry_date = signal['expiry_date']
            quantity = signal['quantity']
            premium = signal['entry_premium']
            strategy = signal['strategy']
            
            # Total cost = premium × quantity × lot_size
            total_cost = premium * quantity * NIFTY_LOT_SIZE
            
            # Check available cash
            portfolio = self.get_portfolio_summary()
            if total_cost > portfolio['available_cash']:
                logger.warning(f"Insufficient cash: Need ₹{total_cost:,.2f}, have ₹{portfolio['available_cash']:,.2f}")
                return False
            
            cursor = self.conn.cursor()
            
            # Insert position
            cursor.execute("""
                INSERT INTO paper_options_positions (
                    symbol, strike, option_type, expiry_date, quantity,
                    entry_premium, current_premium, invested_value, current_value,
                    pnl, pnl_percent, position_type, strategy, entry_iv,
                    days_to_expiry, opened_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, strike, option_type, expiry_date) DO UPDATE SET
                    quantity = paper_options_positions.quantity + EXCLUDED.quantity,
                    invested_value = paper_options_positions.invested_value + EXCLUDED.invested_value
                RETURNING id
            """, (
                symbol, strike, option_type, expiry_date, quantity,
                premium, premium, total_cost, total_cost,
                0, 0, 'LONG', strategy, signal.get('entry_iv', 0),
                self._days_to_expiry(expiry_date), datetime.now(timezone.utc)
            ))
            
            position_id = cursor.fetchone()[0]
            
            # Insert order
            order_id = f"OPT{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            cursor.execute("""
                INSERT INTO paper_options_orders (
                    order_id, symbol, strike, option_type, expiry_date,
                    order_type, quantity, order_premium, executed_premium,
                    total_cost, status, signal_id, strategy, confidence,
                    executed_at, reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id, symbol, strike, option_type, expiry_date,
                'BUY', quantity, premium, premium,
                total_cost, 'EXECUTED', signal.get('id'), strategy,
                signal.get('confidence', 0), datetime.now(timezone.utc),
                signal.get('reason', '')
            ))
            
            # Update portfolio
            cursor.execute("""
                UPDATE paper_options_portfolio SET
                    available_cash = available_cash - %s,
                    invested_amount = invested_amount + %s,
                    updated_at = NOW()
            """, (total_cost, total_cost))
            
            self.conn.commit()
            cursor.close()
            
            logger.info(f"BUY: {quantity} lot(s) {option_type} {strike} @ Rs.{premium:.2f} (Total: Rs.{total_cost:,.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            self.conn.rollback()
            return False
    
    def execute_sell_order(self, position: Dict, exit_premium: float, exit_reason: str) -> bool:
        """Execute options sell order (close position)"""
        try:
            symbol = position['symbol']
            strike = position['strike']
            option_type = position['option_type']
            expiry_date = position['expiry_date']
            quantity = position['quantity']
            entry_premium = position['entry_premium']
            
            # Calculate P&L
            premium_diff = exit_premium - entry_premium
            total_pnl = premium_diff * quantity * NIFTY_LOT_SIZE
            exit_value = exit_premium * quantity * NIFTY_LOT_SIZE
            
            cursor = self.conn.cursor()
            
            # Delete position (close it)
            cursor.execute("""
                DELETE FROM paper_options_positions
                WHERE symbol = %s AND strike = %s AND option_type = %s AND expiry_date = %s
            """, (symbol, strike, option_type, expiry_date))
            
            # Insert exit order
            order_id = f"OPT{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            cursor.execute("""
                INSERT INTO paper_options_orders (
                    order_id, symbol, strike, option_type, expiry_date,
                    order_type, quantity, order_premium, executed_premium,
                    total_cost, status, strategy, executed_at, exit_reason, reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id, symbol, strike, option_type, expiry_date,
                'SELL', quantity, exit_premium, exit_premium,
                exit_value, 'EXECUTED', position['strategy'],
                datetime.now(timezone.utc), exit_reason,
                f"Exit: {exit_reason}"
            ))
            
            # Update portfolio
            cursor.execute("""
                UPDATE paper_options_portfolio SET
                    available_cash = available_cash + %s,
                    invested_amount = invested_amount - %s,
                    total_pnl = total_pnl + %s,
                    today_pnl = today_pnl + %s,
                    updated_at = NOW()
            """, (exit_value, position['invested_value'], total_pnl, total_pnl))
            
            self.conn.commit()
            cursor.close()
            
            logger.info(f"SELL: {quantity} lot(s) {option_type} {strike} @ Rs.{exit_premium:.2f} | P&L: Rs.{total_pnl:,.2f} ({exit_reason})")
            return True
            
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            self.conn.rollback()
            return False
    
    def update_positions_prices(self, options_data: Dict):
        """Update current prices for all positions"""
        positions = self.get_open_positions()
        
        for pos in positions:
            # Normalize strike to int for key matching (avoids 23550.0 vs 23550.00 issues)
            strike_normalized = int(float(pos['strike']))
            key = f"{pos['symbol']}_{strike_normalized}_{pos['option_type']}"
            
            if key in options_data:
                current_premium = options_data[key]['ltp']
                
                # Update position
                cursor = self.conn.cursor()
                
                current_value = current_premium * pos['quantity'] * NIFTY_LOT_SIZE
                pnl = current_value - pos['invested_value']
                pnl_percent = (pnl / pos['invested_value']) * 100
                
                cursor.execute("""
                    UPDATE paper_options_positions SET
                        current_premium = %s,
                        current_value = %s,
                        pnl = %s,
                        pnl_percent = %s,
                        current_iv = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (current_premium, current_value, pnl, pnl_percent,
                      options_data[key].get('iv', 0), pos['id']))
                
                self.conn.commit()
                cursor.close()
    
    def _days_to_expiry(self, expiry_date) -> int:
        """Calculate days to expiry"""
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        today = datetime.now().date()
        return (expiry_date - today).days


if __name__ == "__main__":
    # Test portfolio
    portfolio = OptionsVirtualPortfolio()
    summary = portfolio.get_portfolio_summary()
    
    print("\n=== OPTIONS PORTFOLIO SUMMARY ===")
    print(f"Total Capital: ₹{summary['total_capital']:,.2f}")
    print(f"Available Cash: ₹{summary['available_cash']:,.2f}")
    print(f"Invested: ₹{summary['invested_amount']:,.2f}")
    print(f"Total P&L: ₹{summary['total_pnl']:,.2f}")
    
    positions = portfolio.get_open_positions()
    print(f"\nOpen Positions: {len(positions)}")
    
    for pos in positions:
        print(f"  {pos['option_type']} {pos['strike']} @ ₹{pos['entry_premium']:.2f} | P&L: ₹{pos['pnl']:.2f}")
