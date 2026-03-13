"""
Unit Tests for Risk Manager
Tests position sizing, limits, and exit conditions
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.paper_trading.risk_manager import RiskManager


class TestRiskManager(unittest.TestCase):
    """Test cases for RiskManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_manager = RiskManager()
        self.risk_manager.MAX_POSITION_SIZE_PERCENT = 10
        self.risk_manager.MAX_TOTAL_EXPOSURE = 80
        self.risk_manager.STOP_LOSS_PERCENT = 2
        self.risk_manager.TARGET_PROFIT_PERCENT = 3
    
    def test_position_size_within_limit(self):
        """Test position size validation - within limit"""
        symbol = "RELIANCE"
        quantity = 10
        price = 1400
        total_capital = 1000000
        
        # 10 * 1400 = 14,000 = 1.4% (well within 10%)
        is_valid, reason, suggested_qty = self.risk_manager.validate_position_size(
            symbol, quantity, price, total_capital
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(quantity, suggested_qty)
        self.assertIn("within limits", reason.lower())
    
    def test_position_size_exceeds_limit(self):
        """Test position size validation - exceeds limit"""
        symbol = "RELIANCE"
        quantity = 100
        price = 1400
        total_capital = 1000000
        
        # 100 * 1400 = 140,000 = 14% (exceeds 10%)
        is_valid, reason, suggested_qty = self.risk_manager.validate_position_size(
            symbol, quantity, price, total_capital
        )
        
        self.assertFalse(is_valid)
        self.assertLess(suggested_qty, quantity)
        self.assertIn("exceeds limit", reason.lower())
        
        # Suggested should be within 10%
        suggested_value = suggested_qty * price
        suggested_percent = (suggested_value / total_capital) * 100
        self.assertLessEqual(suggested_percent, 10)
    
    def test_stop_loss_trigger_equity(self):
        """Test stop-loss detection for equity"""
        entry_price = 1400
        current_price = 1370  # -2.14% loss
        
        should_exit, reason = self.risk_manager.should_exit_position(
            "RELIANCE", entry_price, current_price, is_options=False
        )
        
        self.assertTrue(should_exit)
        self.assertIn("STOP-LOSS", reason)
    
    def test_target_hit_equity(self):
        """Test target detection for equity"""
        entry_price = 1400
        current_price = 1443  # +3.07% profit
        
        should_exit, reason = self.risk_manager.should_exit_position(
            "RELIANCE", entry_price, current_price, is_options=False
        )
        
        self.assertTrue(should_exit)
        self.assertIn("TARGET", reason)
    
    def test_no_exit_within_range(self):
        """Test that position is held when within target/stop-loss range"""
        entry_price = 1400
        current_price = 1410  # +0.71% - between stop-loss and target
        
        should_exit, reason = self.risk_manager.should_exit_position(
            "RELIANCE", entry_price, current_price, is_options=False
        )
        
        self.assertFalse(should_exit)
    
    def test_options_stop_loss_wider(self):
        """Test that options have wider stop-loss (40%)"""
        entry_premium = 200
        current_premium = 115  # -42.5% loss
        
        should_exit, reason = self.risk_manager.should_exit_position(
            "NIFTY", entry_premium, current_premium, is_options=True
        )
        
        self.assertTrue(should_exit)
        self.assertIn("OPTIONS STOP-LOSS", reason)
    
    def test_options_normal_loss_not_stopped(self):
        """Test that small options loss doesn't trigger stop"""
        entry_premium = 200
        current_premium = 180  # -10% loss (within 40% limit)
        
        should_exit, reason = self.risk_manager.should_exit_position(
            "NIFTY", entry_premium, current_premium, is_options=True
        )
        
        self.assertFalse(should_exit)
    
    def test_optimal_position_size_calculation(self):
        """Test optimal position size with confidence"""
        # High confidence (90%) should give larger position
        symbol = "INFY"
        price = 1270
        confidence = 90
        
        # Mock database connection
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (1000000, 500000)  # capital, cash
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_connect.return_value.cursor.return_value.close = MagicMock()
            mock_connect.return_value.close = MagicMock()
            
            quantity = self.risk_manager.calculate_optimal_position_size(
                symbol, price, confidence
            )
            
            # Should allocate position
            self.assertGreater(quantity, 0)
            
            # Position should be within 10% of capital
            position_value = quantity * price
            position_percent = (position_value / 1000000) * 100
            self.assertLessEqual(position_percent, 10)
    
    def test_low_confidence_smaller_position(self):
        """Test that low confidence results in smaller position"""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (1000000, 500000)
            mock_connect.return_value.cursor.return_value = mock_cursor
            
            symbol = "INFY"
            price = 1270
            
            # Test low vs high confidence
            qty_low = self.risk_manager.calculate_optimal_position_size(symbol, price, 70)
            qty_high = self.risk_manager.calculate_optimal_position_size(symbol, price, 95)
            
            # High confidence should give more shares
            self.assertGreater(qty_high, qty_low)


class TestPositionSizing(unittest.TestCase):
    """Test cases for position sizing logic"""
    
    def test_position_size_percentage_calculation(self):
        """Test correct percentage calculation"""
        rm = RiskManager()
        
        # Test case: 50,000 position on 1M capital = 5%
        quantity = 50
        price = 1000
        total_capital = 1000000
        
        position_value = quantity * price  # 50,000
        position_percent = (position_value / total_capital) * 100  # 5%
        
        is_valid, _, _ = rm.validate_position_size("TEST", quantity, price, total_capital)
        
        self.assertTrue(is_valid)  # 5% < 10% limit
    
    def test_boundary_condition_exactly_10_percent(self):
        """Test position at exactly 10% limit"""
        rm = RiskManager()
        
        # Exactly 10%
        quantity = 100
        price = 1000
        total_capital = 1000000
        
        is_valid, _, _ = rm.validate_position_size("TEST", quantity, price, total_capital)
        
        self.assertTrue(is_valid)  # At limit is OK
    
    def test_position_over_limit_gets_adjusted(self):
        """Test that oversized position gets adjusted down"""
        rm = RiskManager()
        
        # 15% position
        quantity = 150
        price = 1000
        total_capital = 1000000
        
        is_valid, reason, suggested_qty = rm.validate_position_size(
            "TEST", quantity, price, total_capital
        )
        
        self.assertFalse(is_valid)
        self.assertLess(suggested_qty, quantity)
        
        # Suggested should be within 10%
        suggested_value = suggested_qty * price
        suggested_percent = (suggested_value / total_capital) * 100
        self.assertLessEqual(suggested_percent, 10)


class TestStopLossLogic(unittest.TestCase):
    """Test stop-loss and target exit logic"""
    
    def setUp(self):
        self.rm = RiskManager()
    
    def test_stop_loss_at_exact_2_percent(self):
        """Test stop-loss triggers at exactly -2%"""
        entry = 1000
        current = 980  # Exactly -2%
        
        should_exit, _ = self.rm.should_exit_position("TEST", entry, current)
        self.assertTrue(should_exit)
    
    def test_stop_loss_beyond_2_percent(self):
        """Test stop-loss triggers beyond -2%"""
        entry = 1000
        current = 970  # -3%
        
        should_exit, _ = self.rm.should_exit_position("TEST", entry, current)
        self.assertTrue(should_exit)
    
    def test_no_exit_at_1_percent_loss(self):
        """Test that -1% loss doesn't trigger exit"""
        entry = 1000
        current = 990  # -1%
        
        should_exit, _ = self.rm.should_exit_position("TEST", entry, current)
        self.assertFalse(should_exit)
    
    def test_target_at_3_percent(self):
        """Test target triggers at +3%"""
        entry = 1000
        current = 1030  # +3%
        
        should_exit, _ = self.rm.should_exit_position("TEST", entry, current)
        self.assertTrue(should_exit)
    
    def test_options_wider_stop_loss(self):
        """Test options have 40% stop-loss"""
        entry = 200
        current = 115  # -42.5%
        
        should_exit, _ = self.rm.should_exit_position("NIFTY", entry, current, is_options=True)
        self.assertTrue(should_exit)
        
        # But -20% should not trigger
        current = 160  # -20%
        should_exit, _ = self.rm.should_exit_position("NIFTY", entry, current, is_options=True)
        self.assertFalse(should_exit)


class TestRiskLimits(unittest.TestCase):
    """Test risk limit enforcement"""
    
    def test_max_positions_limit(self):
        """Test maximum position count enforcement"""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (20,)  # At limit
            mock_connect.return_value.cursor.return_value = mock_cursor
            
            rm = RiskManager()
            rm.MAX_POSITIONS = 20
            
            can_add, reason = rm.check_position_limits()
            
            self.assertFalse(can_add)
            self.assertIn("Maximum positions", reason)
    
    def test_total_exposure_limit(self):
        """Test total exposure limit enforcement"""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = MagicMock()
            # Capital: 1M, Already invested: 750K = 75%
            mock_cursor.fetchone.return_value = (1000000, 750000)
            mock_connect.return_value.cursor.return_value = mock_cursor
            
            rm = RiskManager()
            rm.MAX_TOTAL_EXPOSURE = 80
            
            # Adding 100K more would make it 85%
            can_add, reason = rm.check_total_exposure(100000)
            
            self.assertFalse(can_add)
            self.assertIn("exceed", reason.lower())


def run_tests():
    """Run all risk manager tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPositionSizing))
    suite.addTests(loader.loadTestsFromTestCase(TestStopLossLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskLimits))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n[PASS] ALL TESTS PASSED!")
    else:
        print("\n[FAIL] SOME TESTS FAILED!")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
