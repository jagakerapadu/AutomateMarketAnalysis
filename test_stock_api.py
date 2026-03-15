import requests
from datetime import datetime

# Test Stock Trading API
print('=== STOCK TRADING API ===')
response = requests.get('http://localhost:8000/api/portfolio/summary')
data = response.json()
print(f'Total Capital: ₹{data["total_capital"]:,.0f}')
print(f'Available: ₹{data["available"]:,.0f}')
print(f'Invested: ₹{data["invested"]:,.0f}')
print(f'Total P&L: ₹{data["total_pnl"]:,.0f}')
print(f'Open Positions: {data["open_positions"]}')
print(f'Last Updated: {data.get("last_updated", "N/A")}')

# Also check database directly
print('\n=== DIRECT DATABASE CHECK ===')
import psycopg2
conn = psycopg2.connect("postgresql://postgres:root@localhost:5432/market_analysis")
cur = conn.cursor()
cur.execute("SELECT total_capital, available_cash, invested_amount, total_pnl FROM paper_portfolio WHERE id = 1")
row = cur.fetchone()
print(f'DB - Total Capital: ₹{row[0]:,.0f}')
print(f'DB - Available Cash: ₹{row[1]:,.0f}')
print(f'DB - Invested: ₹{row[2]:,.0f}')
print(f'DB - Total P&L: ₹{row[3]:,.0f}')
cur.close()
conn.close()
