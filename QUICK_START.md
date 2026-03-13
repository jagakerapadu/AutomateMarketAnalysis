# Quick Start Guide - Automated Trading System

## ⚡ Daily Trading Routine

### 1. Morning Setup (Before Market Opens - 8:00 AM)

```powershell
# Update yesterday's closing prices
py update_paper_prices.py

# Check current risk status
py services\paper_trading\risk_manager.py

# Run regression tests to verify system integrity
$env:PYTHONPATH = "$PWD"; py tests\regression\test_march13_data.py
```

---

### 2. During Market Hours (9:15 AM - 3:30 PM)

**Option A: Automated Monitoring (Recommended)**
```powershell
# Start continuous monitoring (keeps running)
py monitor_positions.py
```
This will:
- Update prices every 30 seconds
- Alert you when positions hit stop-loss
- Show real-time P&L
- Display risk status

**Option B: Manual Checks**
```powershell
# Check prices and status manually
py update_paper_prices.py
py services\paper_trading\risk_manager.py
```

---

### 3. After Market Close (4:00 PM onwards)

```powershell
# Generate daily trading report
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
py analyze_march13_trading.py

# Run all tests to verify data integrity
py run_all_tests.py
```

---

## 🧪 Testing Commands

### Run All Tests (Recommended before any changes)
```powershell
py run_all_tests.py
```

### Run Individual Test Suites
```powershell
# Risk manager tests (19 tests)
$env:PYTHONPATH = "$PWD"; py tests\unit\test_risk_manager.py

# Portfolio tests (14 tests)
$env:PYTHONPATH = "$PWD"; py tests\unit\test_virtual_portfolio.py

# Regression tests (16 tests) - Validates against March 13 data
$env:PYTHONPATH = "$PWD"; py tests\regression\test_march13_data.py
```

---

## 🛠️ Risk Management

### View Current Risk Status
```powershell
py services\paper_trading\risk_manager.py
```

Shows:
- Total capital and deployed amount
- Position count and limits
- Positions at risk (CRITICAL/HIGH/MEDIUM/LOW)
- Risk alerts

### Risk Limits (Current Configuration)
- **Max per position:** 10% of capital
- **Max total exposure:** 80% of capital
- **Max positions:** 20
- **Equity stop-loss:** -2%
- **Equity target:** +3%
- **Options stop-loss:** -40%
- **Options target:** +50%

---

## 📊 Generate Reports

### Daily Trading Analysis
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
py analyze_march13_trading.py
```

### View Virtual Portfolio
```powershell
py services\paper_trading\virtual_portfolio.py
```

---

## 🚨 Troubleshooting

### Module Import Errors
```powershell
# Set Python path before running tests
$env:PYTHONPATH = "$PWD"
```

### Unicode/Encoding Errors
```powershell
# Set UTF-8 encoding for Rupee symbols
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
```

### Test Failures
```powershell
# Run regression tests to verify data integrity
$env:PYTHONPATH = "$PWD"; py tests\regression\test_march13_data.py

# If tests fail, check:
# 1. Database connectivity (PostgreSQL running?)
# 2. Data consistency (run analyze_march13_trading.py)
# 3. Zerodha API credentials (check .env file)
```

---

## 📱 Key Features

### ✅ Active Features
- Automatic price updates (every 60 seconds during market)
- Automatic stop-loss execution (-2% for equity)
- Position size limits (10% max per position)
- Total exposure limits (80% max)
- Risk-based position sizing
- Continuous monitoring (monitor_positions.py)
- Comprehensive test suite (49 tests)

### ⚠️ Important Notes
1. **Stop-loss is ACTIVE** - Positions will auto-exit at -2%
2. **Position limits enforced** - Can't exceed 10% per position
3. **Test suite validates all calculations** - Run daily
4. **Monitoring recommended** - Use monitor_positions.py during market

---

## 🎯 Next Steps

### This Week (Paper Trading Observation)
- [ ] Run `py monitor_positions.py` daily during market
- [ ] Track win rate (currently 0%)
- [ ] Verify stop-loss triggers at -2%
- [ ] Check position sizes stay within 10%
- [ ] Run tests daily to verify data integrity

### Before Live Trading
- [ ] Achieve 50%+ win rate over 10+ trades
- [ ] Review options strategy (CE 23500 lost 27%)
- [ ] Test with small capital first (Rs.50,000)
- [ ] Set up SMS/email alerts
- [ ] Document all edge cases

---

## 📞 Emergency Commands

### Stop All Trading
```powershell
# Kill monitor if running
Ctrl+C  # in monitor_positions.py terminal

# Close all positions manually (if needed)
# Connect to database and update signal status to CLOSED
```

### Check Last Trade
```sql
SELECT * FROM paper_trading_orders 
ORDER BY executed_at DESC 
LIMIT 5;
```

### Check Open Positions
```sql
SELECT symbol, quantity, avg_price, current_price, pnl, pnl_percent 
FROM paper_trading_positions 
WHERE quantity > 0 
ORDER BY pnl_percent ASC;
```

---

*Last Updated: March 13, 2026*
*System Status: ✅ All Tests Passing (49/49)*
*Recommendation: Continue paper trading, monitor performance*
