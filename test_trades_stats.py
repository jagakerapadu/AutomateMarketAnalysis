"""Test trade stats endpoint"""
import requests

response = requests.get("http://localhost:8000/api/trades/stats")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"\nTrade Statistics:")
    print(f"  Total Trades:    {data['total_trades']}")
    print(f"  Win Rate:         {data['win_rate']}%")
    print(f"  Avg Win:         ₹{data['avg_win']:,.2f}")
    print(f"  Avg Loss:        ₹{data['avg_loss']:,.2f}")
    print(f"  Total P&L:       ₹{data['total_pnl']:,.2f}")
else:
    print(f"Error: {response.text}")
