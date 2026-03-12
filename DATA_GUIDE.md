# How to Get Data from All Sources & Populate Dashboard

## ✅ Current Status

Your system now has:
- **123 OHLC records** → INFY, RELIANCE, TCS (60 days history)
- **11 Global indices** → S&P,Dow, NASDAQ, FTSE, Nikkei
- **20 Trading signals** → 70-95% confidence scores
- **5 Completed trades** → Total P&L: ₹11,860

**Dashboard**: http://localhost:3000  
**API Docs**: http://localhost:8000/api/docs

---

## 🔄 Fetch Data from All Sources

### Method 1: Simplified Fetch (Recommended)

```powershell
# Step 1: Clear cached environment (Important!)
$env:ZERODHA_ACCESS_TOKEN = $null

# Step 2: Fetch data
py fetch_simple.py
```

**What it does:**
- Fetches 15 stocks from Zerodha Kite (60 days OHLC)
- Fetches global indices from Yahoo Finance  
- Stores everything in TimescaleDB

**Time**: ~15-30 seconds

### Method 2: Daily Token Refresh + Fetch

```powershell
# 1. Generate fresh Zerodha token (required daily)
py scripts\generate_kite_token.py

# 2. Clear environment  
$env:ZERODHA_ACCESS_TOKEN = $null; $env:ZERODHA_API_KEY = $null

# 3. Fetch data
py fetch_simple.py
```

---

## 📊 Data Sources Explained

### 1. Zerodha Kite API → Indian Stock Market
- **Data**: OHLC (Open, High, Low, Close), Volume, VWAP
- **Stocks tracked** (15): INFY, RELIANCE, TCS, HDFCBANK, ICICIBANK, KOTAKBANK, SBIN, BHARTIARTL, BAJFINANCE, ITC, HINDUNILVR, ASIANPAINT, HCLTECH, AXISBANK, LT
- **Auth**: Requires daily token generation
- **Script**: `fetch_simple.py`

**Customize watchlist** → Edit` line 19 in `fetch_simple.py`:
```python
WATCHLIST = [
    "INFY", "TCS", "RELIANCE",  # Add your stocks here
]
```

### 2. Yahoo Finance → Global Markets
- **Data**: Index values, daily change
- **Indices**: ^GSPC (S&P 500), ^DJI (Dow), ^IXIC (NASDAQ), ^FTSE, ^N225 (Nikkei)
- **Auth**: None required (free API)
- **Script**: Built into `fetch_simple.py`

### 3. NSE India API → Options & Sentiment
- **Status**: ⚠️ Currently not working (API timeouts)
- **Workaround**: Use Zerodha for Indian stock data
- **What it would provide**: Options chain, FII/DII flows, India VIX

---

## 🎯 View Your Data

### Web Dashboard
Open: http://localhost:3000

Shows:
- Market overview (Nifty, BankNifty, VIX)
- Latest trading signals with confidence scores
- Active positions and P&L
- Performance stats

### API Endpoints

Test in browser or PowerShell:

**Signals**
```powershell
# Latest 5 signals
(Invoke-WebRequest -Uri "http://localhost:8000/api/signals/latest?limit=5" -UseBasicParsing).Content | ConvertFrom-Json | Format-Table

# High confidence only
http://localhost:8000/api/signals/latest?min_confidence=85
```

**Trades**
```powershell
# Trade statistics
(Invoke-WebRequest -Uri "http://localhost:8000/api/trades/stats" -UseBasicParsing).Content | ConvertFrom-Json | Format-List

# All closed trades
http://localhost:8000/api/trades/?status=CLOSED
```

**Market Data**
```powershell
# Global indices
(Invoke-WebRequest -Uri "http://localhost:8000/api/market/global-indices" -UseBasicParsing).Content | ConvertFrom-Json | Format-Table

# Chart data for INFY
http://localhost:8000/api/market/chart/INFY?days=30
```

---

## 🧪 Test/Sample Data

If you need dummy data for testing:

```powershell
py populate_sample_data.py
```

Creates:
- 10 trading signals (random)
- 5 completed trades with P&L

**Note**: This is test data only. For real trading, use `fetch_simple.py`

---

## 🔍 Verify Database Contents

```powershell
py check_db.py
```

Shows:
- All table names
- Record counts
- Date ranges
- Latest timestamps

---

## 🚨 Troubleshooting

### Problem: Dashboard empty / No signals
**Solution**: 
```powershell
py populate_sample_data.py  # For test data
# OR
py fetch_simple.py           # For real market data
```

### Problem: "Incorrect api_key or access_token"
**Solution**:
```powershell
# Clear cached values
$env:ZERODHA_ACCESS_TOKEN = $null

# Generate fresh token
py scripts\generate_kite_token.py
```

### Problem: Zerodha only fetches 3 stocks, rest fail
**Cause**: API rate limiting or token issues

**Solution**:
-Edit `fetch_simple.py` line 19 → Reduce WATCHLIST to 3-5 stocks
- Wait 2-3 seconds between calls (add delay in script)
- Check if token is valid: `py test_connection.py`

### Problem: Global indices work but Zerodha doesn't
**Solution**:
```powershell
# Test Zerodha connection first
py test_connection.py

# If fails, regenerate token
py scripts\generate_kite_token.py

# Then fetch
$env:ZERODHA_ACCESS_TOKEN = $null; py fetch_simple.py
```

---

## 📅 Daily Workflow

### Before Market Open (8:00 AM)
1. **Generate token** (takes 30 sec):
   ```powershell
   py scripts\generate_kite_token.py
   ```

2. **Fetch data**:
   ```powershell
   $env:ZERODHA_ACCESS_TOKEN = $null
   py fetch_simple.py
   ```

3. **Check status**:
   ```powershell
   py system_status.py
   ```

### During Market Hours
- Monitor dashboard: http://localhost:3000
- Check signals: http://localhost:8000/api/signals/latest
- View trades: http://localhost:8000/api/trades/

### After Market Close
- Check P&L: http://localhost:8000/api/trades/daily-pnl
- Review stats: http://localhost:8000/api/trades/stats

---

## 📁 Key Files Reference

| File | Purpose |
|------|---------|
| `fetch_simple.py` | Fetch from Zerodha + Yahoo Finance |
| `populate_sample_data.py` | Create test signals/trades |
| `check_db.py` | View database contents |
| `system_status.py` | Check all components |
| `test_connection.py` | Test Zerodha API |
| `.env` | All credentials (API keys, tokens) |

---

## 🎯 Quick Commands

```powershell
# Fetch real market data
py fetch_simple.py

# Create test data
py populate_sample_data.py

# Check what you have
py check_db.py

# System health
py system_status.py

# New Zerodha token
py scripts\generate_kite_token.py
```

---

**Your dashboard at http://localhost:3000 is now populated with data!**

Refresh the page to see signals, trades, and market data.
