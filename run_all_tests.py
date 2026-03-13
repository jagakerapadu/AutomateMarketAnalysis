"""
Master Test Runner - Runs all test suites
Unit → Integration → Regression
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import unittest
from datetime import datetime
import traceback


def run_all_tests():
    """Run complete test suite"""
    print("="*80)
    print("  AUTOMATED TRADING SYSTEM - COMPLETE TEST SUITE")
    print("="*80)
    print(f"  Started: {datetime.now().strftime('%I:%M:%S %p, %B %d, %Y')}")
    print("="*80)
    print()
    
    results = {}
    
    # ========================================================================
    # 1. UNIT TESTS
    # ========================================================================
    print("\n" + "="*80)
    print("1. UNIT TESTS - Testing individual components")
    print("="*80)
    print()
    
    try:
        # Risk Manager Tests
        print("Running: Risk Manager Tests...")
        from tests.unit.test_risk_manager import run_tests as run_risk_tests
        results['risk_manager'] = run_risk_tests()
        print()
        
        # Virtual Portfolio Tests
        print("Running: Virtual Portfolio Tests...")
        from tests.unit.test_virtual_portfolio import run_tests as run_portfolio_tests
        results['virtual_portfolio'] = run_portfolio_tests()
        print()
        
    except Exception as e:
        print(f"❌ Error in unit tests: {e}")
        traceback.print_exc()
        results['unit_tests'] = False
    
    # ========================================================================
    # 2. INTEGRATION TESTS
    # ========================================================================
    print("\n" + "="*80)
    print("2. INTEGRATION TESTS - Testing workflows")
    print("="*80)
    print()
    
    try:
        from tests.integration.test_trading_workflows import run_integration_tests
        results['integration'] = run_integration_tests()
        print()
        
    except Exception as e:
        print(f"❌ Error in integration tests: {e}")
        traceback.print_exc()
        results['integration'] = False
    
    # ========================================================================
    # 3. REGRESSION TESTS
    # ========================================================================
    print("\n" + "="*80)
    print("3. REGRESSION TESTS - Validating against March 13 data")
    print("="*80)
    print()
    
    try:
        from tests.regression.test_march13_data import run_regression_tests
        results['regression'] = run_regression_tests()
        print()
        
    except Exception as e:
        print(f"❌ Error in regression tests: {e}")
        traceback.print_exc()
        results['regression'] = False
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("  FINAL TEST SUMMARY")
    print("="*80)
    print()
    
    total_suites = len(results)
    passed_suites = sum(1 for v in results.values() if v)
    failed_suites = total_suites - passed_suites
    
    print(f"  Test Suites Run: {total_suites}")
    print(f"  Passed: {passed_suites} ✅")
    print(f"  Failed: {failed_suites} ❌")
    print()
    
    # Detailed breakdown
    for suite_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"    {suite_name:20} : {status}")
    
    print()
    print("="*80)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("  [SUCCESS] ALL TEST SUITES PASSED!")
        print("  [READY] System is ready for live trading")
    else:
        print("  [WARNING] SOME TEST SUITES FAILED")
        print("  [CRITICAL] DO NOT proceed to live trading until fixed")
    
    print("="*80)
    print(f"  Completed: {datetime.now().strftime('%I:%M:%S %p')}")
    print("="*80)
    print()
    
    return all_passed


if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
