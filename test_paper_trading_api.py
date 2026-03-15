import requests
from datetime import datetime

# Test Paper Trading API (the one used by stock trading dashboard)
print('=== PAPER TRADING API (Stock Dashboard) ===')
response = requests.get('http://localhost:8000/api/paper-trading/portfolio')
data = response.json()
print(f'Total Capital: ₹{data["total_capital"]:,.0f}')
print(f'Available Cash: ₹{data["available_cash"]:,.0f}')
print(f'Invested Amount: ₹{data["invested_amount"]:,.0f}')
print(f'Total P&L: ₹{data["total_pnl"]:,.0f}')
print(f'Today P&L: ₹{data["today_pnl"]:,.0f}')
print(f'Positions Count: {data["positions_count"]}')
print(f'Updated At: {data["updated_at"]}')
