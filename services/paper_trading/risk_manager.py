"""
Risk Management Module for Paper Trading
Enforces position limits, stop-loss, capital allocation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("risk_manager")


class RiskManager:
    """Manages trading risk and position sizing"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Risk limits (configurable)
        self.MAX_POSITION_SIZE_PERCENT = 10  # Max 10% of capital per position
        self.MAX_TOTAL_EXPOSURE = 80  # Max 80% capital deployed
        self.STOP_LOSS_PERCENT = 2  # Auto-exit at -2%
        self.TARGET_PROFIT_PERCENT = 3  # Auto-exit at +3%
        self.OPTIONS_STOP_LOSS_PERCENT = 40  # Options stop-loss at -40%
        self.OPTIONS_TARGET_PERCENT = 50  # Options target at +50%
        
        # Concentration limits
        self.MAX_POSITIONS = 20  # Max 20 positions at once
        self.MAX_SECTOR_EXPOSURE = 30  # Max 30% per sector
    
    def validate_position_size(self, symbol: str, quantity: int, price: float, 
                              total_capital: float) -> Tuple[bool, str, int]:
        """
        Validate if position size is within risk limits
        
        Args:
            symbol: Stock symbol
            quantity: Proposed quantity
            price: Entry price
            total_capital: Total portfolio capital
            
        Returns:
            (is_valid, reason, suggested_quantity)
        """
        position_value = quantity * price
        position_percent = (position_value / total_capital) * 100
        
        # Check if position size exceeds limit
        if position_percent > self.MAX_POSITION_SIZE_PERCENT:
            # Calculate max allowed quantity
            max_allowed_value = total_capital * (self.MAX_POSITION_SIZE_PERCENT / 100)
            max_quantity = int(max_allowed_value / price)
            
            reason = (f"Position size {position_percent:.2f}% exceeds limit "
                     f"({self.MAX_POSITION_SIZE_PERCENT}%). "
                     f"Max allowed: {max_quantity} shares (Rs.{max_allowed_value:,.2f})")
            
            logger.warning(f"{symbol}: {reason}")
            return False, reason, max_quantity
        
        return True, "Position size within limits", quantity
    
    def check_total_exposure(self, additional_amount: float) -> Tuple[bool, str]:
        """
        Check if adding new position exceeds total exposure limit
        
        Returns:
            (is_allowed, reason)
        """
        conn = psycopg2.connect(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT total_capital, invested_amount
                FROM paper_portfolio
                ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return True, "No portfolio data"
            
            total_capital = float(row[0])
            current_invested = float(row[1])
            new_invested = current_invested + additional_amount
            
            exposure_percent = (new_invested / total_capital) * 100
            
            if exposure_percent > self.MAX_TOTAL_EXPOSURE:
                reason = (f"Total exposure {exposure_percent:.2f}% would exceed limit "
                         f"({self.MAX_TOTAL_EXPOSURE}%)")
                logger.warning(reason)
                return False, reason
            
            return True, f"Exposure OK: {exposure_percent:.2f}%"
            
        finally:
            cursor.close()
            conn.close()
    
    def check_position_limits(self) -> Tuple[bool, str]:
        """Check if we've hit maximum number of positions"""
        conn = psycopg2.connect(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM paper_positions WHERE quantity > 0")
            position_count = cursor.fetchone()[0]
            
            if position_count >= self.MAX_POSITIONS:
                reason = f"Maximum positions ({self.MAX_POSITIONS}) reached"
                logger.warning(reason)
                return False, reason
            
            return True, f"Positions OK: {position_count}/{self.MAX_POSITIONS}"
            
        finally:
            cursor.close()
            conn.close()
    
    def should_exit_position(self, symbol: str, entry_price: float, current_price: float,
                            is_options: bool = False) -> Tuple[bool, str]:
        """
        Check if position should be exited based on stop-loss or target
        
        Returns:
            (should_exit, reason)
        """
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        
        if is_options:
            # Options have wider stops due to volatility
            if pnl_percent <= -self.OPTIONS_STOP_LOSS_PERCENT:
                return True, f"OPTIONS STOP-LOSS: {pnl_percent:.2f}%"
            elif pnl_percent >= self.OPTIONS_TARGET_PERCENT:
                return True, f"OPTIONS TARGET: +{pnl_percent:.2f}%"
        else:
            # Regular equity stop-loss and target
            if pnl_percent <= -self.STOP_LOSS_PERCENT:
                return True, f"STOP-LOSS: {pnl_percent:.2f}%"
            elif pnl_percent >= self.TARGET_PROFIT_PERCENT:
                return True, f"TARGET: +{pnl_percent:.2f}%"
        
        return False, f"P&L: {pnl_percent:+.2f}%"
    
    def get_positions_at_risk(self) -> List[Dict]:
        """
        Get all positions that are at or near stop-loss
        
        Returns list of positions with risk assessment
        """
        conn = psycopg2.connect(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT symbol, quantity, avg_price, current_price, 
                       invested_value, current_value, pnl, pnl_percent, updated_at
                FROM paper_positions
                WHERE quantity > 0 AND current_price IS NOT NULL
                ORDER BY pnl_percent ASC
            """)
            
            at_risk = []
            for row in cursor.fetchall():
                symbol, qty, avg, curr, inv, curr_val, pnl, pnl_pct, updated = row
                
                pnl_pct_float = float(pnl_pct)
                
                # Risk levels
                risk_level = "LOW"
                action = "HOLD"
                
                if pnl_pct_float <= -2:
                    risk_level = "CRITICAL"
                    action = "EXIT NOW - Stop-loss hit"
                elif pnl_pct_float <= -1.5:
                    risk_level = "HIGH"
                    action = "WATCH - Near stop-loss"
                elif pnl_pct_float <= -1:
                    risk_level = "MEDIUM"
                    action = "MONITOR"
                
                if risk_level != "LOW":
                    at_risk.append({
                        'symbol': symbol,
                        'quantity': qty,
                        'avg_price': float(avg),
                        'current_price': float(curr),
                        'pnl': float(pnl),
                        'pnl_percent': pnl_pct_float,
                        'risk_level': risk_level,
                        'action': action,
                        'updated_minutes_ago': (datetime.now(timezone.utc) - updated).total_seconds() / 60
                    })
            
            return at_risk
            
        finally:
            cursor.close()
            conn.close()
    
    def calculate_optimal_position_size(self, symbol: str, price: float, 
                                       confidence: float = 75) -> int:
        """
        Calculate optimal position size based on risk management rules
        
        Args:
            symbol: Stock symbol
            price: Entry price
            confidence: Signal confidence (0-100)
            
        Returns:
            Suggested quantity
        """
        conn = psycopg2.connect(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT total_capital, available_cash
                FROM paper_portfolio
                ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return 0
            
            total_capital = float(row[0])
            available_cash = float(row[1])
            
            # Base allocation: 10% of capital max
            max_position_value = total_capital * (self.MAX_POSITION_SIZE_PERCENT / 100)
            
            # Adjust for confidence (70% = 50% of max, 100% = 100% of max)
            confidence_factor = (confidence - 70) / 30  # Maps 70-100 to 0-1
            confidence_factor = max(0.5, min(1.0, confidence_factor))
            
            adjusted_position_value = max_position_value * confidence_factor
            
            # Ensure we have enough cash
            position_value = min(adjusted_position_value, available_cash * 0.9)  # Use max 90% of available
            
            # Calculate quantity
            quantity = int(position_value / price)
            
            logger.info(f"{symbol}: Optimal size = {quantity} shares "
                       f"(Rs.{quantity*price:,.2f}, {confidence}% confidence)")
            
            return max(1, quantity)
            
        finally:
            cursor.close()
            conn.close()
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        conn = psycopg2.connect(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        try:
            # Portfolio metrics
            cursor.execute("""
                SELECT total_capital, available_cash, invested_amount, total_pnl
                FROM paper_portfolio
                ORDER BY id DESC LIMIT 1
            """)
            portfolio = cursor.fetchone()
            
            total_capital = float(portfolio[0])
            available_cash = float(portfolio[1])
            invested = float(portfolio[2])
            total_pnl = float(portfolio[3])
            
            # Position metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as position_count,
                    MAX(invested_value) as largest_position,
                    AVG(pnl_percent) as avg_pnl_percent,
                    COUNT(CASE WHEN pnl_percent < -1.5 THEN 1 END) as near_stop_loss
                FROM paper_positions
                WHERE quantity > 0
            """)
            pos_metrics = cursor.fetchone()
            
            # Options risk
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(invested), 0), COALESCE(SUM(pnl_percent), 0)
                FROM paper_options_positions
                WHERE quantity > 0
            """)
            opt_metrics = cursor.fetchone()
            
            exposure_percent = (invested / total_capital) * 100
            largest_position_percent = (float(pos_metrics[1] or 0) / total_capital) * 100
            
            return {
                'total_capital': total_capital,
                'exposure_percent': exposure_percent,
                'cash_reserve_percent': (available_cash / total_capital) * 100,
                'position_count': pos_metrics[0],
                'largest_position_percent': largest_position_percent,
                'avg_position_pnl': float(pos_metrics[2] or 0),
                'positions_near_stop_loss': pos_metrics[3],
                'options_positions': opt_metrics[0],
                'options_invested': float(opt_metrics[1]),
                'total_pnl': total_pnl,
                'within_limits': {
                    'exposure': exposure_percent <= self.MAX_TOTAL_EXPOSURE,
                    'position_size': largest_position_percent <= self.MAX_POSITION_SIZE_PERCENT,
                    'position_count': pos_metrics[0] <= self.MAX_POSITIONS
                }
            }
            
        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    """Test risk manager"""
    rm = RiskManager()
    
    print("="*80)
    print("RISK MANAGEMENT SUMMARY")
    print("="*80)
    
    summary = rm.get_risk_summary()
    
    print(f"\nCapital: Rs.{summary['total_capital']:,.2f}")
    print(f"Exposure: {summary['exposure_percent']:.2f}% (Limit: {rm.MAX_TOTAL_EXPOSURE}%) {' ✅' if summary['within_limits']['exposure'] else ' ❌'}")
    print(f"Cash Reserve: {summary['cash_reserve_percent']:.2f}%")
    
    print(f"\nPositions: {summary['position_count']} (Limit: {rm.MAX_POSITIONS}) {' ✅' if summary['within_limits']['position_count'] else ' ❌'}")
    print(f"Largest Position: {summary['largest_position_percent']:.2f}% (Limit: {rm.MAX_POSITION_SIZE_PERCENT}%) {' ✅' if summary['within_limits']['position_size'] else ' ❌'}")
    print(f"Avg P&L: {summary['avg_position_pnl']:+.2f}%")
    print(f"Near Stop-Loss: {summary['positions_near_stop_loss']} positions")
    
    if summary['options_positions'] > 0:
        print(f"\nOptions: {summary['options_positions']} positions (Rs.{summary['options_invested']:,.2f})")
    
    print(f"\nTotal P&L: Rs.{summary['total_pnl']:+,.2f}")
    
    # Check positions at risk
    print("\n" + "="*80)
    print("POSITIONS AT RISK")
    print("="*80)
    
    at_risk = rm.get_positions_at_risk()
    
    if at_risk:
        print(f"\nFound {len(at_risk)} positions requiring attention:\n")
        for pos in at_risk:
            print(f"{pos['symbol']:12} | P&L: {pos['pnl_percent']:+6.2f}% | {pos['risk_level']:8} | {pos['action']}")
            print(f"             | Entry: Rs.{pos['avg_price']:8.2f} | Current: Rs.{pos['current_price']:8.2f} | Loss: Rs.{pos['pnl']:+,.2f}")
            print()
    else:
        print("\n✅ No positions at immediate risk")
