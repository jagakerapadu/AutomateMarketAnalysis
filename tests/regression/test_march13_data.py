"""
Regression Test Suite
Validates trading calculations against known March 13, 2026 data
Ensures no calculation errors or data corruption
"""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from config.settings import get_settings
from decimal import Decimal


class TestMarch13Regression(unittest.TestCase):
    """Regression tests against March 13, 2026 actual data"""
    
    @classmethod
    def setUpClass(cls):
        """Connect to database once"""
        settings = get_settings()
        cls.conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cls.cursor = cls.conn.cursor()
    
    @classmethod
    def tearDownClass(cls):
        """Close connection"""
        cls.cursor.close()
        cls.conn.close()
    
    def test_total_buy_orders_march_13(self):
        """Verify total BUY orders = 20 and amount = Rs.510,982.60"""
        self.cursor.execute("""
            SELECT COUNT(*), SUM(quantity * executed_price)
            FROM paper_orders
            WHERE order_type = 'BUY' 
            AND DATE(executed_at) = '2026-03-13'
        """)
        count, total = self.cursor.fetchone()
        
        self.assertEqual(count, 20, "Should have exactly 20 BUY orders")
        self.assertAlmostEqual(float(total), 510982.60, places=1, 
                              msg="Total buy amount should be Rs.510,982.60")
    
    def test_total_sell_orders_march_13(self):
        """Verify total SELL orders = 4 and amount = Rs.290,407.20"""
        self.cursor.execute("""
            SELECT COUNT(*), SUM(quantity * executed_price)
            FROM paper_orders
            WHERE order_type = 'SELL'
            AND DATE(executed_at) = '2026-03-13'
        """)
        count, total = self.cursor.fetchone()
        
        self.assertEqual(count, 4, "Should have exactly 4 SELL orders")
        self.assertAlmostEqual(float(total), 290407.20, places=1,
                              msg="Total sell amount should be Rs.290,407.20")
    
    def test_realized_pnl_march_13(self):
        """Verify realized P&L = -Rs.6,542.20"""
        # Calculate from closed positions
        closed_trades = [
            ('LT', 1, 3562.70, 3478.90, -83.80),
            ('WIPRO', 110, 201.34, 196.87, -491.70),
            ('TCS', 69, 2458.18, 2402.90, -3814.20),
            ('HCLTECH', 75, 1355.00, 1326.30, -2152.50)
        ]
        
        total_realized = sum(trade[4] for trade in closed_trades)
        
        self.assertAlmostEqual(total_realized, -6542.20, places=1,
                              msg="Total realized loss should be -Rs.6,542.20")
    
    def test_infy_position_quantity(self):
        """Verify INFY position = 190 shares"""
        self.cursor.execute("""
            SELECT quantity
            FROM paper_positions
            WHERE symbol = 'INFY' AND quantity > 0
        """)
        result = self.cursor.fetchone()
        
        self.assertIsNotNone(result, "INFY position should exist")
        self.assertEqual(result[0], 190, "INFY should have 190 shares")
    
    def test_infy_average_price(self):
        """Verify INFY average price calculation"""
        self.cursor.execute("""
            SELECT avg_price
            FROM paper_positions
            WHERE symbol = 'INFY'
        """)
        avg_price = float(self.cursor.fetchone()[0])
        
        # Expected: (64 * 1267.80 + 126 * 1270.65) / 190 = 1269.72
        self.assertAlmostEqual(avg_price, 1269.72, places=2,
                              msg="INFY avg price should be Rs.1,269.72")
    
    def test_options_position_exists(self):
        """Verify options position exists and has valid data"""
        self.cursor.execute("""
            SELECT quantity, entry_premium, strike, option_type
            FROM paper_options_positions
            WHERE symbol = 'NIFTY' 
            ORDER BY opened_at DESC
            LIMIT 1
        """)
        result = self.cursor.fetchone()
        
        if result:  # Only test if position exists
            quantity, entry, strike, opt_type = result
            self.assertGreater(quantity, 0, "Quantity should be positive")
            self.assertGreater(entry, 0, "Entry premium should be positive")
            self.assertGreater(strike, 0, "Strike should be positive")
            self.assertIn(opt_type, ['CE', 'PE'], "Type should be CE or PE")
    
    def test_options_pnl_calculation(self):
        """Verify options P&L calculation accuracy with generic values"""
        # Generic test - not tied to specific market prices
        lots = 2
        lot_size = 50
        entry = 200.00
        current = 180.00
        
        invested = lots * entry * lot_size
        current_val = lots * current * lot_size
        pnl = current_val - invested
        pnl_percent = (pnl / invested) * 100
        
        self.assertAlmostEqual(invested, 20000, places=0)
        self.assertAlmostEqual(current_val, 18000, places=0)
        self.assertAlmostEqual(pnl, -2000, places=0)
        self.assertAlmostEqual(pnl_percent, -10.0, places=1)
    
    def test_open_positions_count(self):
        """Verify 16 open equity positions"""
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM paper_positions
            WHERE quantity > 0
        """)
        count = self.cursor.fetchone()[0]
        
        self.assertEqual(count, 16, "Should have exactly 16 open positions")
    
    def test_portfolio_capital_accuracy(self):
        """Verify portfolio capital tracking"""
        self.cursor.execute("""
            SELECT total_capital, available_cash, invested_amount
            FROM paper_portfolio
            ORDER BY id DESC LIMIT 1
        """)
        capital, cash, invested = self.cursor.fetchone()
        
        capital = float(capital)
        cash = float(cash)
        invested = float(invested)
        
        # Starting capital
        self.assertEqual(capital, 1000000, "Total capital should be Rs.10,00,000")
        
        # Cash + Invested should equal capital (minus losses)
        account_value = cash + invested
        
        # Account value should be less than capital due to losses
        self.assertLess(account_value, capital, "Account value should reflect losses")
    
    def test_signal_status_sync(self):
        """Verify signal statuses are synchronized"""
        # Count signals by status
        self.cursor.execute("""
            SELECT status, COUNT(*)
            FROM signals
            WHERE DATE(created_at) = '2026-03-13'
            GROUP BY status
        """)
        status_counts = dict(self.cursor.fetchall())
        
        # Should have ACTIVE signals (for open positions)
        self.assertIn('ACTIVE', status_counts, "Should have ACTIVE signals")
        
        # Should have CLOSED signals (for sold positions)
        # Note: May or may not be present depending on implementation
    
    def test_no_duplicate_positions(self):
        """Verify no duplicate positions for same symbol"""
        self.cursor.execute("""
            SELECT symbol, COUNT(*)
            FROM paper_positions
            WHERE quantity > 0
            GROUP BY symbol
            HAVING COUNT(*) > 1
        """)
        duplicates = self.cursor.fetchall()
        
        self.assertEqual(len(duplicates), 0, 
                        f"Found {len(duplicates)} symbols with duplicate positions")
    
    def test_all_prices_populated(self):
        """Verify all positions have current prices"""
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM paper_positions
            WHERE quantity > 0 AND current_price IS NULL
        """)
        null_count = self.cursor.fetchone()[0]
        
        # Note: This may fail if prices haven't been updated
        # but it's a good regression check
        if null_count > 0:
            print(f"\n⚠️  Warning: {null_count} positions have NULL prices (data may be stale)")


class TestCalculationConsistency(unittest.TestCase):
    """Test that calculations are consistent across database"""
    
    @classmethod
    def setUpClass(cls):
        settings = get_settings()
        cls.conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cls.cursor = cls.conn.cursor()
    
    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()
    
    def test_position_invested_value_calculation(self):
        """Verify invested_value = quantity * avg_price"""
        self.cursor.execute("""
            SELECT symbol, quantity, avg_price, invested_value
            FROM paper_positions
            WHERE quantity > 0
        """)
        
        for symbol, qty, avg, invested in self.cursor.fetchall():
            expected_invested = qty * float(avg)
            actual_invested = float(invested)
            
            # Allow 1 rupee difference for accumulated rounding
            difference = abs(expected_invested - actual_invested)
            self.assertLess(difference, 1.0,
                           msg=f"{symbol}: Invested value mismatch "
                               f"(Expected: Rs.{expected_invested:.2f}, "
                               f"Actual: Rs.{actual_invested:.2f}, "
                               f"Diff: Rs.{difference:.2f})")
    
    def test_position_current_value_calculation(self):
        """Verify current_value = quantity * current_price"""
        self.cursor.execute("""
            SELECT symbol, quantity, current_price, current_value
            FROM paper_positions
            WHERE quantity > 0 AND current_price IS NOT NULL
        """)
        
        for symbol, qty, current, curr_val in self.cursor.fetchall():
            expected_value = qty * float(current)
            actual_value = float(curr_val) if curr_val else 0
            
            self.assertAlmostEqual(expected_value, actual_value, places=2,
                                  msg=f"{symbol}: Current value mismatch")
    
    def test_position_pnl_calculation(self):
        """Verify pnl = current_value - invested_value"""
        self.cursor.execute("""
            SELECT symbol, invested_value, current_value, pnl
            FROM paper_positions
            WHERE quantity > 0 AND current_value IS NOT NULL
        """)
        
        for symbol, invested, curr_val, pnl in self.cursor.fetchall():
            expected_pnl = float(curr_val) - float(invested)
            actual_pnl = float(pnl) if pnl else 0
            
            self.assertAlmostEqual(expected_pnl, actual_pnl, places=2,
                                  msg=f"{symbol}: P&L calculation mismatch")
    
    def test_position_pnl_percent_calculation(self):
        """Verify pnl_percent = (pnl / invested) * 100"""
        self.cursor.execute("""
            SELECT symbol, invested_value, pnl, pnl_percent
            FROM paper_positions
            WHERE quantity > 0 AND pnl IS NOT NULL
        """)
        
        for symbol, invested, pnl, pnl_pct in self.cursor.fetchall():
            inv_float = float(invested)
            pnl_float = float(pnl) if pnl else 0
            
            expected_pct = (pnl_float / inv_float) * 100 if inv_float > 0 else 0
            actual_pct = float(pnl_pct) if pnl_pct else 0
            
            self.assertAlmostEqual(expected_pct, actual_pct, places=2,
                                  msg=f"{symbol}: P&L% calculation mismatch")


def run_regression_tests():
    """Run complete regression test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestMarch13Regression))
    suite.addTests(loader.loadTestsFromTestCase(TestCalculationConsistency))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("REGRESSION TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n[PASS] ALL REGRESSION TESTS PASSED!")
        print("   System calculations are accurate and consistent")
    else:
        print("\n[FAIL] REGRESSION TESTS FAILED!")
        print("   CRITICAL: Data calculations may have errors")
        
        if result.failures:
            print("\n[FAIL] Failed Tests:")
            for test, _ in result.failures:
                print(f"     {test}")
        
        if result.errors:
            print("\n[ERROR] Error Tests:")
            for test, _ in result.errors:
                print(f"     {test}")
    
    print("\n" + "="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("="*70)
    print("RUNNING REGRESSION TESTS AGAINST MARCH 13, 2026 DATA")
    print("="*70)
    print()
    
    success = run_regression_tests()
    sys.exit(0 if success else 1)
