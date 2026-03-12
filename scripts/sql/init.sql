-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Market OHLC Data (Core time-series table)
CREATE TABLE IF NOT EXISTS market_ohlc (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h, 1d
    open DECIMAL(12, 2) NOT NULL,
    high DECIMAL(12, 2) NOT NULL,
    low DECIMAL(12, 2) NOT NULL,
    close DECIMAL(12, 2) NOT NULL,
    volume BIGINT NOT NULL,
    vwap DECIMAL(12, 2),
    oi BIGINT DEFAULT 0,
    PRIMARY KEY (timestamp, symbol, timeframe)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('market_ohlc', 'timestamp', if_not_exists => TRUE);

-- Create indices for fast queries
CREATE INDEX IF NOT EXISTS idx_market_ohlc_symbol_time ON market_ohlc (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_ohlc_timeframe ON market_ohlc (timeframe, timestamp DESC);

-- Options Chain Data
CREATE TABLE IF NOT EXISTS options_chain (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    expiry_date DATE NOT NULL,
    strike DECIMAL(12, 2) NOT NULL,
    option_type VARCHAR(2) NOT NULL, -- CE or PE
    ltp DECIMAL(12, 2),
    iv DECIMAL(8, 4),
    oi BIGINT,
    oi_change BIGINT,
    volume BIGINT,
    bid DECIMAL(12, 2),
    ask DECIMAL(12, 2),
    PRIMARY KEY (timestamp, symbol, expiry_date, strike, option_type)
);

SELECT create_hypertable('options_chain', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_options_symbol_expiry ON options_chain (symbol, expiry_date, timestamp DESC);

-- Technical Indicators
CREATE TABLE IF NOT EXISTS indicators (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    rsi DECIMAL(8, 4),
    macd DECIMAL(12, 4),
    macd_signal DECIMAL(12, 4),
    macd_hist DECIMAL(12, 4),
    ema_9 DECIMAL(12, 2),
    ema_21 DECIMAL(12, 2),
    ema_50 DECIMAL(12, 2),
    ema_200 DECIMAL(12, 2),
    vwap DECIMAL(12, 2),
    supertrend DECIMAL(12, 2),
    supertrend_direction VARCHAR(10),
    atr DECIMAL(12, 4),
    bb_upper DECIMAL(12, 2),
    bb_middle DECIMAL(12, 2),
    bb_lower DECIMAL(12, 2),
    stoch_k DECIMAL(8, 4),
    stoch_d DECIMAL(8, 4),
    PRIMARY KEY (timestamp, symbol, timeframe)
);

SELECT create_hypertable('indicators', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_indicators_symbol ON indicators (symbol, timestamp DESC);

-- Trading Signals
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    signal_type VARCHAR(10) NOT NULL, -- BUY, SELL, HOLD
    timeframe VARCHAR(10) NOT NULL,
    entry_price DECIMAL(12, 2) NOT NULL,
    stop_loss DECIMAL(12, 2) NOT NULL,
    target_price DECIMAL(12, 2) NOT NULL,
    confidence DECIMAL(5, 2),
    quantity INTEGER,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, EXECUTED, CANCELLED, EXPIRED
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON signals (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals (status, timestamp DESC);

-- Trades (Executed Positions)
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    order_type VARCHAR(10) NOT NULL, -- BUY, SELL
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(12, 2) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_price DECIMAL(12, 2),
    exit_time TIMESTAMPTZ,
    stop_loss DECIMAL(12, 2),
    target DECIMAL(12, 2),
    pnl DECIMAL(12, 2),
    pnl_percent DECIMAL(8, 4),
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, CLOSED, STOPPED
    broker_order_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades (status, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades (strategy, entry_time DESC);

-- Market Sentiment & VIX
CREATE TABLE IF NOT EXISTS market_sentiment (
    timestamp TIMESTAMPTZ NOT NULL PRIMARY KEY,
    india_vix DECIMAL(8, 4),
    nifty_pe_ratio DECIMAL(8, 4),
    nifty_pb_ratio DECIMAL(8, 4),
    fii_net DECIMAL(12, 2),
    dii_net DECIMAL(12, 2),
    advance_decline_ratio DECIMAL(8, 4),
    put_call_ratio DECIMAL(8, 4)
);

SELECT create_hypertable('market_sentiment', 'timestamp', if_not_exists => TRUE);

-- Global Market Indices
CREATE TABLE IF NOT EXISTS global_indices (
    timestamp TIMESTAMPTZ NOT NULL,
    index_name VARCHAR(20) NOT NULL,
    value DECIMAL(12, 2) NOT NULL,
    change_percent DECIMAL(8, 4),
    PRIMARY KEY (timestamp, index_name)
);

SELECT create_hypertable('global_indices', 'timestamp', if_not_exists => TRUE);

-- Backtest Results
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(12, 2) NOT NULL,
    final_capital DECIMAL(12, 2) NOT NULL,
    total_return DECIMAL(12, 2),
    total_return_percent DECIMAL(8, 4),
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    win_rate DECIMAL(8, 4),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    avg_win DECIMAL(12, 2),
    avg_loss DECIMAL(12, 2),
    profit_factor DECIMAL(8, 4),
    parameters JSONB,
    equity_curve JSONB,
    trades JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_results (strategy_name, created_at DESC);

-- Strategy Performance Tracking
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    trades_taken INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    gross_profit DECIMAL(12, 2) DEFAULT 0,
    gross_loss DECIMAL(12, 2) DEFAULT 0,
    net_pnl DECIMAL(12, 2) DEFAULT 0,
    win_rate DECIMAL(8, 4),
    avg_profit_per_trade DECIMAL(12, 2),
    UNIQUE (strategy_name, date)
);

CREATE INDEX IF NOT EXISTS idx_strategy_perf_date ON strategy_performance (date DESC);

-- System Logs & Monitoring
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level VARCHAR(10) NOT NULL, -- INFO, WARNING, ERROR
    component VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs (level, timestamp DESC);

-- Data retention policies (keep 5 years of data, aggregate older data)
SELECT add_retention_policy('market_ohlc', INTERVAL '5 years', if_not_exists => TRUE);
SELECT add_retention_policy('indicators', INTERVAL '5 years', if_not_exists => TRUE);
SELECT add_retention_policy('options_chain', INTERVAL '2 years', if_not_exists => TRUE);

-- Continuous aggregates for performance (pre-computed daily summaries)
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_market_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    symbol,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume
FROM market_ohlc
WHERE timeframe = '1d'
GROUP BY day, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('daily_market_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
