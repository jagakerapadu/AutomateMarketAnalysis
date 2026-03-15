import psycopg2

# Connect directly to database
conn = psycopg2.connect(
    host="localhost",
    port=5433,  # Docker postgres port
    database="market_analysis",
    user="postgres",
    password="root"
)

cur = conn.cursor()

print("=== DIRECT DATABASE CHECK ===")
cur.execute("SELECT total_capital, available_cash, invested_amount, total_pnl, today_pnl, updated_at FROM paper_portfolio WHERE id = 1")
row = cur.fetchone()
print(f'Total Capital: ₹{row[0]:,.0f}')
print(f'Available Cash: ₹{row[1]:,.0f}')
print(f'Invested Amount: ₹{row[2]:,.0f}')
print(f'Total P&L: ₹{row[3]:,.0f}')
print(f'Today P&L: ₹{row[4]:,.0f}')
print(f'Updated At: {row[5]}')

cur.close()
conn.close()
