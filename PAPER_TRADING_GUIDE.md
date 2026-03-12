# 📊 Paper Trading Guide

## What is Paper Trading?

Paper trading allows you to test your trading strategies with **virtual money** and **real market data** - perfect for learning and testing without financial risk!

---

## ✨ Key Features

✅ **₹10,00,000 Virtual Capital** - Start with 10 lakhs virtual money  
✅ **Live Market Data** - Real-time prices from Zerodha API  
✅ **Auto-Execution** - Trading signals automatically executed  
✅ **Risk Management** - Max 20% capital per trade  
✅ **Auto Exit** - Target: +3% profit | Stop Loss: -2% loss  
✅ **Complete Tracking** - All positions, orders, and P&L tracked  

---

## 🚀 Quick Start

### 1. Test the System
```bash
python test_paper_trading.py
```
This will verify:
- Virtual portfolio creation
- Order placement (BUY/SELL)
- Position tracking
- P&L calculation

### 2. Start Paper Trading Engine
```bash
python start_paper_trading.py
```
This will:
- Run every 60 seconds
- Fetch live market prices
- Execute pending trading signals
- Monitor positions for exit conditions
- Only trade during market hours (9:15 AM - 3:30 PM IST)

### 3. View Paper Trading Dashboard
```
http://localhost:3000/paper-trading
```
Shows:
- Portfolio summary (capital, P&L, positions)
- Current positions with live P&L
- Order history
- Trading statistics

---

## 📡 API Endpoints

### Get Portfolio Summary
```bash
GET http://localhost:8000/api/paper-trading/portfolio
```
Returns total capital, available cash, invested amount, total P&L, today's P&L

### Get Current Positions
```bash
GET http://localhost:8000/api/paper-trading/positions
```
Returns all open positions with current prices and P&L

### Get Order History
```bash
GET http://localhost:8000/api/paper-trading/orders?limit=50
```
Returns recent orders (BUY/SELL)

### Get Statistics
```bash
GET http://localhost:8000/api/paper-trading/stats
```
Returns total orders, buy/sell counts, P&L stats

### Place Manual Order
```bash
POST http://localhost:8000/api/paper-trading/orders
{
  "symbol": "INFY",
  "order_type": "BUY",
  "quantity": 100,
  "price": 1275.50
}
```

### Reset Portfolio
```bash
POST http://localhost:8000/api/paper-trading/portfolio/reset
```
Resets to initial ₹10,00,000 capital (clears all positions and orders)

---

## 📋 How It Works

### 1️⃣ **Signal Detection**
Your trading strategies generate signals:
- RSI Oversold/Overbought
- SMA Crossover
- Volume Breakout
- MACD signals

### 2️⃣ **Auto-Execution**
Paper trading engine:
1. Fetches pending signals (confidence ≥ 70%)
2. Gets live market price from Zerodha
3. Checks if price is close to signal entry (±2%)
4. Calculates position size (max 20% of available cash)
5. Executes virtual order

### 3️⃣ **Position Management**
Engine monitors positions:
- Updates prices every 60 seconds
- Checks exit conditions:
  - ✅ Exit if profit ≥ 3%
  - ❌ Exit if loss ≥ 2%
- Automatically places SELL orders

### 4️⃣ **P&L Tracking**
All trades tracked in database:
- Entry/exit prices
- Realized P&L (closed positions)
- Unrealized P&L (open positions)
- Win rate, best/worst trades

---

## 💡 Example Workflow

```bash
# Morning: Start the systems
python setup_credentials.py          # Generate Zerodha token
python start_api.py                  # Start API server (background)
cd dashboard && npm run dev          # Start dashboard (background)

# Start paper trading
python start_paper_trading.py        # Main trading engine
```

**Output:**
```
============================================================
🚀 Starting Paper Trading Engine
============================================================

Features:
  ✅ Virtual portfolio with ₹10,00,000 capital
  ✅ Live market data from Zerodha
  ✅ Auto-execution of trading signals
  ✅ Real-time position tracking
  ✅ Automatic stop-loss and target management

Settings:
  • Update interval: 60 seconds
  • Risk per trade: 20% max
  • Target: +3% | Stop Loss: -2%
  • Market hours: 9:15 AM - 3:30 PM IST

============================================================

✅ Engine initialized successfully
⏰ Starting trading loop...

Press Ctrl+C to stop
============================================================

Running paper trading cycle
📈 Market is OPEN
Found 3 pending signals
✅ Executed: BUY 100 INFY @ ₹1275.50 (Confidence: 77%)

📊 Portfolio Summary:
   Total Capital: ₹1,000,000.00
   Available Cash: ₹872,450.00
   Invested: ₹127,550.00
   Total P&L: ₹0.00
   Today P&L: ₹0.00
   Positions: 1
```

---

## 🎯 Trading Rules

### Entry Rules
- **Confidence Filter**: Only signals ≥ 70% confidence executed
- **Price Check**: Current price must be within 2% of signal entry price
- **Cash Requirement**: Must have sufficient available cash
- **Position Size**: Maximum 20% of available capital per trade

### Exit Rules
- **Profit Target**: Auto-exit when position gains ≥ 3%
- **Stop Loss**: Auto-exit when position loses ≥ 2%
- **Market Close**: Positions held overnight (no forced exit)

### Risk Management
- **Max Capital per Trade**: 20% (₹2,00,000 on ₹10,00,000)
- **Diversification**: Can hold multiple positions simultaneously
- **Cash Reserve**: Always maintains available cash for new trades

---

## 📊 Database Tables

### `paper_portfolio`
Stores overall portfolio status:
- `total_capital`: Starting capital
- `available_cash`: Cash available for new trades
- `invested_amount`: Total invested in positions
- `total_pnl`: All-time P&L
- `today_pnl`: Today's P&L

### `paper_positions`
Tracks open positions:
- `symbol`, `quantity`, `avg_price`
- `current_price`, `current_value`
- `pnl`, `pnl_percent`
- `opened_at`, `updated_at`

### `paper_orders`
Records all orders:
- `order_id`, `symbol`, `order_type` (BUY/SELL)
- `quantity`, `executed_price`
- `status`, `signal_id`
- `placed_at`, `executed_at`

---

## 🔧 Configuration

### Change Initial Capital
Edit `start_paper_trading.py`:
```python
portfolio = VirtualPortfolio(initial_capital=500000)  # 5 lakhs
```

### Adjust Update Interval
```bash
python start_paper_trading.py --interval 30  # Update every 30 seconds
```

### Disable Auto-Execution
```bash
python start_paper_trading.py --no-auto  # Manual trading only
```

### Change Risk Settings
Edit `services/paper_trading/paper_trading_engine.py`:
```python
# Line 165: Risk per trade (default 20%)
max_trade_value = available_cash * 0.10  # Change to 10%

# Lines 253-257: Exit conditions
if pnl_percent >= 5:  # Change target to 5%
    should_exit = True
elif pnl_percent <= -1:  # Change stop-loss to 1%
    should_exit = True
```

---

## 📈 Monitoring

### Real-Time Logs
The engine provides detailed logs:
```
2026-03-12 10:30:15 - paper_trading_engine - INFO - Running paper trading cycle
2026-03-12 10:30:16 - paper_trading_engine - INFO - Found 2 pending signals
2026-03-12 10:30:17 - virtual_portfolio - INFO - Order executed: BUY 150 RELIANCE @ ₹1387.00
2026-03-12 10:30:45 - paper_trading_engine - INFO - 🔔 Exited position: INFY - Target hit: +3.24%
```

### Check Portfolio Anytime
```bash
python -c "from services.paper_trading.virtual_portfolio import VirtualPortfolio; p=VirtualPortfolio(); print(p.get_portfolio_summary())"
```

### View Positions
```bash
python -c "from services.paper_trading.virtual_portfolio import VirtualPortfolio; p=VirtualPortfolio(); [print(pos) for pos in p.get_positions()]"
```

---

## ❓ Troubleshooting

### "No live prices available"
**Issue**: Zerodha access token expired  
**Fix**: Regenerate token
```bash
python setup_credentials.py  # Select option 3
```

### "Insufficient funds"
**Issue**: Not enough cash for new trade  
**Fix**: Wait for positions to close or reduce position sizes

### "No pending signals"
**Issue**: All signals already executed or too old  
**Fix**: Generate fresh signals
```bash
python populate_real_data.py  # Fetches new data and generates signals
```

### Reset Everything
```bash
# Via API
curl -X POST http://localhost:8000/api/paper-trading/portfolio/reset

# Or via Python
python -c "from services.paper_trading.virtual_portfolio import VirtualPortfolio; VirtualPortfolio().reset_portfolio()"
```

---

## 🎓 Best Practices

1. **Start Small**: Test with default ₹10L before increasing capital
2. **Monitor Closely**: Watch first few days to understand behavior
3. **Review Performance**: Check win rate, avg P&L, best/worst trades
4. **Adjust Rules**: Fine-tune exit conditions based on results
5. **Compare with Real**: Match paper trading results with actual market trades
6. **Learn from Mistakes**: Paper trading is for learning - analyze losing trades

---

## 📞 Support

For issues or questions:
1. Check logs in terminal output
2. Review API docs: http://localhost:8000/api/docs
3. Test individual components: `python test_paper_trading.py`
4. Check database: `python system_status.py`

---

## 🚦 Status Check

**Is paper trading working?**
```bash
# 1. Check API
curl http://localhost:8000/api/paper-trading/stats

# 2. View dashboard
# Open: http://localhost:3000/paper-trading

# 3. Check engine logs
# Terminal should show "Running paper trading cycle" every 60 seconds
```

---

**Happy Paper Trading! 📈💰**
