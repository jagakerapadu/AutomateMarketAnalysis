# Trading System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      TRADING SYSTEM                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Market     │  │  Indicator   │  │   Strategy   │         │
│  │   Data       │─▶│   Engine     │─▶│   Engine     │         │
│  │   Pipeline   │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                                     │                 │
│         ▼                                     ▼                 │
│  ┌──────────────────────────────────────────────────┐         │
│  │          TimescaleDB (PostgreSQL)                │         │
│  └──────────────────────────────────────────────────┘         │
│         │                                     │                 │
│         ▼                                     ▼                 │
│  ┌──────────────┐                   ┌──────────────┐         │
│  │   FastAPI    │◀──────────────────│   Scheduler  │         │
│  │   Backend    │                   │              │         │
│  └──────────────┘                   └──────────────┘         │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                              │
│  │   Next.js    │                                              │
│  │   Dashboard  │                                              │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Market Data Pipeline
**Location**: `services/market_data/`

**Purpose**: Ingest market data from multiple sources

**Components**:
- **Zerodha Adapter**: Primary data source for live trading
- **NSE Adapter**: Options chain and sentiment data
- **Yahoo Finance Adapter**: Fallback and global indices

**Data Flow**:
```
External APIs → Adapters → Validation → TimescaleDB
```

**Key Features**:
- Multi-source redundancy
- Automatic retry logic
- Data validation
- Duplicate handling

### 2. TimescaleDB Storage
**Location**: `scripts/sql/init.sql`

**Purpose**: Optimized time-series data storage

**Tables**:
- `market_ohlc` - Candlestick data (hypertable)
- `indicators` - Technical indicators
- `options_chain` - Options data
- `signals` - Trading signals
- `trades` - Executed trades
- `backtest_results` - Performance metrics

**Optimizations**:
- Hypertables for time-series
- Continuous aggregates
- Retention policies
- Compression

### 3. Indicator Engine
**Location**: `services/indicators/`

**Purpose**: Calculate technical indicators

**Indicators**:
- Trend: EMA (9, 21, 50, 200), MACD
- Momentum: RSI, Stochastic
- Volatility: ATR, Bollinger Bands
- Custom: Supertrend, VWAP

**Processing**:
- Batch calculation
- Incremental updates
- Multiple timeframes
- Efficient DataFrame operations

### 4. Strategy Engine
**Location**: `services/strategy/`

**Purpose**: Generate trading signals

**Architecture**:
```
BaseStrategy (Abstract)
    │
    ├── VWAPTrapStrategy
    ├── OpeningRangeBreakoutStrategy
    └── [Custom Strategies...]
```

**Strategy Lifecycle**:
1. Fetch market data + indicators
2. Validate conditions
3. Generate signal
4. Calculate position size
5. Store signal in database

### 5. Backtest Engine
**Location**: `services/backtest/`

**Purpose**: Historical strategy simulation

**Features**:
- Event-driven simulation
- Realistic slippage/commission
- Performance metrics
- Equity curve tracking

**Metrics Calculated**:
- Total return
- Sharpe ratio
- Max drawdown
- Win rate
- Profit factor
- Average win/loss

### 6. FastAPI Backend
**Location**: `services/api/`

**Purpose**: RESTful API for all services

**Endpoints**:
- `/api/market/*` - Market data
- `/api/signals/*` - Trading signals
- `/api/trades/*` - Trade management
- `/api/backtest/*` - Backtest results
- `/api/portfolio/*` - Portfolio tracking

**Features**:
- CORS enabled
- Auto-generated docs
- Async operations
- Error handling

### 7. Next.js Dashboard
**Location**: `dashboard/`

**Purpose**: User interface

**Pages**:
- Dashboard - Market overview and signals
- Signals - Detailed signal analysis
- Trades - Trade history and analytics
- Backtest - Strategy performance

**Technology**:
- TypeScript
- Tailwind CSS
- Recharts for visualization
- Axios for API calls

### 8. Scheduler
**Location**: `scheduler/`

**Purpose**: Automate daily workflow

**Jobs**:
```
07:30 AM - Fetch global markets
08:00 AM - Fetch Indian market data
08:45 AM - Fetch options chain  
09:00 AM - Calculate indicators
09:10 AM - Generate signals
Every 5 min - Intraday updates (during market hours)
04:00 PM - Post-market analysis
```

## Data Flow

### Pre-Market Flow
```
1. Global Markets → Yahoo Finance → global_indices table
2. OHLC Data → Zerodha/NSE → market_ohlc table
3. Options Chain → NSE → options_chain table
4. Market Sentiment → NSE → market_sentiment table
5. Indicators ← market_ohlc → indicators table
6. Strategies ← indicators → signals table
7. Dashboard ← FastAPI ← signals table
```

### Live Trading Flow
```
1. Signal Generated → signals table
2. User/Bot Approval → Trade Execution
3. Order Placed → Broker API
4. Order Status → trades table
5. Position Monitored → Real-time updates
6. Exit Triggered → Broker API
7. Trade Closed → trades table (P&L calculated)
```

## Security Architecture

### Environment Variables
- Never commit `.env`
- Use strong passwords
- Rotate API keys regularly

### Database
- Connection pooling
- Prepared statements
- Read-only access for analytics

### API
- JWT authentication (optional)
- Rate limiting
- CORS configuration
- Input validation

### Trading Safety
- Max daily loss limit
- Position size limits
- Risk per trade cap
- Emergency kill switch

## Scalability Considerations

### Current Capacity
- 50+ symbols
- Multiple timeframes
- 5+ years historical data
- Real-time updates

### Future Scaling
- Add more workers for parallel processing
- Redis caching layer
- Message queue (RabbitMQ/Kafka)
- Microservices architecture
- Load balancing

## Monitoring

### System Health
- Database connection pool
- API response times
- Scheduler job status
- Disk space usage

### Trading Metrics
- Win rate by strategy
- Daily P&L
- Open positions count
- Risk exposure

## Disaster Recovery

### Backups
- Daily database backups
- Trade logs preservation
- Configuration versioning

### Failover
- Multiple data sources
- Manual override capabilities
- Emergency stop procedures

---

This architecture is designed for:
- **Reliability**: Multiple data sources, error handling
- **Performance**: Optimized queries, hypertables
- **Extensibility**: Easy to add strategies, indicators
- **Maintainability**: Modular design, clear separation
