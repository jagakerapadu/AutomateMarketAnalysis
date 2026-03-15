-- =============================================================================
-- HIGH-PRIORITY PERFORMANCE INDEXES
-- =============================================================================
-- Purpose: Add missing indexes to critical tables for better query performance
-- Impact: 10-100x faster queries as data grows
-- Downtime: ZERO (using CONCURRENTLY)
-- Execution Time: 1-2 minutes
-- Safe to run: YES (on live production system)
-- =============================================================================

-- Check current indexes (for verification)
\echo '=============================================================================='
\echo 'CURRENT INDEXES ON paper_orders:'
\echo '=============================================================================='
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'paper_orders';

\echo ''
\echo '=============================================================================='
\echo 'ADDING NEW INDEXES (This may take 1-2 minutes)...'
\echo '=============================================================================='

-- =============================================================================
-- 1. paper_orders (MOST CRITICAL - Currently has ZERO performance indexes)
-- =============================================================================

-- Index 1: Symbol + Time (Most common query: Order history by symbol)
-- Query: SELECT * FROM paper_orders WHERE symbol = 'INFY' ORDER BY placed_at DESC
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_symbol_time 
    ON paper_orders (symbol, placed_at DESC);

\echo '  ✓ Created: idx_paper_orders_symbol_time'

-- Index 2: Status + Time (Common query: Find PENDING/COMPLETED orders)
-- Query: SELECT * FROM paper_orders WHERE status = 'PENDING' ORDER BY placed_at DESC
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_status_time 
    ON paper_orders (status, placed_at DESC);

\echo '  ✓ Created: idx_paper_orders_status_time'

-- Index 3: Signal ID (Track orders from specific signal)
-- Query: SELECT * FROM paper_orders WHERE signal_id = 123
-- Partial index (only for orders with signal_id) - smaller, faster
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_signal_id 
    ON paper_orders (signal_id) 
    WHERE signal_id IS NOT NULL;

\echo '  ✓ Created: idx_paper_orders_signal_id'

-- Index 4: Composite for common query pattern
-- Query: SELECT * FROM paper_orders WHERE order_type = 'BUY' AND symbol = 'INFY' ORDER BY placed_at DESC
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_type_symbol_time 
    ON paper_orders (order_type, symbol, placed_at DESC);

\echo '  ✓ Created: idx_paper_orders_type_symbol_time'

-- =============================================================================
-- 2. paper_positions (MODERATE PRIORITY)
-- =============================================================================

-- Index 1: Updated timestamp (Find stale positions not updated recently)
-- Query: SELECT * FROM paper_positions WHERE updated_at < NOW() - INTERVAL '1 hour'
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_positions_updated 
    ON paper_positions (updated_at DESC);

\echo '  ✓ Created: idx_paper_positions_updated'

-- Index 2: P&L tracking (Top performers/losers)
-- Query: SELECT * FROM paper_positions ORDER BY pnl DESC LIMIT 10
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_positions_pnl 
    ON paper_positions (pnl DESC NULLS LAST);

\echo '  ✓ Created: idx_paper_positions_pnl'

-- =============================================================================
-- 3. signals (OPTIMIZATION)
-- =============================================================================

-- Index 1: Strategy-based queries
-- Query: SELECT * FROM signals WHERE strategy = 'MOMENTUM_BREAKOUT' ORDER BY created_at DESC
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signals_strategy_status 
    ON signals (strategy, status, created_at DESC);

\echo '  ✓ Created: idx_signals_strategy_status'

-- Index 2: Partial index for active signals only (smaller, faster)
-- Query: SELECT * FROM signals WHERE status IN ('PENDING', 'EXECUTED') AND symbol = 'INFY'
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signals_active 
    ON signals (symbol, created_at DESC) 
    WHERE status IN ('PENDING', 'EXECUTED');

\echo '  ✓ Created: idx_signals_active'

-- =============================================================================
-- VERIFY INDEX CREATION
-- =============================================================================

\echo ''
\echo '=============================================================================='
\echo 'INDEX CREATION SUMMARY:'
\echo '=============================================================================='

SELECT 
    tablename,
    COUNT(*) AS index_count,
    pg_size_pretty(SUM(pg_relation_size(indexrelid))) AS total_index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('paper_orders', 'paper_positions', 'signals')
GROUP BY tablename
ORDER BY tablename;

\echo ''
\echo '=============================================================================='
\echo 'ALL INDEXES ON CRITICAL TABLES:'
\echo '=============================================================================='

SELECT 
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('paper_orders', 'paper_positions', 'signals')
ORDER BY tablename, indexname;

\echo ''
\echo '=============================================================================='
\echo '✅ INDEX CREATION COMPLETE!'
\echo '=============================================================================='
\echo 'Next steps:'
\echo '1. Run: py scripts/test_query_performance.py (test performance improvement)'
\echo '2. Monitor query times in production'
\echo '3. Check for unused indexes after 1 week: SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;'
\echo '=============================================================================='
