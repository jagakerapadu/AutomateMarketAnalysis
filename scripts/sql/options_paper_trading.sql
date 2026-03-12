-- =============================================================================
-- NIFTY 50 OPTIONS PAPER TRADING SCHEMA
-- =============================================================================
-- Created: March 12, 2026
-- Purpose: Track paper trading of Nifty 50 Call (CE) and Put (PE) options
-- =============================================================================

-- Virtual Options Portfolio Table
CREATE TABLE IF NOT EXISTS paper_options_portfolio (
    id SERIAL PRIMARY KEY,
    total_capital DECIMAL(15, 2) NOT NULL,
    available_cash DECIMAL(15, 2) NOT NULL,
    invested_amount DECIMAL(15, 2) DEFAULT 0,
    total_pnl DECIMAL(15, 2) DEFAULT 0,
    today_pnl DECIMAL(15, 2) DEFAULT 0,
    total_premium_paid DECIMAL(15, 2) DEFAULT 0,
    total_premium_received DECIMAL(15, 2) DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Virtual Options Positions Table
CREATE TABLE IF NOT EXISTS paper_options_positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL, -- NIFTY, BANKNIFTY
    strike DECIMAL(10, 2) NOT NULL,
    option_type VARCHAR(2) NOT NULL, -- CE or PE
    expiry_date DATE NOT NULL,
    quantity INTEGER NOT NULL, -- Lot size
    entry_premium DECIMAL(10, 2) NOT NULL, -- Premium paid per contract
    current_premium DECIMAL(10, 2), -- Current market premium
    invested_value DECIMAL(15, 2) NOT NULL, -- Total premium paid
    current_value DECIMAL(15, 2), -- Current total value
    pnl DECIMAL(15, 2), -- Profit/Loss
    pnl_percent DECIMAL(8, 2), -- P&L percentage
    position_type VARCHAR(10) DEFAULT 'LONG', -- LONG (buy) or SHORT (sell)
    strategy VARCHAR(50), -- Which strategy created this position
    entry_iv DECIMAL(8, 4), -- Implied Volatility at entry
    current_iv DECIMAL(8, 4), -- Current IV
    delta DECIMAL(6, 4), -- Option delta
    theta DECIMAL(8, 4), -- Time decay per day
    days_to_expiry INTEGER, -- Days remaining
    opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, strike, option_type, expiry_date)
);

CREATE INDEX IF NOT EXISTS idx_paper_options_positions_symbol ON paper_options_positions (symbol, expiry_date);
CREATE INDEX IF NOT EXISTS idx_paper_options_positions_expiry ON paper_options_positions (expiry_date);

-- Virtual Options Orders Table
CREATE TABLE IF NOT EXISTS paper_options_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    strike DECIMAL(10, 2) NOT NULL,
    option_type VARCHAR(2) NOT NULL, -- CE or PE
    expiry_date DATE NOT NULL,
    order_type VARCHAR(10) NOT NULL, -- BUY or SELL
    quantity INTEGER NOT NULL, -- Number of lots
    order_premium DECIMAL(10, 2), -- Expected premium
    executed_premium DECIMAL(10, 2), -- Actual execution premium
    total_cost DECIMAL(15, 2), -- Total cost (premium × quantity × lot_size)
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, EXECUTED, CANCELLED, EXPIRED
    signal_id INTEGER, -- Reference to signals table
    strategy VARCHAR(50), -- Strategy that generated this order
    confidence DECIMAL(5, 2), -- Signal confidence
    placed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMPTZ,
    reason TEXT, -- Entry/exit reason
    exit_reason VARCHAR(50) -- TARGET, STOP_LOSS, TIME_DECAY, MANUAL, EXPIRY
);

CREATE INDEX IF NOT EXISTS idx_paper_options_orders_symbol ON paper_options_orders (symbol, placed_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_options_orders_status ON paper_options_orders (status);
CREATE INDEX IF NOT EXISTS idx_paper_options_orders_expiry ON paper_options_orders (expiry_date);

-- Options Trading Signals Table (extends main signals table for options)
CREATE TABLE IF NOT EXISTS options_signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL, -- NIFTY, BANKNIFTY
    strike DECIMAL(10, 2) NOT NULL,
    option_type VARCHAR(2) NOT NULL, -- CE or PE
    expiry_date DATE NOT NULL,
    signal_type VARCHAR(10) NOT NULL, -- BUY, SELL
    strategy VARCHAR(50) NOT NULL,
    entry_premium DECIMAL(10, 2) NOT NULL,
    stop_loss_premium DECIMAL(10, 2),
    target_premium DECIMAL(10, 2),
    confidence DECIMAL(5, 2),
    quantity INTEGER, -- Number of lots to trade
    
    -- Options-specific data
    current_spot_price DECIMAL(10, 2), -- Nifty spot price
    strike_distance DECIMAL(8, 2), -- Distance from ATM (in points)
    strike_type VARCHAR(10), -- ATM, ITM, OTM
    entry_iv DECIMAL(8, 4), -- Implied Volatility
    pcr_ratio DECIMAL(8, 4), -- Put-Call Ratio
    oi_buildup BIGINT, -- Open Interest at strike
    max_pain DECIMAL(10, 2), -- Max pain level
    
    -- Risk management
    risk_amount DECIMAL(15, 2), -- Max risk per trade
    reward_amount DECIMAL(15, 2), -- Expected reward
    risk_reward_ratio DECIMAL(6, 2),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, EXECUTED, CANCELLED, EXPIRED
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_options_signals_symbol ON options_signals (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_options_signals_status ON options_signals (status, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_options_signals_expiry ON options_signals (expiry_date);

-- Options Analytics Table (End-of-Day Performance Tracking)
CREATE TABLE IF NOT EXISTS options_daily_analytics (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    
    -- Portfolio metrics
    starting_capital DECIMAL(15, 2),
    ending_capital DECIMAL(15, 2),
    day_pnl DECIMAL(15, 2),
    day_pnl_percent DECIMAL(8, 4),
    
    -- Trading activity
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(6, 2),
    
    -- Financial metrics
    total_premium_paid DECIMAL(15, 2) DEFAULT 0,
    total_premium_received DECIMAL(15, 2) DEFAULT 0,
    avg_profit DECIMAL(15, 2),
    avg_loss DECIMAL(15, 2),
    profit_factor DECIMAL(6, 2),
    largest_win DECIMAL(15, 2),
    largest_loss DECIMAL(15, 2),
    
    -- Options-specific metrics
    avg_iv_entry DECIMAL(8, 4),
    total_theta_decay DECIMAL(15, 2), -- Total time decay impact
    ce_trades INTEGER DEFAULT 0,
    pe_trades INTEGER DEFAULT 0,
    
    -- Strategy performance
    best_strategy VARCHAR(50),
    worst_strategy VARCHAR(50),
    strategy_breakdown JSONB, -- Detailed breakdown by strategy
    
    -- Market conditions
    nifty_open DECIMAL(10, 2),
    nifty_close DECIMAL(10, 2),
    nifty_change_percent DECIMAL(8, 4),
    india_vix DECIMAL(8, 4),
    
    -- What went well / What went wrong
    wins_analysis TEXT[], -- Array of winning trade analysis
    losses_analysis TEXT[], -- Array of losing trade analysis
    key_learnings TEXT[],
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_options_analytics_date ON options_daily_analytics (trade_date DESC);

-- Options Trade Journal (Detailed trade-by-trade analysis)
CREATE TABLE IF NOT EXISTS options_trade_journal (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Position details
    symbol VARCHAR(50) NOT NULL,
    strike DECIMAL(10, 2) NOT NULL,
    option_type VARCHAR(2) NOT NULL,
    expiry_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    
    -- Entry
    entry_premium DECIMAL(10, 2) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    entry_spot_price DECIMAL(10, 2),
    entry_iv DECIMAL(8, 4),
    entry_reason TEXT,
    
    -- Exit
    exit_premium DECIMAL(10, 2),
    exit_time TIMESTAMPTZ,
    exit_spot_price DECIMAL(10, 2),
    exit_iv DECIMAL(8, 4),
    exit_reason VARCHAR(50), -- TARGET, STOP_LOSS, TIME_DECAY, EXPIRY
    
    -- Performance
    pnl DECIMAL(15, 2),
    pnl_percent DECIMAL(8, 4),
    hold_duration_minutes INTEGER,
    strategy VARCHAR(50),
    confidence DECIMAL(5, 2),
    
    -- Analysis
    what_went_well TEXT,
    what_went_wrong TEXT,
    lessons_learned TEXT,
    rating INTEGER, -- 1-5 stars for trade quality
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_options_journal_date ON options_trade_journal (trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_options_journal_symbol ON options_trade_journal (symbol, entry_time DESC);

-- Options Market Indicators (Custom indicators for options)
CREATE TABLE IF NOT EXISTS options_market_indicators (
    timestamp TIMESTAMPTZ NOT NULL PRIMARY KEY,
    
    -- Nifty metrics
    nifty_spot DECIMAL(10, 2),
    nifty_fut DECIMAL(10, 2),
    
    -- PCR ratios
    pcr_all DECIMAL(8, 4), -- Overall PCR
    pcr_oi DECIMAL(8, 4), -- OI-based PCR
    pcr_volume DECIMAL(8, 4), -- Volume-based PCR
    
    -- Max Pain
    max_pain_nifty DECIMAL(10, 2),
    max_pain_banknifty DECIMAL(10, 2),
    
    -- IV metrics
    atm_call_iv DECIMAL(8, 4),
    atm_put_iv DECIMAL(8, 4),
    iv_rank DECIMAL(6, 2), -- 0-100 percentile
    
    -- OI Analysis
    total_ce_oi BIGINT,
    total_pe_oi BIGINT,
    oi_change_ce BIGINT,
    oi_change_pe BIGINT,
    
    -- Support/Resistance from options
    call_resistance DECIMAL(10, 2), -- Strike with highest call OI
    put_support DECIMAL(10, 2), -- Strike with highest put OI
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_options_indicators_time ON options_market_indicators (timestamp DESC);

-- Initialize options portfolio with capital
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM paper_options_portfolio) THEN
        INSERT INTO paper_options_portfolio (total_capital, available_cash)
        VALUES (1000000, 1000000); -- ₹10 Lakhs initial capital
        RAISE NOTICE 'Initialized options paper portfolio with ₹10,00,000';
    END IF;
END $$;

-- Create view for active options positions with live P&L
CREATE OR REPLACE VIEW v_active_options_positions AS
SELECT 
    p.*,
    (p.current_value - p.invested_value) as unrealized_pnl,
    ((p.current_value - p.invested_value) / p.invested_value * 100) as unrealized_pnl_percent,
    EXTRACT(EPOCH FROM (p.expiry_date::timestamp - NOW())) / 86400 as days_to_expiry_calc
FROM paper_options_positions p
WHERE p.quantity > 0
ORDER BY p.opened_at DESC;

-- Create view for options performance summary
CREATE OR REPLACE VIEW v_options_performance_summary AS
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    ROUND(AVG(CASE WHEN pnl > 0 THEN pnl ELSE 0 END), 2) as avg_win,
    ROUND(AVG(CASE WHEN pnl < 0 THEN pnl ELSE 0 END), 2) as avg_loss,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl_percent), 2) as avg_pnl_percent,
    ROUND(SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) / NULLIF(ABS(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END)), 0), 2) as profit_factor
FROM options_trade_journal
WHERE exit_time IS NOT NULL;

-- =============================================================================
-- COMMENTS & NOTES
-- =============================================================================
-- 
-- TABLES:
-- 1. paper_options_portfolio - Overall options trading capital
-- 2. paper_options_positions - Active option positions
-- 3. paper_options_orders - All buy/sell orders (entry + exit)
-- 4. options_signals - Generated trading signals for options
-- 5. options_daily_analytics - End-of-day performance tracking
-- 6. options_trade_journal - Detailed trade analysis with learnings
-- 7. options_market_indicators - Options-specific market data (PCR, max pain, IV)
--
-- VIEWS:
-- - v_active_options_positions - Live positions with unrealized P&L
-- - v_options_performance_summary - Overall trading statistics
--
-- =============================================================================
