"""Test the fixed portfolio API endpoint"""
import requests
import json

API_URL = "http://localhost:8000"

print("\n" + "=" * 80)
print("TESTING FIXED PORTFOLIO API")
print("=" * 80)

try:
    # Test portfolio summary
    print("\n1. Testing /api/portfolio/summary...")
    response = requests.get(f"{API_URL}/api/portfolio/summary", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API Response:")
        print(f"   Total Capital:    ₹{data['total_capital']:,.2f}")
        print(f"   Available Cash:   ₹{data['available']:,.2f}")
        print(f"   Invested:         ₹{data['invested']:,.2f}")
        print(f"   Total P&L:        ₹{data['total_pnl']:,.2f}  {'📈' if data['total_pnl'] >= 0 else '📉'}")
        print(f"   Open Positions:   {data['open_positions']}")
        
        # Verify it's showing the correct P&L
        print("\n" + "=" * 80)
        if data['total_pnl'] < 0:
            print("✅ CORRECT! Dashboard should now show LOSS (not fake profit)")
            print(f"   Expected: ~₹-9,083.70")
            print(f"   Got:       ₹{data['total_pnl']:,.2f}")
        else:
            print("⚠️  Still showing profit? Check if API server was restarted.")
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(response.text)
    
    # Test positions endpoint
    print("\n2. Testing /api/portfolio/positions...")
    response = requests.get(f"{API_URL}/api/portfolio/positions", timeout=5)
    
    if response.status_code == 200:
        positions = response.json()
        print(f"✅ Found {len(positions)} positions")
        
        if positions:
            print("\nTop 5 Positions:")
            for pos in sorted(positions, key=lambda x: x['unrealized_pnl'], reverse=True)[:5]:
                pnl_icon = "📈" if pos['unrealized_pnl'] >= 0 else "📉"
                print(f"   {pos['symbol']:<15} Qty: {pos['quantity']:<5} P&L: ₹{pos['unrealized_pnl']:>10.2f} {pnl_icon}")
    else:
        print(f"❌ Error: Status {response.status_code}")

except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to API server!")
    print("   Make sure the API is running: py start_api.py")
    print("   API should be at: http://localhost:8000")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. If API is not running: py start_api.py")
print("2. If API shows old data: Restart API server (CTRL+C then py start_api.py)")
print("3. Refresh dashboard: Press F5 in browser")
print("4. Dashboard should now show correct P&L: ₹-9,083.70 (LOSS)")
print("=" * 80 + "\n")
