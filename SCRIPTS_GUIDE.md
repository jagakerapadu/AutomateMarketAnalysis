# Scripts Guide

Complete reference for all Python scripts in the trading system.

## 📁 Project Structure

```
AutomateMarketAnalysis/
├── setup_credentials.py          # 🔐 Credential management (Zerodha, ICICI)
├── start.py                      # 🚀 All-in-one system launcher
├── start_api.py                  # 🔌 Backend API launcher
├── system_status.py              # 🔍 Health check for all components
├── populate_real_data.py         # 📊 Fetch real market data
├── fetch_all_data.py             # 📥 Comprehensive data fetcher
├── fetch_simple.py               # 📥 Simple data fetcher
├── scripts/
│   └── generate_kite_token.py   # 🔑 Zerodha token regeneration
├── services/
│   ├── api/main.py              # FastAPI backend server
│   ├── indicators/indicator_engine.py
│   ├── strategy/strategy_engine.py
│   └── backtest/backtest_engine.py
├── scheduler/
│   └── scheduler.py             # ⏰ Automated job scheduler
└── dashboard/                    # Next.js frontend

```

---

## 🔐 Credential Management

### `setup_credentials.py`
**Purpose**: Interactive credential setup for trading APIs

**Features**:
- Setup Zerodha Kite API credentials
- Setup ICICI Direct API credentials
- Automatic access token generation
- Secure storage in `.env` file
- View masked credentials
- Regenerate expired tokens

**Usage**:
```bash
python setup_credentials.py
```

**Menu Options**:
1. Setup Zerodha Kite API - Add API key, secret, generate token
2. Setup ICICI Direct API - Add ICICI credentials
3. View Current Credentials - Display masked credentials
4. Regenerate Zerodha Access Token - Daily token refresh
5. Save & Exit - Write to .env and exit
6. Exit without Saving - Discard changes

**When to Use**:
- First-time setup
- Daily: Zerodha tokens expire after 24 hours
- When changing API credentials
- After API key rotation

---

## 🚀 System Launchers

### `start.py`
**Purpose**: All-in-one system launcher with health checks

**Features**:
- Verifies `.env` configuration
- Checks database connectivity
- Starts Docker containers (if applicable)
- Launches backend API server
- Launches Next.js dashboard
- Runs comprehensive health checks

**Usage**:
```bash
python start.py
```

**What it does**:
1. ✅ Environment validation
2. ✅ Database connection test
3. 🐳 Docker startup (TimescaleDB)
4. 🔌 Backend API startup (port 8000)
5. 🎨 Dashboard startup (port 3000)
6. 🔍 Health verification

**Requirements**:
- Valid `.env` file
- TimescaleDB running
- Ports 8000 and 3000 available

---

### `start_api.py`
**Purpose**: Start backend API server only

**Features**:
- Launches FastAPI backend
- Hot-reload enabled in development
- Automatic port configuration from .env

**Usage**:
```bash
python start_api.py
```

**Endpoints**:
- Base: `http://localhost:8000`
- Docs: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/health`

**Use Case**:
- When dashboard is already running
- For API development/testing
- When running dashboard separately

---

## 🔍 Monitoring & Status

### `system_status.py`
**Purpose**: Comprehensive health check of all components

**Checks**:
1. **Zerodha API Connection**
   - Validates credentials
   - Tests API connectivity
   - Displays user profile

2. **TimescaleDB Database**
   - Connection status
   - Database version
   - Table count
   - Data record counts

3. **Backend API Server**
   - Server status
   - API version
   - Health endpoint

4. **Next.js Dashboard**
   - Server status
   - Accessibility

**Usage**:
```bash
python system_status.py
```

**Output Example**:
```
======================================================================
  TRADING SYSTEM - STATUS CHECK
======================================================================

1. ZERODHA API CONNECTION
----------------------------------------------------------------------
✅ Connected
   User: John Doe (AB1234)
   Email: john@example.com

2. TIMESCALEDB DATABASE
----------------------------------------------------------------------
✅ Connected
   PostgreSQL 15.2 (Ubuntu 15.2-1.pgdg22.04+1)
   Tables: 12
   OHLC Records: 1,234

3. BACKEND API SERVER
----------------------------------------------------------------------
✅ Online
   Trading System API v1.0.0
   URL: http://localhost:8000
   Docs: http://localhost:8000/api/docs

4. NEXT.JS DASHBOARD
----------------------------------------------------------------------
✅ Online
   URL: http://localhost:3000
```

**When to Use**:
- After system startup
- Troubleshooting connection issues
- Before running data fetches
- Daily health verification

---

## 📊 Data Management

### `populate_real_data.py`
**Purpose**: Fetch REAL market data and populate database with realistic signals/trades

**What it does**:
1. **Fetch Market Data**
   - Global indices from Yahoo Finance (S&P 500, Dow Jones, Nasdaq)
   - Indian stocks from Zerodha (INFY, RELIANCE, TCS)
   - 60 days of historical OHLC data

2. **Generate Realistic Signals**
   - SMA Crossover (5/10/20 periods)
   - RSI Oversold/Overbought (14 period)
   - Volume Breakout detection
   - Based on actual price movements

3. **Create Realistic Trades**
   - Historical trades from actual price data
   - Real entry/exit prices
   - Actual P&L calculations

**Usage**:
```bash
python populate_real_data.py
```

**Output**:
- ✅ 123 OHLC records (real prices)
- ✅ 10-20 trading signals (75-90% confidence)
- ✅ 10 historical trades (with real P&L)

**When to Use**:
- First-time database population
- After clearing database
- Weekly data refresh
- After adding new symbols

**Timestamp Handling**:
- Stores times in **IST (Indian Standard Time)**
- Market data at 3:30 PM IST (market close)
- Converts properly: 3:30 PM IST = 10:00 AM UTC

---

### `fetch_all_data.py`
**Purpose**: Comprehensive data fetch from all sources

**Features**:
- Fetches 15+ symbols from Zerodha
- Global indices from Yahoo Finance
- Options chain data (if available)
- Market sentiment indicators
- 90 days of historical data

**Usage**:
```bash
python fetch_all_data.py
```

**Symbols Covered**:
- INFY, RELIANCE, TCS, HDFCBANK, ICICIBANK
- KOTAKBANK, SBIN, BHARTIARTL, BAJFINANCE
- HINDUNILVR, ASIANPAINT, ITC, LT
- And more...

**When to Use**:
- Weekly comprehensive data update
- Building large historical dataset
- After market hours (post 3:30 PM IST)

---

### `fetch_simple.py`
**Purpose**: Quick data fetch for essential symbols

**Features**:
- Fetches 5-10 core symbols
- Fast execution (< 30 seconds)
- Daily data only
- Minimal API calls

**Usage**:
```bash
python fetch_simple.py
```

**When to Use**:
- Daily EOD data updates
- Quick data refresh
- Before market open (pre-market data)
- When API call limits are a concern

---

## 🔑 Token Management

### `scripts/generate_kite_token.py`
**Purpose**: Regenerate Zerodha Kite access token

**Features**:
- Starts local OAuth server
- Opens browser for Zerodha login
- Captures callback automatically
- Generates access token
- Saves to .env file

**Usage**:
```bash
python scripts/generate_kite_token.py
```

**Process**:
1. Script starts local server on port 9088
2. Opens browser to Kite login page
3. You login with credentials/TOTP
4. Browser redirects to localhost
5. Script captures request token
6. Exchanges for access token
7. Saves to `.env` automatically

**When to Use**:
- **Daily**: Zerodha tokens expire every 24 hours
- Before market open (8:00-9:00 AM IST)
- After `401 Unauthorized` errors
- When `setup_credentials.py` token generation fails

**Alternative**: Use `setup_credentials.py` menu option 4

---

## 🔧 Service Engines

### `services/indicators/indicator_engine.py`
**Purpose**: Calculate technical indicators on OHLC data

**Indicators Calculated**:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Average)
- SMA (Simple Moving Average)
- Bollinger Bands
- Supertrend
- ATR (Average True Range)
- ADX (Average Directional Index)

**Usage**:
```bash
python services/indicators/indicator_engine.py
```

**When to Use**:
- After fetching new OHLC data
- For strategy backtesting
- Manual indicator calculation

---

### `services/strategy/strategy_engine.py`
**Purpose**: Generate trading signals based on strategies

**Strategies**:
- VWAP Trap
- Opening Range Breakout
- SMA Crossover
- RSI Mean Reversion
- Custom strategies (extensible)

**Usage**:
```bash
python services/strategy/strategy_engine.py
```

**Output**:
- Trading signals with entry/exit/SL prices
- Confidence scores (70-95%)
- Strategy reasoning

**When to Use**:
- After indicator calculation
- Pre-market scan (8:30 AM IST)
- Intraday scan (every 5-15 minutes)
- Post-market analysis

---

### `services/backtest/backtest_engine.py`
**Purpose**: Run historical backtests on strategies

**Metrics Calculated**:
- Total return %
- Win rate
- Sharpe ratio
- Maximum drawdown
- Profit factor
- Average win/loss
- Equity curve

**Usage**:
```bash
python services/backtest/backtest_engine.py
```

**Features**:
- Historical simulation
- Multiple strategy comparison
- Detailed trade-by-trade analysis
- Risk metrics

**When to Use**:
- Strategy validation
- Parameter optimization
- Performance analysis
- Before live trading

---

## ⏰ Automation

### `scheduler/scheduler.py`
**Purpose**: Automated job scheduling for trading system

**Scheduled Jobs**:

| Time (IST) | Job | Description |
|------------|-----|-------------|
| 7:30 AM | Fetch Global Indices | Pre-market preparation |
| 8:00 AM | Fetch Indian Stocks | Pre-market data |
| 8:30 AM | Pre-market Scan | Generate signals |
| 9:15 AM | Market Open | Start intraday monitoring |
| 9:20-3:25 PM | Intraday Updates | Every 5 minutes |
| 3:30 PM | Market Close | EOD processing |
| 4:00 PM | Post-market Analysis | Performance review |

**Usage**:
```bash
cd scheduler
python scheduler.py
```

**Features**:
- Cron-like scheduling
- Error handling & retry logic
- Logging
- Market hours detection

**When to Use**:
- Run continuously during trading days
- Deploy as system service
- For hands-free operation

---

## 🎯 Typical Daily Workflow

### Morning (8:00 AM IST)
```bash
# 1. Regenerate token (expires daily)
python setup_credentials.py
# Select: 4. Regenerate Zerodha Access Token

# 2. Check system health
python system_status.py

# 3. Fetch latest data
python fetch_simple.py

# 4. Start system
python start.py
```

### During Market (9:15 AM - 3:30 PM IST)
- System runs automatically (if scheduler active)
- Monitor dashboard at `http://localhost:3000`
- Check signals page for new opportunities

### Evening (After 3:30 PM IST)
```bash
# Fetch EOD data
python populate_real_data.py

# Review performance
python system_status.py
```

---

## 🚨 Troubleshooting

### "401 Unauthorized" from Zerodha
```bash
python setup_credentials.py
# Select option 4: Regenerate token
```

### Database Connection Failed
```bash
# Check if TimescaleDB is running
docker ps | grep timescaledb

# Restart database
docker-compose restart

# Verify
python system_status.py
```

### No Data in Dashboard
```bash
# Populate data
python populate_real_data.py

# Check database
python system_status.py
```

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process or change API_PORT in .env
```

---

## 📝 Script Dependencies

```
setup_credentials.py
  └─ Requires: kiteconnect, python-dotenv

start.py
  └─ Requires: All system components

populate_real_data.py
  └─ Requires: zerodha_adapter, yfinance_adapter, data_writer, database

fetch_all_data.py
  └─ Requires: zerodha_adapter, yfinance_adapter

scripts/generate_kite_token.py
  └─ Requires: kiteconnect, http.server

system_status.py
  └─ Requires: kiteconnect, psycopg2, requests
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** to version control
2. **Rotate API keys** every 90 days
3. **Use strong database passwords**
4. **Regenerate Zerodha tokens daily**
5. **Limit API key permissions** to required scopes only
6. **Monitor API usage** to detect unauthorized access
7. **Keep dependencies updated** for security patches

---

## 📚 Additional Resources

- [Zerodha Kite API Docs](https://kite.trade/docs/connect/v3/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

---

**Last Updated**: March 11, 2026
**System Version**: 1.0.0
