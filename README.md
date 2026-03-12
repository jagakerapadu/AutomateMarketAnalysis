# Trading System - Hedge Fund Style Personal System

A complete enterprise-grade trading system for Indian markets (NSE/BSE) with automated data ingestion, technical analysis, strategy execution, and backtesting.

## 🚀 Features

- **Market Data Pipeline**: Multi-source data ingestion (Zerodha, Yahoo Finance)
- **TimescaleDB Storage**: Optimized time-series database for historical analysis
- **Technical Indicators**: 15+ indicators (EMA, MACD, RSI, Supertrend, etc.)
- **Trading Strategies**: 
  - VWAP Trap Strategy
  - Opening Range Breakout
  - SMA Crossover
  - RSI Oversold/Overbought
  - Volume Breakout
  - Extensible strategy framework
- **Backtest Engine**: Historical simulation with detailed metrics
- **FastAPI Backend**: RESTful API for all services
- **Next.js Dashboard**: Real-time market intelligence interface
- **Automated Scheduler**: Pre-market, intraday, and post-market jobs

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ with TimescaleDB extension
- Zerodha Kite API account (optional: ICICI Direct)
- Docker (optional, recommended)

## 🛠️ Installation

### 1. Clone and Install Dependencies

```bash
cd AutomateMarketAnalysis

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd dashboard
npm install
cd ..
```

### 2. Setup Database

**Using Docker (Recommended):**
```bash
docker-compose up -d
```

**Manual Setup:**
```sql
-- Install TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Run initialization scripts
\i scripts/sql/init.sql
```

### 3. Configure Credentials

Run the credential management system:

```bash
python setup_credentials.py
```

This interactive tool will help you:
- Setup Zerodha Kite API credentials
- Setup ICICI Direct API credentials (optional)
- Generate access tokens automatically
- Save credentials securely to `.env` file

**Alternative: Manual Setup**

Create `.env` file:
```env
# Database
DB_HOST=localhost
DB_PORT=5434
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Zerodha Kite
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_ACCESS_TOKEN=your_access_token

# ICICI Direct (Optional)
ICICI_API_KEY=your_icici_key
ICICI_API_SECRET=your_icici_secret
ICICI_SESSION_TOKEN=your_session_token

# Application
API_PORT=8000
LOG_LEVEL=INFO
```

## 🚀 Quick Start

### Option 1: All-in-One Start (Recommended)

```bash
python start.py
```

This will:
1. Verify environment configuration
2. Check database connectivity
3. Start TimescaleDB (if using Docker)
4. Launch backend API server
5. Launch Next.js dashboard
6. Run system health checks

### Option 2: Manual Start

**1. Start Backend API**
```bash
python start_api.py
```
API available at `http://localhost:8000`
API Docs: `http://localhost:8000/api/docs`

**2. Start Dashboard**
```bash
cd dashboard
npm run dev
```
Dashboard available at `http://localhost:3000`

**3. Run Scheduler (Optional)**
```bash
cd scheduler
python scheduler.py
```

## 📦 Available Scripts

### Core Production Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `setup_credentials.py` | Interactive credential management for Zerodha & ICICI | `python setup_credentials.py` |
| `start.py` | All-in-one system launcher | `python start.py` |
| `start_api.py` | Start backend API only | `python start_api.py` |
| `system_status.py` | Check health of all components | `python system_status.py` |
| `populate_real_data.py` | Fetch real market data and populate DB | `python populate_real_data.py` |
| `fetch_all_data.py` | Comprehensive data fetch (stocks + indices) | `python fetch_all_data.py` |
| `fetch_simple.py` | Simple data fetch for quick updates | `python fetch_simple.py` |

### Utility Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `scripts/generate_kite_token.py` | Regenerate Zerodha access token | `python scripts/generate_kite_token.py` |

### Service Engines (Can be run standalone)

| Script | Purpose | Command |
|--------|---------|---------|
| `services/indicators/indicator_engine.py` | Calculate technical indicators | `python services/indicators/indicator_engine.py` |
| `services/strategy/strategy_engine.py` | Generate trading signals | `python services/strategy/strategy_engine.py` |
| `services/backtest/backtest_engine.py` | Run backtests on strategies | `python services/backtest/backtest_engine.py` |

## 📊 First Run Workflow

### 1. Setup Credentials
```bash
python setup_credentials.py
```
Follow the interactive prompts to setup Zerodha API.

### 2. Populate Initial Data
```bash
python populate_real_data.py
```
This will:
- Fetch 60 days of historical data from Zerodha
- Fetch global market indices
- Generate realistic trading signals
- Create sample trades

### 3. Start the System
```bash
python start.py
```

### 4. Access Dashboard
Open browser to `http://localhost:3000`

Pages available:
- `/` - Market overview with global indices
- `/signals` - Trading signals with confidence scores
- `/trades` - Trade history with P&L analysis
- `/backtest` - Backtest results and metrics

## 🔐 Security Notes

- **Never commit `.env` file** to version control
- Zerodha access tokens expire daily - regenerate using `setup_credentials.py` or `scripts/generate_kite_token.py`
- Store API secrets securely
- Use environment variables for production deployments

## 📈 Daily Usage

### Morning Routine (Before Market Opens - 9:00 AM IST)
```bash
# Regenerate Zerodha token (expires daily)
python setup_credentials.py
# Select option 4: Regenerate Zerodha Access Token

# Fetch pre-market data
python fetch_all_data.py

# Start the system
python start.py
```

### During Market Hours
The system will continuously:
- Fetch real-time data (if scheduler is running)
- Generate signals based on strategies
- Display updates on dashboard

### Post-Market (After 3:30 PM IST)
```bash
# Fetch end-of-day data
python populate_real_data.py

# Review performance
python system_status.py
```

## 📁 Project Structure

```
AutomateMarketAnalysis/
├── config/                 # Configuration and settings
├── services/
│   ├── market_data/       # Data ingestion pipeline
│   ├── indicators/        # Technical indicator engine
│   ├── strategy/          # Trading strategies
│   ├── backtest/          # Backtesting engine
│   └── api/               # FastAPI backend
├── dashboard/             # Next.js dashboard
├── scheduler/            # Task scheduler
├── scripts/sql/          # Database schema
├── docker-compose.yml
└── requirements.txt
```

## 📊 Database Schema

### Core Tables

- `market_ohlc` - OHLC candlestick data (hypertable)
- `indicators` - Technical indicators (hypertable)
- `options_chain` - Options data (hypertable)
- `signals` - Trading signals
- `trades` - Executed trades
- `backtest_results` - Backtest performance
- `market_sentiment` - VIX, FII/DII data

## 🎯 Daily Workflow

### Pre-Market (7:30 AM - 9:15 AM)
1. 7:30 AM - Fetch global market data
2. 8:00 AM - Fetch Indian market data
3. 8:45 AM - Fetch options chain
4. 9:00 AM - Calculate technical indicators
5. 9:10 AM - Generate trading signals

### Market Hours (9:15 AM - 3:30 PM)
- Every 5 minutes: Update intraday data

### Post-Market (4:00 PM)
- Calculate daily indicators
- Update strategy performance

## ⚠️ Security

- Never commit `.env` file
- Store API keys securely
- Use `ENABLE_LIVE_TRADING=false` for testing
- Implement IP whitelisting for production

## 📝 Adding New Strategies

1. Create strategy file in `services/strategy/strategies/`
2. Inherit from `BaseStrategy`
3. Implement `generate_signal()` and `validate_conditions()`
4. Register in `StrategyEngine`

---

**Warning**: This is a trading system. Test thoroughly before using real money. Past performance does not guarantee future results. Trade at your own risk.