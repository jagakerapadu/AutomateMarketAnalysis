"""
Virtual Portfolio Manager - Track paper trading positions and P&L
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone
from typing import Dict, List, Optional
import psycopg2
from decimal import Decimal
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("virtual_portfolio")
settings = get_settings()


class VirtualPortfolio:
    """Manages virtual trading portfolio"""
    
    def __init__(self, initial_capital: float = 1000000):
        """
        Initialize virtual portfolio
        
        Args:
            initial_capital: Starting capital in INR (default: 10 lakhs)
        """
        self.initial_capital = initial_capital
        self.conn = self._get_db_connection()
        self._ensure_tables()
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
    
    def _ensure_tables(self):
        """Create paper trading tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Virtual portfolio table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_portfolio (
                id SERIAL PRIMARY KEY,
                total_capital DECIMAL(15, 2) NOT NULL,
                available_cash DECIMAL(15, 2) NOT NULL,
                invested_amount DECIMAL(15, 2) DEFAULT 0,
                total_pnl DECIMAL(15, 2) DEFAULT 0,
                today_pnl DECIMAL(15, 2) DEFAULT 0,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Virtual positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_positions (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                avg_price DECIMAL(10, 2) NOT NULL,
                current_price DECIMAL(10, 2),
                invested_value DECIMAL(15, 2) NOT NULL,
                current_value DECIMAL(15, 2),
                pnl DECIMAL(15, 2),
                pnl_percent DECIMAL(8, 2),
                position_type VARCHAR(10) DEFAULT 'LONG',
                opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol)
            )
        """)
        
        # Virtual orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_orders (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50) UNIQUE NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                order_type VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10, 2),
                executed_price DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'PENDING',
                signal_id INTEGER,
                placed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMPTZ,
                reason TEXT
            )
        """)
        
        self.conn.commit()
        cursor.close()
    
    def _initialize_portfolio(self):
        """Initialize portfolio with starting capital"""
        cursor = self.conn.cursor()
        
        # Check if portfolio exists
        cursor.execute("SELECT COUNT(*) FROM paper_portfolio")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute("""
                INSERT INTO paper_portfolio (total_capital, available_cash)
                VALUES (%s, %s)
            """, (self.initial_capital, self.initial_capital))
            self.conn.commit()
            logger.info(f"Initialized paper portfolio with ₹{self.initial_capital:,.2f}")
        
        cursor.close()
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        cursor = self.conn.cursor()
        
        # Get portfolio data
        cursor.execute("""
            SELECT total_capital, available_cash, invested_amount, 
                   total_pnl, today_pnl, updated_at
            FROM paper_portfolio
            ORDER BY id DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        # Get positions count
        cursor.execute("SELECT COUNT(*) FROM paper_positions WHERE quantity > 0")
        positions_count = cursor.fetchone()[0]
        
        cursor.close()
        
        if row:
            return {
                'total_capital': float(row[0]),
                'available_cash': float(row[1]),
                'invested_amount': float(row[2]),
                'total_pnl': float(row[3]),
                'today_pnl': float(row[4]),
                'positions_count': positions_count,
                'updated_at': row[5]
            }
        
        return None
    
    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, symbol, quantity, avg_price, current_price,
                   invested_value, current_value, pnl, pnl_percent,
                   position_type, opened_at, updated_at
            FROM paper_positions
            WHERE quantity > 0
            ORDER BY pnl DESC
        """)
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                'id': row[0],
                'symbol': row[1],
                'quantity': row[2],
                'avg_price': float(row[3]),
                'current_price': float(row[4]) if row[4] else None,
                'invested_value': float(row[5]),
                'current_value': float(row[6]) if row[6] else 0,
                'pnl': float(row[7]) if row[7] else 0,
                'pnl_percent': float(row[8]) if row[8] else 0,
                'position_type': row[9],
                'opened_at': row[10],
                'updated_at': row[11]
            })
        
        cursor.close()
        return positions
    
    def place_order(self, order_id: str, symbol: str, order_type: str, 
                    quantity: int, price: float, signal_id: int = None) -> bool:
        """
        Place a virtual order
        
        Args:
            order_id: Unique order identifier
            symbol: Stock symbol
            order_type: BUY or SELL
            quantity: Number of shares
            price: Execution price
            signal_id: Related signal ID
        """
        cursor = self.conn.cursor()
        
        try:
            # Check available cash for BUY orders
            if order_type == 'BUY':
                required_amount = quantity * price
                
                cursor.execute("SELECT available_cash FROM paper_portfolio ORDER BY id DESC LIMIT 1")
                available_cash = float(cursor.fetchone()[0])
                
                if required_amount > available_cash:
                    logger.warning(f"Insufficient funds: Need ₹{required_amount:,.2f}, Have ₹{available_cash:,.2f}")
                    return False
            
            # Insert order
            cursor.execute("""
                INSERT INTO paper_orders 
                (order_id, symbol, order_type, quantity, price, executed_price, 
                 status, signal_id, executed_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'EXECUTED', %s, %s)
            """, (order_id, symbol, order_type, quantity, price, price, 
                  signal_id, datetime.now(timezone.utc)))
            
            # Update position
            if order_type == 'BUY':
                self._add_to_position(cursor, symbol, quantity, price)
            else:
                self._reduce_from_position(cursor, symbol, quantity, price)
            
            self.conn.commit()
            logger.info(f"Order executed: {order_type} {quantity} {symbol} @ ₹{price:.2f}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error placing order: {e}")
            return False
        finally:
            cursor.close()
    
    def _add_to_position(self, cursor, symbol: str, quantity: int, price: float):
        """Add to existing position or create new"""
        # Check if position exists
        cursor.execute("""
            SELECT quantity, avg_price, invested_value 
            FROM paper_positions 
            WHERE symbol = %s
        """, (symbol,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing position
            old_qty = existing[0]
            old_avg = float(existing[1])
            old_invested = float(existing[2])
            
            new_qty = old_qty + quantity
            new_invested = old_invested + (quantity * price)
            new_avg = new_invested / new_qty
            
            cursor.execute("""
                UPDATE paper_positions
                SET quantity = %s,
                    avg_price = %s,
                    invested_value = %s,
                    updated_at = %s
                WHERE symbol = %s
            """, (new_qty, new_avg, new_invested, datetime.now(timezone.utc), symbol))
        else:
            # Create new position
            invested = quantity * price
            cursor.execute("""
                INSERT INTO paper_positions 
                (symbol, quantity, avg_price, invested_value)
                VALUES (%s, %s, %s, %s)
            """, (symbol, quantity, price, invested))
        
        # Update portfolio cash
        amount = quantity * price
        cursor.execute("""
            UPDATE paper_portfolio
            SET available_cash = available_cash - %s,
                invested_amount = invested_amount + %s,
                updated_at = %s
        """, (amount, amount, datetime.now(timezone.utc)))
    
    def _reduce_from_position(self, cursor, symbol: str, quantity: int, price: float):
        """Reduce or close position"""
        cursor.execute("""
            SELECT quantity, avg_price, invested_value
            FROM paper_positions
            WHERE symbol = %s
        """, (symbol,))
        
        existing = cursor.fetchone()
        
        if not existing:
            logger.warning(f"No position found for {symbol}")
            return
        
        old_qty = existing[0]
        old_avg = float(existing[1])
        old_invested = float(existing[2])
        
        if quantity > old_qty:
            logger.warning(f"Trying to sell {quantity} but only have {old_qty}")
            quantity = old_qty
        
        # Calculate P&L
        sell_value = quantity * price
        cost_basis = quantity * old_avg
        pnl = sell_value - cost_basis
        
        # Update position
        new_qty = old_qty - quantity
        new_invested = old_invested - cost_basis
        
        if new_qty > 0:
            cursor.execute("""
                UPDATE paper_positions
                SET quantity = %s,
                    invested_value = %s,
                    updated_at = %s
                WHERE symbol = %s
            """, (new_qty, new_invested, datetime.now(timezone.utc), symbol))
        else:
            # Close position
            cursor.execute("DELETE FROM paper_positions WHERE symbol = %s", (symbol,))
        
        # Update portfolio
        cursor.execute("""
            UPDATE paper_portfolio
            SET available_cash = available_cash + %s,
                invested_amount = invested_amount - %s,
                total_pnl = total_pnl + %s,
                today_pnl = today_pnl + %s,
                updated_at = %s
        """, (sell_value, cost_basis, pnl, pnl, datetime.now(timezone.utc)))
        
        logger.info(f"Position closed: {symbol} P&L: ₹{pnl:,.2f}")
    
    def update_positions_with_live_prices(self, live_prices: Dict[str, float]):
        """
        Update all positions with current market prices
        
        Args:
            live_prices: Dict of {symbol: current_price}
        """
        cursor = self.conn.cursor()
        
        try:
            total_pnl = 0
            
            for symbol, current_price in live_prices.items():
                cursor.execute("""
                    UPDATE paper_positions
                    SET current_price = %s,
                        current_value = quantity * %s,
                        pnl = (quantity * %s) - invested_value,
                        pnl_percent = ((quantity * %s - invested_value) / invested_value * 100),
                        updated_at = %s
                    WHERE symbol = %s AND quantity > 0
                """, (current_price, current_price, current_price, current_price, 
                      datetime.now(timezone.utc), symbol))
            
            # Calculate total unrealized P&L
            cursor.execute("""
                SELECT COALESCE(SUM(pnl), 0) 
                FROM paper_positions 
                WHERE quantity > 0
            """)
            unrealized_pnl = float(cursor.fetchone()[0])
            
            # Update portfolio
            cursor.execute("""
                UPDATE paper_portfolio
                SET updated_at = %s
                WHERE id = (SELECT id FROM paper_portfolio ORDER BY id DESC LIMIT 1)
            """, (datetime.now(timezone.utc),))
            
            self.conn.commit()
            logger.debug(f"Updated {len(live_prices)} positions. Unrealized P&L: ₹{unrealized_pnl:,.2f}")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating positions: {e}")
        finally:
            cursor.close()
    
    def get_orders(self, limit: int = 50) -> List[Dict]:
        """Get order history"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT order_id, symbol, order_type, quantity, price, 
                   executed_price, status, placed_at, executed_at
            FROM paper_orders
            ORDER BY placed_at DESC
            LIMIT %s
        """, (limit,))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'order_id': row[0],
                'symbol': row[1],
                'order_type': row[2],
                'quantity': row[3],
                'price': float(row[4]) if row[4] else None,
                'executed_price': float(row[5]) if row[5] else None,
                'status': row[6],
                'placed_at': row[7],
                'executed_at': row[8]
            })
        
        cursor.close()
        return orders
    
    def reset_portfolio(self):
        """Reset portfolio to initial state"""
        cursor = self.conn.cursor()
        
        cursor.execute("DELETE FROM paper_positions")
        cursor.execute("DELETE FROM paper_orders")
        cursor.execute("DELETE FROM paper_portfolio")
        
        cursor.execute("""
            INSERT INTO paper_portfolio (total_capital, available_cash)
            VALUES (%s, %s)
        """, (self.initial_capital, self.initial_capital))
        
        self.conn.commit()
        cursor.close()
        
        logger.info(f"Portfolio reset to ₹{self.initial_capital:,.2f}")
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'conn'):
            self.conn.close()
