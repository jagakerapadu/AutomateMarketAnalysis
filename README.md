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
- **Paper Trading Engine**: Virtual portfolio with real-time execution simulation
- **Risk Management System**: 
  - Automatic stop-loss execution (-2% equity, -40% options)
  - Position size limits (10% max per position)
  - Total exposure limits (80% max deployed)
  - Confidence-based position sizing
  - Real-time risk monitoring and alerts
- **Backtest Engine**: Historical simulation with detailed metrics
- **FastAPI Backend**: RESTful API for all services
- **Next.js Dashboard**: Real-time market intelligence interface
- **Automated Scheduler**: Pre-market, intraday, and post-market jobs
- **Comprehensive Testing**: 49 automated tests (unit, integration, regression)

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

### 🛡️ Risk Management & Monitoring

| Script | Purpose | Command |
|--------|---------|---------|
| `services/paper_trading/risk_manager.py` | View risk status and limits | `python services/paper_trading/risk_manager.py` |
| `monitor_positions.py` | **Real-time position monitoring** | `python monitor_positions.py` |
| `update_paper_prices.py` | Update paper trading prices | `python update_paper_prices.py` |
| `analyze_march13_trading.py` | Daily trading analysis report | `python analyze_march13_trading.py` |

**Risk Limits (Active Protection):**
- Max per position: **10% of capital**
- Max total exposure: **80% of capital**
- Max positions: **20 concurrent**
- Equity stop-loss: **-2%** (automatic exit)
- Equity target: **+3%** (automatic exit)
- Options stop-loss: **-40%** (wider tolerance)
- Options target: **+50%**

### 🧪 Testing & Quality Assurance

| Test Suite | Tests | Command |
|------------|-------|---------|
| **All Tests** | 49 tests | `python run_all_tests.py` |
| Risk Manager Unit Tests | 19 tests | `$env:PYTHONPATH = "$PWD"; py tests\unit\test_risk_manager.py` |
| Portfolio Unit Tests | 14 tests | `$env:PYTHONPATH = "$PWD"; py tests\unit\test_virtual_portfolio.py` |
| Regression Tests | 16 tests | `$env:PYTHONPATH = "$PWD"; py tests\regression\test_march13_data.py` |

**Test Coverage:**
- ✅ Position sizing validation
- ✅ Stop-loss/target logic
- ✅ P&L calculations (realized & unrealized)
- ✅ Cash flow tracking
- ✅ Options calculations (lot sizes)
- ✅ Regression validation against March 13, 2026 data
- ✅ Risk limit enforcement

**Test Status:** 49/49 Passing (100%)

---

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

### Morning Routine (Before Market Opens - 8:00 AM IST)
```bash
# Regenerate Zerodha token (expires daily)
python setup_credentials.py
# Select option 4: Regenerate Zerodha Access Token

# Update paper trading prices
python update_paper_prices.py

# Check risk status
python services/paper_trading/risk_manager.py

# Run regression tests to verify system integrity
$env:PYTHONPATH = "$PWD"; python tests/regression/test_march13_data.py

# Fetch pre-market data
python fetch_all_data.py

# Start the system
python start.py
```

### During Market Hours (9:15 AM - 3:30 PM IST)

**Recommended: Start Real-Time Monitoring**
```bash
python monitor_positions.py
```
This will:
- Update prices every 30 seconds
- Alert on positions approaching stop-loss
- Show real-time risk dashboard
- Auto-execute stop-loss at -2%

**Or Manual Monitoring:**
```bash
# Check current positions and risk
python services/paper_trading/risk_manager.py

# Update prices manually
python update_paper_prices.py
```

The system will continuously:
- Fetch real-time data (if scheduler is running)
- Generate signals based on strategies
- Execute paper trades with risk validation
- Display updates on dashboard

### Post-Market (After 3:30 PM IST)
```bash
# Fetch end-of-day data
python populate_real_data.py

# Generate daily trading report
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
python analyze_march13_trading.py

# Run full test suite to verify data integrity
python run_all_tests.py

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
│   ├── paper_trading/     # Paper trading engine
│   │   ├── paper_trading_engine.py
│   │   ├── virtual_portfolio.py
│   │   └── risk_manager.py      # NEW: Risk management framework
│   └── api/               # FastAPI backend
├── tests/                 # NEW: Comprehensive test suite
│   ├── unit/             # Unit tests (33 tests)
│   │   ├── test_risk_manager.py          (19 tests)
│   │   └── test_virtual_portfolio.py     (14 tests)
│   ├── integration/      # Integration tests
│   │   └── test_trading_workflows.py
│   └── regression/       # Regression tests (16 tests)
│       └── test_march13_data.py
├── dashboard/             # Next.js dashboard
├── scheduler/            # Task scheduler
├── scripts/sql/          # Database schema
├── monitor_positions.py   # NEW: Real-time position monitoring
├── run_all_tests.py      # NEW: Master test runner
├── analyze_march13_trading.py  # Daily trading analysis
├── docker-compose.yml
├── requirements.txt
├── SYSTEM_IMPROVEMENTS.md  # NEW: Detailed improvement docs
└── QUICK_START.md         # NEW: Quick reference guide
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

## 🆕 Recent Improvements (March 2026)

### Risk Management System
- **Automatic stop-loss**: Exits at -2% for equity, -40% for options
- **Position limits**: Max 10% per position, 80% total exposure
- **Risk monitoring**: Real-time alerts for positions at risk
- **Optimal sizing**: Confidence-based position sizing

### Testing Framework
- **49 automated tests** covering all critical functions
- **Unit tests**: Risk manager (19) + Portfolio (14)
- **Regression tests**: Validates against March 13, 2026 data (16)
- **100% pass rate**: All calculations verified accurate

### Monitoring Tools
- **monitor_positions.py**: Continuous 30-second price updates
- **Risk dashboard**: Live exposure, P&L, and alerts
- **Alert system**: Notifications for positions near stop-loss

**📚 Documentation:**
- `SYSTEM_IMPROVEMENTS.md` - Detailed technical improvements
- `QUICK_START.md` - Quick reference for daily operations
- `MARCH13_2026_TRADING_REPORT.md` - Sample trading day analysis

---

**Warning**: This is a trading system. Test thoroughly before using real money. Past performance does not guarantee future results. Trade at your own risk.